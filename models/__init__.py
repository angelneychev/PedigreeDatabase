from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from database import Base
from datetime import datetime

class HealthTestType(Base):
    __tablename__ = "health_test_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    valid_results = Column(Text, nullable=False)  # JSON string with valid results
    
    health_tests = relationship("HealthTest", back_populates="test_type")

class Dog(Base):
    __tablename__ = "dogs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    registration_number = Column(String(200), unique=True, nullable=True)
    sex = Column(String(10), nullable=False)  # Male/Female
    date_of_birth = Column(Date, nullable=True)
    color = Column(String(50), nullable=True)
    breed = Column(String(100), nullable=False)
    kennel_name = Column(String(100), nullable=True)
    tatoo_no = Column(String(50), nullable=True)
    microchip = Column(String(50), nullable=True)
    breeder = Column(String(100), nullable=True)
    url_org = Column(String(255), nullable=True)  # URL to original registry record
    
    # Self-referencing relationships for pedigree
    sire_id = Column(Integer, ForeignKey("dogs.id"), nullable=True)
    dam_id = Column(Integer, ForeignKey("dogs.id"), nullable=True)
    
    sire = relationship("Dog", remote_side=[id], foreign_keys=[sire_id], backref="sired_offspring")
    dam = relationship("Dog", remote_side=[id], foreign_keys=[dam_id], backref="dam_offspring")
    
    # Health tests relationship
    health_tests = relationship("HealthTest", back_populates="dog")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class HealthTest(Base):
    __tablename__ = "health_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    dog_id = Column(Integer, ForeignKey("dogs.id"), nullable=False)
    test_type_id = Column(Integer, ForeignKey("health_test_types.id"), nullable=False)
    test_date = Column(Date, nullable=False)
    place = Column(String(200), nullable=True)
    result = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    
    dog = relationship("Dog", back_populates="health_tests")
    test_type = relationship("HealthTestType", back_populates="health_tests")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
