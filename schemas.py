from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, datetime

class HealthTestTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    valid_results: str  # JSON string

class HealthTestTypeCreate(HealthTestTypeBase):
    pass

class HealthTestType(HealthTestTypeBase):
    id: int
    
    class Config:
        from_attributes = True

class HealthTestBase(BaseModel):
    test_type_id: int
    test_date: date
    place: Optional[str] = None
    result: str
    notes: Optional[str] = None

class HealthTestCreate(HealthTestBase):
    pass

class HealthTest(HealthTestBase):
    id: int
    dog_id: int
    test_type: Optional[HealthTestType] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DogBase(BaseModel):
    name: str
    registration_number: Optional[str] = None
    sex: str = Field(..., pattern="^(Male|Female)$")
    date_of_birth: Optional[date] = None
    color: Optional[str] = None
    breed: str
    kennel_name: Optional[str] = None
    tatoo_no: Optional[str] = None
    microchip: Optional[str] = None
    breeder: Optional[str] = None
    sire_id: Optional[int] = None
    dam_id: Optional[int] = None

class DogCreate(DogBase):
    pass

class DogUpdate(BaseModel):
    name: Optional[str] = None
    registration_number: Optional[str] = None
    sex: Optional[str] = None
    date_of_birth: Optional[date] = None
    color: Optional[str] = None
    breed: Optional[str] = None
    kennel_name: Optional[str] = None
    tatoo_no: Optional[str] = None
    microchip: Optional[str] = None
    breeder: Optional[str] = None
    sire_id: Optional[int] = None
    dam_id: Optional[int] = None

class DogSimple(BaseModel):
    id: int
    name: str
    registration_number: Optional[str] = None
    sex: str
    date_of_birth: Optional[date] = None
    breed: str
    
    class Config:
        from_attributes = True

class Dog(DogBase):
    id: int
    sire: Optional[DogSimple] = None
    dam: Optional[DogSimple] = None
    health_tests: List[HealthTest] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DogPedigree(DogSimple):
    sire: Optional['DogPedigree'] = None
    dam: Optional['DogPedigree'] = None
    
    class Config:
        from_attributes = True

# Enable forward references
DogPedigree.model_rebuild()
