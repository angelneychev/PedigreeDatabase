#!/usr/bin/env python3
"""
Bulgarian Dalmatian Registry Data Import - Phase 2 (Fixed)
Импортира липсващи родители от български регистър за далматинци - етап 2

Този скрипт търси липсващи родители в данните и ги импортира като нови записи.
"""

import csv
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import re

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from database import get_db
from models import Dog
from sqlalchemy.orm import Session


def setup_logging():
    """Setup logging configuration"""
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'bulgaria_import_phase2_parents_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Log file: {log_file}")
    return logger


def load_csv_data(file_path: Path) -> List[Dict]:
    """Load data from CSV file"""
    logging.info(f"Loading CSV data from: {file_path}")
    
    records = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # Use semicolon as delimiter
        csv_reader = csv.DictReader(f, delimiter=';')
        
        for row in csv_reader:
            records.append(row)
    
    logging.info(f"Loaded {len(records)} records from CSV")
    return records


def clean_field_value(value: Optional[str]) -> Optional[str]:
    """Clean field value, return None for empty values"""
    if not value or value.strip() in ['', 'None', 'NULL']:
        return None
    return value.strip()


def normalize_registration_number(reg_code: Optional[str]) -> Optional[str]:
    """Normalize registration number for storage"""
    if not reg_code or reg_code.strip() in ['', 'None']:
        return None
    
    # Keep original value for display, but clean it
    reg_code = reg_code.strip()
    
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', reg_code).strip()
    
    return cleaned


def normalize_for_comparison(reg_code: Optional[str]) -> Optional[str]:
    """Normalize registration number for duplicate detection"""
    if not reg_code:
        return None
    
    # Remove all spaces and convert to uppercase
    normalized = re.sub(r'\s+', '', reg_code.strip().upper())
    
    # Handle common patterns
    # "N17385/06" should match "NO 17385/06" -> both become "NO17385/06"
    if re.match(r'^N\d+/', normalized):
        normalized = 'NO' + normalized[1:]
    
    return normalized


def normalize_dog_name_for_comparison(name: Optional[str]) -> Optional[str]:
    """Normalize dog name for duplicate detection"""
    if not name:
        return None
    
    # Convert to uppercase and normalize spaces
    normalized = name.strip().upper()
    
    # Normalize apostrophes and dashes
    normalized = normalized.replace("'", "'")  # Normalize apostrophes
    normalized = re.sub(r'\s*-\s*', '-', normalized)  # Normalize dashes
    normalized = re.sub(r'\s+', ' ', normalized)  # Normalize spaces
    
    return normalized


def normalize_dog_name_for_storage(name: Optional[str]) -> Optional[str]:
    """Normalize dog name for storage (convert to uppercase)"""
    if not name:
        return None
    
    # Convert to uppercase and clean spaces
    normalized = name.strip().upper()
    normalized = re.sub(r'\s+', ' ', normalized)  # Normalize spaces
    
    return normalized


def find_dog_by_name_and_reg(name: str, reg_number: str, existing_dogs: List[Dog]) -> Optional[Dog]:
    """Find dog by name and registration number"""
    norm_name = normalize_dog_name_for_comparison(name)
    norm_reg = normalize_for_comparison(reg_number)
    
    for dog in existing_dogs:
        # Check by registration number first (stronger identifier)
        if norm_reg and dog.registration_number:
            existing_norm_reg = normalize_for_comparison(dog.registration_number)
            if norm_reg == existing_norm_reg:
                return dog
        
        # Check by name
        if norm_name and dog.name:
            existing_norm_name = normalize_dog_name_for_comparison(dog.name)
            if norm_name == existing_norm_name:
                return dog
    
    return None


