from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import crud
import schemas
from database import get_db
from models import Dog

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# HTML Routes
@router.get("/", response_class=HTMLResponse)
async def read_dogs_homepage(request: Request, db: Session = Depends(get_db)):
    dogs = crud.get_dogs(db, limit=6)  # Get first 6 dogs for homepage
    
    # Get basic statistics
    from utils import get_breeding_statistics
    stats = get_breeding_statistics(db)
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "dogs": dogs,
        "stats": stats
    })

@router.get("/search", response_class=HTMLResponse)
async def search_dogs_page(request: Request, q: str = "", page: int = 1, db: Session = Depends(get_db)):
    from fastapi.responses import RedirectResponse
    dogs = []
    total_results = 0
    total_pages = 0
    limit = 20

    if q and len(q.strip()) >= 2:
        skip = (page - 1) * limit
        dogs = crud.search_dogs(db, query=q.strip(), skip=skip, limit=limit)
        total_results = crud.count_search_dogs(db, query=q.strip())
        total_pages = (total_results + limit - 1) // limit  # Ceiling division

        # If only one result, redirect to dog detail page
        if total_results == 1 and dogs:
            return RedirectResponse(url=f"/dogs/{dogs[0].id}")

    return templates.TemplateResponse("search_results.html", {
        "request": request, 
        "dogs": dogs, 
        "query": q,
        "current_page": page,
        "total_pages": total_pages,
        "total_results": total_results,
        "has_prev": page > 1,
        "has_next": page < total_pages,
        "prev_page": page - 1 if page > 1 else None,
        "next_page": page + 1 if page < total_pages else None
    })

