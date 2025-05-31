from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import crud
import schemas
from database import get_db
import json

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Health Test Types Routes
@router.get("/api/health-test-types/", response_model=List[schemas.HealthTestType])
def read_health_test_types(db: Session = Depends(get_db)):
    return crud.get_health_test_types(db)

@router.post("/api/health-test-types/", response_model=schemas.HealthTestType)
def create_health_test_type(test_type: schemas.HealthTestTypeCreate, db: Session = Depends(get_db)):
    return crud.create_health_test_type(db=db, test_type=test_type)

# Health Tests Routes
@router.get("/dogs/{dog_id}/health-tests", response_class=HTMLResponse)
async def dog_health_tests_page(request: Request, dog_id: int, db: Session = Depends(get_db)):
    dog = crud.get_dog(db, dog_id=dog_id)
    if dog is None:
        raise HTTPException(status_code=404, detail="Dog not found")
    
    health_tests = crud.get_dog_health_tests(db, dog_id=dog_id)
    test_types = crud.get_health_test_types(db)
    
    return templates.TemplateResponse("health_tests.html", {
        "request": request,
        "dog": dog,
        "health_tests": health_tests,
        "test_types": test_types
    })

@router.post("/dogs/{dog_id}/health-tests", response_class=HTMLResponse)
async def add_health_test(
    request: Request,
    dog_id: int,
    test_type_id: int = Form(...),
    test_date: str = Form(...),
    place: Optional[str] = Form(None),
    result: str = Form(...),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        health_test_data = {
            "test_type_id": test_type_id,
            "test_date": test_date,
            "place": place if place else None,
            "result": result,
            "notes": notes if notes else None,
        }
        
        health_test_create = schemas.HealthTestCreate(**health_test_data)
        health_test = crud.create_health_test(db=db, dog_id=dog_id, health_test=health_test_create)
        
        # Redirect back to health tests page
        dog = crud.get_dog(db, dog_id=dog_id)
        health_tests = crud.get_dog_health_tests(db, dog_id=dog_id)
        test_types = crud.get_health_test_types(db)
        
        return templates.TemplateResponse("health_tests.html", {
            "request": request,
            "dog": dog,
            "health_tests": health_tests,
            "test_types": test_types,
            "success": "Health test added successfully!"
        })
    except ValueError as e:
        dog = crud.get_dog(db, dog_id=dog_id)
        health_tests = crud.get_dog_health_tests(db, dog_id=dog_id)
        test_types = crud.get_health_test_types(db)
        
        return templates.TemplateResponse("health_tests.html", {
            "request": request,
            "dog": dog,
            "health_tests": health_tests,
            "test_types": test_types,
            "error": str(e)
        })

@router.get("/api/dogs/{dog_id}/health-tests", response_model=List[schemas.HealthTest])
def get_dog_health_tests_api(dog_id: int, db: Session = Depends(get_db)):
    return crud.get_dog_health_tests(db, dog_id=dog_id)

@router.post("/api/dogs/{dog_id}/health-tests", response_model=schemas.HealthTest)
def create_health_test_api(dog_id: int, health_test: schemas.HealthTestCreate, db: Session = Depends(get_db)):
    return crud.create_health_test(db=db, dog_id=dog_id, health_test=health_test)

@router.post("/api/translate-health-tests")
def translate_health_test_names(db: Session = Depends(get_db)):
    """Translate Estonian health test names to English"""
    from models import HealthTestType
    
    # Translation mapping
    translations = {
        "Düsplaasia": "Hip Dysplasia",
        "Küünarliigeste uuring": "Elbow Dysplasia", 
        "Seljauuring": "Spine Examination",
        "Kuulmistest (BAEP)": "BAER Test",
        "BAER (kuulmistest)": "BAER Test",
        "Baer-test": "BAER Test"
    }
    
    updated_count = 0
    results = []
    
    # Get all test types
    test_types = db.query(HealthTestType).all()
    
    for test_type in test_types:
        old_name = test_type.name
        
        if old_name in translations:
            new_name = translations[old_name]
            
            # Check if English name already exists
            existing = db.query(HealthTestType).filter_by(name=new_name).first()
            
            if existing and existing.id != test_type.id:
                results.append(f"Skipped {old_name} → {new_name} (already exists)")
                continue
            
            # Update the name
            test_type.name = new_name
            test_type.description = f"Health test: {new_name}"
            
            results.append(f"Updated: {old_name} → {new_name}")
            updated_count += 1
        else:
            results.append(f"Kept: {old_name}")
    
    # Commit changes
    db.commit()
    
    return {
        "message": f"Translation completed! Updated {updated_count} test types.",
        "updated_count": updated_count,
        "details": results
    }