def collect_missing_parents(records: List[Dict], existing_dogs: List[Dog], logger) -> Dict:
    """Collect all missing parents from the records"""
    
    missing_fathers = {}  # reg_number -> parent_info
    missing_mothers = {}  # reg_number -> parent_info
    
    logger.info("Collecting missing parents from records...")
    
    for i, record in enumerate(records, 1):
        father_name = clean_field_value(record.get('fatherName'))
        father_reg = clean_field_value(record.get('fatherRegNumber'))
        mother_name = clean_field_value(record.get('motherName'))
        mother_reg = clean_field_value(record.get('motherRegNumber'))
        
        # Check father
        if father_name and father_reg:
            existing_father = find_dog_by_name_and_reg(father_name, father_reg, existing_dogs)
            if not existing_father:
                # Use registration number as key for deduplication
                norm_father_reg = normalize_for_comparison(father_reg)
                if norm_father_reg not in missing_fathers:
                    missing_fathers[norm_father_reg] = {
                        'name': father_name,
                        'registration_number': father_reg,
                        'sex': 'Male',
                        'source_record': i
                    }
        
        # Check mother
        if mother_name and mother_reg:
            existing_mother = find_dog_by_name_and_reg(mother_name, mother_reg, existing_dogs)
            if not existing_mother:
                # Use registration number as key for deduplication
                norm_mother_reg = normalize_for_comparison(mother_reg)
                if norm_mother_reg not in missing_mothers:
                    missing_mothers[norm_mother_reg] = {
                        'name': mother_name,
                        'registration_number': mother_reg,
                        'sex': 'Female',
                        'source_record': i
                    }
    
    logger.info(f"Found {len(missing_fathers)} unique missing fathers")
    logger.info(f"Found {len(missing_mothers)} unique missing mothers")
    
    return {
        'fathers': missing_fathers,
        'mothers': missing_mothers
    }


def import_missing_parents(missing_parents: Dict, db: Session, logger) -> Dict:
    """Import missing parents as new dog records"""
    
    stats = {
        'fathers_imported': 0,
        'mothers_imported': 0,
        'errors': 0
    }
    
    # Import fathers
    logger.info("Importing missing fathers...")
    for norm_reg, parent_info in missing_parents['fathers'].items():
        try:
            normalized_name = normalize_dog_name_for_storage(parent_info['name'])
            normalized_reg = normalize_registration_number(parent_info['registration_number'])
            
            new_father = Dog(
                name=normalized_name,
                sex='Male',
                breed='DALMATIAN',
                registration_number=normalized_reg
            )
            
            db.add(new_father)
            db.flush()  # Get ID without committing
            
            logger.info(f"Imported father: {normalized_name} (ID: {new_father.id}) - {normalized_reg}")
            stats['fathers_imported'] += 1
            
        except Exception as e:
            logger.error(f"Error importing father {parent_info['name']}: {e}")
            stats['errors'] += 1
    
    # Import mothers
    logger.info("Importing missing mothers...")
    for norm_reg, parent_info in missing_parents['mothers'].items():
        try:
            normalized_name = normalize_dog_name_for_storage(parent_info['name'])
            normalized_reg = normalize_registration_number(parent_info['registration_number'])
            
            new_mother = Dog(
                name=normalized_name,
                sex='Female',
                breed='DALMATIAN',
                registration_number=normalized_reg
            )
            
            db.add(new_mother)
            db.flush()  # Get ID without committing
            
            logger.info(f"Imported mother: {normalized_name} (ID: {new_mother.id}) - {normalized_reg}")
            stats['mothers_imported'] += 1
            
        except Exception as e:
            logger.error(f"Error importing mother {parent_info['name']}: {e}")
            stats['errors'] += 1
    
    # Commit all changes
    try:
        db.commit()
        logger.info("All parent records committed successfully")
    except Exception as e:
        logger.error(f"Commit failed: {e}")
        db.rollback()
        raise
    
    return stats


def main():
    """Main function"""
    logger = setup_logging()
    logger.info("BULGARIA IMPORT PHASE 2 (FIXED) - Missing Parents")
    logger.info("=" * 60)
    
    # File path
    csv_file = Path(__file__).parent / 'data' / 'Registar_BDK_2025_raboten.csv'
    
    if not csv_file.exists():
        logger.error(f"CSV file not found: {csv_file}")
        return False
    
    try:
        # Load CSV data
        records = load_csv_data(csv_file)
        
        # Import to database
        db = next(get_db())
        try:
            # Get all existing dogs
            existing_dogs = db.query(Dog).all()
            logger.info(f"Loaded {len(existing_dogs)} existing dogs")
            
            # Collect missing parents
            missing_parents = collect_missing_parents(records, existing_dogs, logger)
            
            # Import missing parents
            stats = import_missing_parents(missing_parents, db, logger)
            
            # Print summary
            logger.info("\n" + "=" * 60)
            logger.info("PHASE 2 IMPORT SUMMARY:")
            logger.info(f"Missing fathers imported: {stats['fathers_imported']}")
            logger.info(f"Missing mothers imported: {stats['mothers_imported']}")
            logger.info(f"Total parents imported: {stats['fathers_imported'] + stats['mothers_imported']}")
            logger.info(f"Errors: {stats['errors']}")
            logger.info("=" * 60)
            
            return stats['errors'] == 0
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
