#!/usr/bin/env python3
"""
Bulgarian Dalmatian Registry Data Import - Phase 3 (Fixed)
Установява родителските връзки - етап 3

Този скрипт намира родителите за всяко куче и установява връзките.
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
    log_file = log_dir / f'bulgaria_import_phase3_relationships_{timestamp}.log'
    
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


def find_offspring_dog(record: Dict, existing_dogs: List[Dog]) -> Optional[Dog]:
    """Find the offspring dog from the record"""
    offspring_name = clean_field_value(record.get('name'))
    offspring_reg = clean_field_value(record.get('regCode'))
    
    if not offspring_name:
        return None
    
    if offspring_reg:
        return find_dog_by_name_and_reg(offspring_name, offspring_reg, existing_dogs)
    else:
        # Find by name only
        norm_name = normalize_dog_name_for_comparison(offspring_name)
        for dog in existing_dogs:
            if dog.name:
                existing_norm_name = normalize_dog_name_for_comparison(dog.name)
                if norm_name == existing_norm_name:
                    return dog
    
    return None


def update_parent_relationships(records: List[Dict], existing_dogs: List[Dog], db: Session, logger) -> Dict:
    """Update parent relationships for all dogs"""
    
    stats = {
        'total_records': len(records),
        'dogs_found': 0,
        'fathers_linked': 0,
        'mothers_linked': 0,
        'missing_fathers': 0,
        'missing_mothers': 0,
        'missing_offspring': 0,
        'errors': 0
    }
    
    logger.info(f"Updating parent relationships for {len(records)} records...")
    
    for i, record in enumerate(records, 1):
        try:
            # Find the offspring dog
            offspring_dog = find_offspring_dog(record, existing_dogs)
            if not offspring_dog:
                logger.warning(f"Record {i}: Offspring dog not found: {record.get('name', 'UNKNOWN')}")
                stats['missing_offspring'] += 1
                continue
                
            stats['dogs_found'] += 1
            
            # Get parent information
            father_name = clean_field_value(record.get('fatherName'))
            father_reg = clean_field_value(record.get('fatherRegNumber'))
            mother_name = clean_field_value(record.get('motherName'))
            mother_reg = clean_field_value(record.get('motherRegNumber'))
            
            # Find and link father
            if father_name and father_reg:
                father_dog = find_dog_by_name_and_reg(father_name, father_reg, existing_dogs)
                if father_dog:
                    offspring_dog.sire_id = father_dog.id
                    stats['fathers_linked'] += 1
                    logger.info(f"Record {i}: Linked father {father_dog.name} (ID: {father_dog.id}) to {offspring_dog.name} (ID: {offspring_dog.id})")
                else:
                    stats['missing_fathers'] += 1
                    logger.warning(f"Record {i}: Father not found: {father_name} ({father_reg})")
            
            # Find and link mother
            if mother_name and mother_reg:
                mother_dog = find_dog_by_name_and_reg(mother_name, mother_reg, existing_dogs)
                if mother_dog:
                    offspring_dog.dam_id = mother_dog.id
                    stats['mothers_linked'] += 1
                    logger.info(f"Record {i}: Linked mother {mother_dog.name} (ID: {mother_dog.id}) to {offspring_dog.name} (ID: {offspring_dog.id})")
                else:
                    stats['missing_mothers'] += 1
                    logger.warning(f"Record {i}: Mother not found: {mother_name} ({mother_reg})")
            
            # Commit in batches
            if i % 50 == 0:
                db.commit()
                logger.info(f"Committed batch at record {i}")
                
        except Exception as e:
            logger.error(f"Record {i}: Error updating relationships for {record.get('name', 'UNKNOWN')}: {e}")
            stats['errors'] += 1
    
    # Final commit
    try:
        db.commit()
        logger.info("Final commit completed successfully")
    except Exception as e:
        logger.error(f"Final commit failed: {e}")
        db.rollback()
        raise
    
    return stats


def main():
    """Main function"""
    logger = setup_logging()
    logger.info("BULGARIA IMPORT PHASE 3 (FIXED) - Parent Relationships")
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
            
            # Update parent relationships
            stats = update_parent_relationships(records, existing_dogs, db, logger)
            
            # Print summary
            logger.info("\n" + "=" * 60)
            logger.info("PHASE 3 IMPORT SUMMARY:")
            logger.info(f"Total records processed: {stats['total_records']}")
            logger.info(f"Offspring dogs found: {stats['dogs_found']}")
            logger.info(f"Fathers linked: {stats['fathers_linked']}")
            logger.info(f"Mothers linked: {stats['mothers_linked']}")
            logger.info(f"Total relationships: {stats['fathers_linked'] + stats['mothers_linked']}")
            logger.info(f"Missing fathers: {stats['missing_fathers']}")
            logger.info(f"Missing mothers: {stats['missing_mothers']}")
            logger.info(f"Missing offspring: {stats['missing_offspring']}")
            logger.info(f"Errors: {stats['errors']}")
            
            # Calculate success rate
            total_possible = stats['dogs_found'] * 2  # Each dog can have father + mother
            total_linked = stats['fathers_linked'] + stats['mothers_linked']
            if total_possible > 0:
                success_rate = (total_linked / total_possible) * 100
                logger.info(f"Success rate: {success_rate:.1f}% ({total_linked}/{total_possible})")
            
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