@router.get("/dogs", response_class=HTMLResponse)
async def list_dogs_page(request: Request, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    dogs = crud.get_dogs(db, skip=skip, limit=limit)
    return templates.TemplateResponse("dogs_list.html", {"request": request, "dogs": dogs})

from fastapi import Query

@router.get("/dogs/{dog_id}", response_class=HTMLResponse)
async def read_dog_page(request: Request, dog_id: int, db: Session = Depends(get_db)):
    # Default generation count
    default_generations = 4
    show_gen_int = default_generations

    dog = crud.get_dog(db, dog_id=dog_id)
    if dog is None:
        raise HTTPException(status_code=404, detail="Dog not found")

    # Get pedigree information for the requested number of generations
    pedigree_dog = crud.get_dog_pedigree(db, dog_id=dog_id, generations=show_gen_int)
    health_tests = crud.get_dog_health_tests(db, dog_id=dog_id)# Get additional information
    from utils import get_health_summary, search_related_dogs, calculate_age_from_birth_date, get_pedigree_completeness, detect_pedigree_inbreeding
    
    health_summary = get_health_summary(dog)
    related_dogs = search_related_dogs(dog, db, "siblings")[:5]  # Limit to 5 for display
    age_str = calculate_age_from_birth_date(dog.date_of_birth)
    pedigree_completeness = get_pedigree_completeness(dog, db, show_gen_int)    # Detect inbreeding in 4 generations for highlighting
    inbreeding_data = detect_pedigree_inbreeding(pedigree_dog, generations=4)

    return templates.TemplateResponse("dog_detail.html", {
        "request": request,
        "dog": pedigree_dog,
        "pedigree": getattr(pedigree_dog, 'pedigree_data', None),
        "ancestor_matrix": getattr(pedigree_dog, 'ancestor_matrix', {}),
        "health_tests": health_tests,
        "health_summary": health_summary,
        "related_dogs": related_dogs,
        "age_str": age_str,
        "pedigree_completeness": pedigree_completeness,
        "inbreeding_data": inbreeding_data,
        "show_gen": show_gen_int
    })

@router.get("/dogs/add", response_class=HTMLResponse)
async def add_dog_form(request: Request, db: Session = Depends(get_db)):
    dogs = crud.get_dogs(db, limit=1000)  # For parent selection
    return templates.TemplateResponse("dog_form.html", {"request": request, "dogs": dogs})

@router.post("/dogs/add", response_class=HTMLResponse)
async def create_dog_form(
    request: Request,
    name: str = Form(...),
    registration_number: Optional[str] = Form(None),
    sex: str = Form(...),
    date_of_birth: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    breed: str = Form(...),
    kennel_name: Optional[str] = Form(None),
    tatoo_no: Optional[str] = Form(None),
    microchip: Optional[str] = Form(None),
    breeder: Optional[str] = Form(None),
    sire_id: Optional[int] = Form(None),
    dam_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        dog_data = {
            "name": name,
            "registration_number": registration_number if registration_number else None,
            "sex": sex,
            "date_of_birth": date_of_birth if date_of_birth else None,
            "color": color if color else None,
            "breed": breed,
            "kennel_name": kennel_name if kennel_name else None,
            "tatoo_no": tatoo_no if tatoo_no else None,
            "microchip": microchip if microchip else None,
            "breeder": breeder if breeder else None,
            "sire_id": sire_id if sire_id and sire_id != 0 else None,
            "dam_id": dam_id if dam_id and dam_id != 0 else None,
        }
        
        dog_create = schemas.DogCreate(**dog_data)
        dog = crud.create_dog(db=db, dog=dog_create)
        return templates.TemplateResponse("dog_success.html", {"request": request, "dog": dog})
    except Exception as e:
        dogs = crud.get_dogs(db, limit=1000)
        return templates.TemplateResponse("dog_form.html", {
            "request": request, 
            "dogs": dogs,
            "error": str(e)
        })

@router.get("/dogs/{dog_id}/pedigree", response_class=HTMLResponse)
async def read_dog_pedigree_page(request: Request, dog_id: int, db: Session = Depends(get_db)):
    dog = crud.get_dog_pedigree(db, dog_id=dog_id)
    if dog is None:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    # Simplified - no siblings for now due to SQLAlchemy issues
    siblings = []
    
    # Get pedigree completeness and inbreeding data
    from utils import get_pedigree_completeness, detect_pedigree_inbreeding, calculate_inbreeding_coefficient
    pedigree_completeness = get_pedigree_completeness(dog, db, 4)  # 4 generations
    inbreeding_data = detect_pedigree_inbreeding(dog, generations=4)
    
    # Add inbreeding levels to each dog in the pedigree
    def add_inbreeding_info(dog_obj):
        if dog_obj:
            try:
                coi_data = calculate_inbreeding_coefficient(dog_obj, db, generations=4)
                coi_percentage = coi_data.get('coi_percentage', 0.0)
                
                # Determine inbreeding level based on COI percentage
                if coi_percentage == 0.0:
                    inbred_level = None  # No highlighting
                elif coi_percentage < 3.125:
                    inbred_level = 'low'  # Green
                elif coi_percentage < 6.25:
                    inbred_level = 'moderate'  # Yellow
                elif coi_percentage < 12.5:
                    inbred_level = 'high'  # Orange
                else:
                    inbred_level = 'very-high'  # Red
                
                dog_obj.coi_percentage = coi_percentage
                dog_obj.inbred_level = inbred_level
            except Exception as e:
                # If COI calculation fails, don't highlight
                dog_obj.coi_percentage = 0.0
                dog_obj.inbred_level = None
        return dog_obj
    
    # Process all dogs in the pedigree tree
    add_inbreeding_info(dog)
    if hasattr(dog, 'sire') and dog.sire:
        add_inbreeding_info(dog.sire)
        if hasattr(dog.sire, 'sire') and dog.sire.sire:
            add_inbreeding_info(dog.sire.sire)
            if hasattr(dog.sire.sire, 'sire') and dog.sire.sire.sire:
                add_inbreeding_info(dog.sire.sire.sire)
            if hasattr(dog.sire.sire, 'dam') and dog.sire.sire.dam:
                add_inbreeding_info(dog.sire.sire.dam)
        if hasattr(dog.sire, 'dam') and dog.sire.dam:
            add_inbreeding_info(dog.sire.dam)
            if hasattr(dog.sire.dam, 'sire') and dog.sire.dam.sire:
                add_inbreeding_info(dog.sire.dam.sire)
            if hasattr(dog.sire.dam, 'dam') and dog.sire.dam.dam:
                add_inbreeding_info(dog.sire.dam.dam)
    if hasattr(dog, 'dam') and dog.dam:
        add_inbreeding_info(dog.dam)
        if hasattr(dog.dam, 'sire') and dog.dam.sire:
            add_inbreeding_info(dog.dam.sire)
            if hasattr(dog.dam.sire, 'sire') and dog.dam.sire.sire:
                add_inbreeding_info(dog.dam.sire.sire)
            if hasattr(dog.dam.sire, 'dam') and dog.dam.sire.dam:
                add_inbreeding_info(dog.dam.sire.dam)
        if hasattr(dog.dam, 'dam') and dog.dam.dam:
            add_inbreeding_info(dog.dam.dam)
            if hasattr(dog.dam.dam, 'sire') and dog.dam.dam.sire:
                add_inbreeding_info(dog.dam.dam.sire)
            if hasattr(dog.dam.dam, 'dam') and dog.dam.dam.dam:
                add_inbreeding_info(dog.dam.dam.dam)
    
    return templates.TemplateResponse("pedigree_horizontal.html", {
        "request": request, 
        "dog": dog,
        "siblings": siblings,
        "pedigree_completeness": pedigree_completeness,
        "inbreeding_data": inbreeding_data
    })

# API endpoint for getting pedigree data with specific generation count
@router.get("/api/dogs/{dog_id}/pedigree/{generations}")
async def get_dog_pedigree_api(dog_id: int, generations: int, db: Session = Depends(get_db)):
    # Validate generations parameter
    if generations < 1 or generations > 9:
        raise HTTPException(status_code=400, detail="Generations must be between 1 and 9")
      # Get dog and pedigree information for the requested number of generations
    pedigree_dog = crud.get_dog_pedigree(db, dog_id=dog_id, generations=generations)
    if pedigree_dog is None:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    # Get additional information
    from utils import get_pedigree_completeness, detect_pedigree_inbreeding, calculate_inbreeding_coefficient
    
    pedigree_completeness = get_pedigree_completeness(pedigree_dog, db, generations)
    # Detect inbreeding in specified generations for highlighting
    inbreeding_data = detect_pedigree_inbreeding(pedigree_dog, generations=generations)
    
    def add_coi_data_to_matrix(matrix, db):
        """Add individual COI data to each ancestor in the matrix"""
        for generation, ancestors in matrix.items():
            for position, ancestor in ancestors.items():
                if ancestor and isinstance(ancestor, dict) and 'id' in ancestor:
                    ancestor_id = ancestor['id']
                    
                    # Calculate COI for this individual ancestor
                    try:
                        ancestor_dog = db.query(Dog).filter(Dog.id == ancestor_id).first()
                        if ancestor_dog:
                            coi_data = calculate_inbreeding_coefficient(ancestor_dog, db, generations=5)
                            matrix[generation][position]['coi_percentage'] = coi_data['coi_percentage']
                            matrix[generation][position]['coi_interpretation'] = coi_data['interpretation']
                        else:
                            matrix[generation][position]['coi_percentage'] = 0.0
                    except Exception as e:
                        # If COI calculation fails, set to 0
                        matrix[generation][position]['coi_percentage'] = 0.0
        return matrix
    
    def add_inbreeding_levels_to_matrix(matrix, inbreeding_data):
        """Add inbreeding levels to each ancestor in the matrix based on common ancestors"""
        # Convert inbreeding_data keys to integers for comparison
        inbred_ancestor_ids = {int(k): v for k, v in inbreeding_data.items()}
        
        for generation, ancestors in matrix.items():
            # ancestors is a dict with position as key, ancestor dict as value
            for position, ancestor in ancestors.items():
                if ancestor and isinstance(ancestor, dict) and 'id' in ancestor:
                    ancestor_id = ancestor['id']
                    
                    # Check if this ancestor is a common ancestor in main dog's pedigree
                    if ancestor_id in inbred_ancestor_ids:
                        inbred_info = inbred_ancestor_ids[ancestor_id]
                        color_index = inbred_info['color_index']
                        
                        # Map color index to inbreeding level (limited to 6 for CSS)
                        if color_index <= 6:
                            inbred_level = str(color_index)
                        else:
                            inbred_level = '6'  # Max level for CSS
                        
                        # Add inbreeding highlighting to ancestor
                        matrix[generation][position]['inbred_level'] = inbred_level
                        matrix[generation][position]['is_common_ancestor'] = True
                        matrix[generation][position]['common_ancestor_count'] = inbred_info['count']
                        matrix[generation][position]['common_ancestor_color'] = inbred_info['color']
                    else:
                        # Not a common ancestor - no highlighting
                        matrix[generation][position]['inbred_level'] = None
                        matrix[generation][position]['is_common_ancestor'] = False
        
        return matrix
    
    # Add inbreeding highlighting based on common ancestors detected in main dog's pedigree
    ancestor_matrix = getattr(pedigree_dog, 'ancestor_matrix', {})
    ancestor_matrix_with_inbreeding = add_inbreeding_levels_to_matrix(ancestor_matrix, inbreeding_data)
    ancestor_matrix_with_coi = add_coi_data_to_matrix(ancestor_matrix_with_inbreeding, db)

    # Convert dog object to dict for JSON serialization
    dog_dict = {
        "id": pedigree_dog.id,
        "name": pedigree_dog.name,
        "registration_number": pedigree_dog.registration_number,
        "sex": pedigree_dog.sex,
        "date_of_birth": pedigree_dog.date_of_birth.isoformat() if pedigree_dog.date_of_birth is not None else None,
        "color": pedigree_dog.color,
        "breed": pedigree_dog.breed,
        "kennel_name": pedigree_dog.kennel_name,
        "breeder": pedigree_dog.breeder
    }

    return {
        "dog": dog_dict,
        "pedigree": getattr(pedigree_dog, 'pedigree_data', None),
        "ancestor_matrix": ancestor_matrix_with_coi,
        "pedigree_completeness": pedigree_completeness,
        "inbreeding_data": inbreeding_data,
        "show_gen": generations
    }

# API Routes
@router.get("/api/dogs/", response_model=List[schemas.Dog])
def read_dogs_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    dogs = crud.get_dogs(db, skip=skip, limit=limit)
    return dogs

@router.post("/api/dogs/", response_model=schemas.Dog)
def create_dog_api(dog: schemas.DogCreate, db: Session = Depends(get_db)):
    return crud.create_dog(db=db, dog=dog)

@router.get("/api/dogs/{dog_id}", response_model=schemas.Dog)
def read_dog_api(dog_id: int, db: Session = Depends(get_db)):
    db_dog = crud.get_dog(db, dog_id=dog_id)
    if db_dog is None:
        raise HTTPException(status_code=404, detail="Dog not found")
    return db_dog

@router.put("/api/dogs/{dog_id}", response_model=schemas.Dog)
def update_dog_api(dog_id: int, dog: schemas.DogUpdate, db: Session = Depends(get_db)):
    db_dog = crud.update_dog(db, dog_id=dog_id, dog_update=dog)
    if db_dog is None:
        raise HTTPException(status_code=404, detail="Dog not found")
    return db_dog

@router.delete("/api/dogs/{dog_id}")
def delete_dog_api(dog_id: int, db: Session = Depends(get_db)):
    success = crud.delete_dog(db, dog_id=dog_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dog not found")
    return {"message": "Dog deleted successfully"}
