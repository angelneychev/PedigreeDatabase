from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import crud
import schemas
from database import get_db

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
    
    # Get siblings (dogs with same parents)
    siblings = []
    if dog.sire_id or dog.dam_id:
        from sqlalchemy import and_, or_
        from models import Dog
        
        sibling_query = db.query(Dog).filter(
            Dog.id != dog.id,  # Exclude the dog itself
            or_(
                and_(Dog.sire_id == dog.sire_id, Dog.sire_id.isnot(None)),
                and_(Dog.dam_id == dog.dam_id, Dog.dam_id.isnot(None))
            )
        ).order_by(Dog.name)
        
        siblings = sibling_query.all()
        
        # Get health tests for siblings
        for sibling in siblings:
            sibling.health_tests = crud.get_dog_health_tests(db, dog_id=sibling.id)
    
    # Get pedigree completeness
    from utils import get_pedigree_completeness
    pedigree_completeness = get_pedigree_completeness(dog, db, 4)  # 4 generations
    
    return templates.TemplateResponse("pedigree_horizontal.html", {
        "request": request, 
        "dog": dog,
        "siblings": siblings,
        "pedigree_completeness": pedigree_completeness
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
    from utils import get_pedigree_completeness, detect_pedigree_inbreeding
    
    pedigree_completeness = get_pedigree_completeness(pedigree_dog, db, generations)
    # Detect inbreeding in specified generations for highlighting
    inbreeding_data = detect_pedigree_inbreeding(pedigree_dog, generations=generations)

    # Convert dog object to dict for JSON serialization
    dog_dict = {
        "id": pedigree_dog.id,
        "name": pedigree_dog.name,
        "registration_number": pedigree_dog.registration_number,
        "sex": pedigree_dog.sex,
        "date_of_birth": pedigree_dog.date_of_birth.isoformat() if pedigree_dog.date_of_birth else None,
        "color": pedigree_dog.color,
        "breed": pedigree_dog.breed,
        "kennel_name": pedigree_dog.kennel_name,
        "breeder": pedigree_dog.breeder
    }

    return {
        "dog": dog_dict,
        "pedigree": getattr(pedigree_dog, 'pedigree_data', None),
        "ancestor_matrix": getattr(pedigree_dog, 'ancestor_matrix', {}),
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
