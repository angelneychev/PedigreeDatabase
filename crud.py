from sqlalchemy.orm import Session
from typing import Optional, List
import json
from models import Dog, HealthTest, HealthTestType
import schemas

def get_dog(db: Session, dog_id: int) -> Optional[Dog]:
    return db.query(Dog).filter(Dog.id == dog_id).first()

def get_dog_by_registration(db: Session, registration_number: str) -> Optional[Dog]:
    return db.query(Dog).filter(Dog.registration_number == registration_number).first()

def get_dogs(db: Session, skip: int = 0, limit: int = 100) -> List[Dog]:
    return db.query(Dog).offset(skip).limit(limit).all()

def create_dog(db: Session, dog: schemas.DogCreate) -> Dog:
    db_dog = Dog(**dog.dict())
    db.add(db_dog)
    db.commit()
    db.refresh(db_dog)
    return db_dog

def update_dog(db: Session, dog_id: int, dog_update: schemas.DogUpdate) -> Optional[Dog]:
    db_dog = db.query(Dog).filter(Dog.id == dog_id).first()
    if db_dog:
        update_data = dog_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_dog, field, value)
        db.commit()
        db.refresh(db_dog)
    return db_dog

def delete_dog(db: Session, dog_id: int) -> bool:
    db_dog = db.query(Dog).filter(Dog.id == dog_id).first()
    if db_dog:
        db.delete(db_dog)
        db.commit()
        return True
    return False

def get_parents_recursively(db: Session, dog_id: int, generation: int = 0, max_generation: int = 9) -> Optional[dict]:
    """Recursively get parents of a dog up to max_generation levels
    
    Args:
        generation: Current generation level (0 = main dog, 1 = parents, 2 = grandparents, etc.)
        max_generation: Maximum generation to fetch (9 = up to 9th generation)
    """
    # Stop recursion if we've exceeded the maximum generation or no dog_id
    if generation > max_generation or not dog_id:
        return None
    
    # Load the current dog individually (no JOINs)
    dog = db.query(Dog).get(dog_id)
    if not dog:
        return None
      # Create result dictionary with basic dog info
    result = {
        "id": dog.id,
        "name": dog.name,
        "registration_number": dog.registration_number,
        "date_of_birth": dog.date_of_birth,
        "sex": dog.sex,
        "breed": dog.breed,
        "kennel_name": dog.kennel_name,
        "sire": None,
        "dam": None
    }
    
    # Recursively get sire (father) if exists
    if dog.sire_id:
        result["sire"] = get_parents_recursively(db, dog.sire_id, generation + 1, max_generation)
    
    # Recursively get dam (mother) if exists  
    if dog.dam_id:
        result["dam"] = get_parents_recursively(db, dog.dam_id, generation + 1, max_generation)
    
    return result

def get_ancestor_at_position(pedigree_data: dict, generation: int, position: int) -> Optional[dict]:
    """Get ancestor at specific generation and position using binary path navigation"""
    if not pedigree_data:
        return None
    
    current = pedigree_data
    
    # Navigate through the generations using binary representation
    for level in range(generation):
        if not current:
            return None
            
        # Calculate which path to take (0=sire, 1=dam)
        # Use MSB first approach: divide by 2^(generation-1-level)
        divisor = 2 ** (generation - 1 - level)
        bit = (position // divisor) % 2
        
        if bit == 0:
            current = current.get("sire")
        else:
            current = current.get("dam")
    
    return current

def get_dog_pedigree(db: Session, dog_id: int, generations: int = 3) -> Optional[Dog]:
    """Get dog with pedigree information for specified number of generations"""
    # First get the main dog
    dog = db.query(Dog).get(dog_id)
    if not dog:
        return None
      # Get the recursive pedigree data and attach it to the dog object
    # Start with generation 0 for the main dog, so parents are generation 1
    pedigree_data = get_parents_recursively(db, dog_id, 0, generations)
    
    # Create ancestor matrix for easier template access
    if pedigree_data:
        dog.pedigree_data = pedigree_data
        
        # Create a pre-computed ancestor matrix for all positions
        dog.ancestor_matrix = {}
        for gen in range(1, generations + 1):
            dog.ancestor_matrix[gen] = {}
            total_positions = 2 ** gen
            for pos in range(total_positions):
                ancestor = get_ancestor_at_position(pedigree_data, gen, pos)
                dog.ancestor_matrix[gen][pos] = ancestor
    
    return dog

def get_health_test_types(db: Session) -> List[HealthTestType]:
    return db.query(HealthTestType).all()

def create_health_test_type(db: Session, test_type: schemas.HealthTestTypeCreate) -> HealthTestType:
    db_test_type = HealthTestType(**test_type.dict())
    db.add(db_test_type)
    db.commit()
    db.refresh(db_test_type)
    return db_test_type

def get_health_test_type(db: Session, test_type_id: int) -> Optional[HealthTestType]:
    return db.query(HealthTestType).filter(HealthTestType.id == test_type_id).first()

def create_health_test(db: Session, dog_id: int, health_test: schemas.HealthTestCreate) -> HealthTest:
    # Validate result against test type
    test_type = get_health_test_type(db, health_test.test_type_id)
    if test_type:
        valid_results = json.loads(test_type.valid_results)
        if health_test.result not in valid_results:
            raise ValueError(f"Invalid result '{health_test.result}' for test type '{test_type.name}'. Valid options: {', '.join(valid_results)}")
    
    db_health_test = HealthTest(dog_id=dog_id, **health_test.dict())
    db.add(db_health_test)
    db.commit()
    db.refresh(db_health_test)
    return db_health_test

def get_dog_health_tests(db: Session, dog_id: int) -> List[HealthTest]:
    return db.query(HealthTest).filter(HealthTest.dog_id == dog_id).all()

def search_dogs(db: Session, query: str, skip: int = 0, limit: int = 100) -> List[Dog]:
    """Search dogs by name, registration_number, tatoo_no, microchip, kennel_name, or breed"""
    return db.query(Dog).filter(
        Dog.name.contains(query) | 
        Dog.registration_number.contains(query) |
        Dog.tatoo_no.contains(query) |
        Dog.microchip.contains(query) |
        Dog.kennel_name.contains(query) |
        Dog.breed.contains(query)
    ).offset(skip).limit(limit).all()

def count_search_dogs(db: Session, query: str) -> int:
    """Count total search results for pagination"""
    return db.query(Dog).filter(
        Dog.name.contains(query) | 
        Dog.registration_number.contains(query) |
        Dog.tatoo_no.contains(query) |
        Dog.microchip.contains(query) |
        Dog.kennel_name.contains(query) |
        Dog.breed.contains(query)
    ).count()
