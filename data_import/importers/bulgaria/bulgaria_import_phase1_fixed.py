#!/usr/bin/env python3
"""
Bulgarian Dalmatian Registry Data Import - Phase 1 (Fixed)
Импортира данни от български регистър за далматинци - етап 1

Този скрипт импортира всички уникални кучета без родителски връзки.
Използва подобрена логика за откриване на дублирани записи.

Структура на CSV файла:
dateOfBirth;sex;name;microchip;regCode;fatherName;fatherRegNumber;motherName;motherRegNumber;breeder
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
    log_file = log_dir / f'bulgaria_import_fixed_{timestamp}.log'
    
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


def parse_bulgarian_date(date_str: Optional[str]) -> Optional[str]:
    """Parse Bulgarian date string and convert to database format"""
    if not date_str or date_str.strip() in ['', 'None']:
        return None
    
    date_str = date_str.strip()
    
    # Remove 'г.' (година) if present
    date_str = date_str.replace(' г.', '').replace('г.', '')
    
    # Handle DD.MM.YYYY format
    if '.' in date_str:
        try:
            parts = date_str.split('.')
            if len(parts) == 3:
                day, month, year = parts
                # Convert to ISO format YYYY-MM-DD
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except Exception as e:
            logging.warning(f"Could not parse date '{date_str}': {e}")
            pass
    
    return None


def normalize_registration_number(reg_code: Optional[str]) -> Optional[str]:
    """Normalize registration number for comparison and storage"""
    if not reg_code or reg_code.strip() in ['', 'None']:
        return None
    
    # Keep original value for display, but normalize for comparison
    reg_code = reg_code.strip()
    
    # For storage, we keep the original format but clean it
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
    
    # "PK04704/05" should match "PK 04704/05" -> both become "PK04704/05"
    # This is already handled by removing spaces
    
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


def check_for_duplicates(record: Dict, existing_dogs: List[Dog], logger) -> Optional[Dog]:
    """
    Check if a record is a duplicate of existing dogs
    Returns the existing dog if duplicate is found, None otherwise
    """
    name = record.get('name', '').strip()
    reg_code = record.get('regCode', '').strip()
    microchip = record.get('microchip', '').strip()
    date_of_birth = parse_bulgarian_date(record.get('dateOfBirth'))
    
    # Normalize values for comparison
    norm_name = normalize_dog_name_for_comparison(name)
    norm_reg = normalize_for_comparison(reg_code)
    
    for existing_dog in existing_dogs:
        # Check 1: Registration number match (strongest identifier)
        if norm_reg and existing_dog.registration_number:
            existing_norm_reg = normalize_for_comparison(existing_dog.registration_number)
            if norm_reg == existing_norm_reg:
                logger.warning(f"DUPLICATE by reg number: '{reg_code}' matches existing '{existing_dog.registration_number}' for dog {existing_dog.name} (ID: {existing_dog.id})")
                return existing_dog
        
        # Check 2: Microchip match (very strong identifier)
        if microchip and existing_dog.microchip and microchip == existing_dog.microchip:
            logger.warning(f"DUPLICATE by microchip: '{microchip}' for dog {existing_dog.name} (ID: {existing_dog.id})")
            return existing_dog
        
        # Check 3: Name + date of birth match (strong identifier)
        if norm_name and date_of_birth and existing_dog.name and existing_dog.date_of_birth:
            existing_norm_name = normalize_dog_name_for_comparison(existing_dog.name)
            if norm_name == existing_norm_name and str(date_of_birth) == str(existing_dog.date_of_birth):
                logger.warning(f"DUPLICATE by name+date: '{name}' ({date_of_birth}) matches existing '{existing_dog.name}' (ID: {existing_dog.id})")
                return existing_dog
    
    return None


def import_dogs_only(records: List[Dict], db: Session, logger) -> Dict:
    """Import dogs without parent relationships"""
    
    stats = {
        'total_records': len(records),
        'imported': 0,
        'skipped_duplicates': 0,
        'errors': 0,
        'skipped_records': []
    }
    
    logger.info(f"Starting import of {len(records)} records...")
    
    # Get all existing dogs once for duplicate checking
    existing_dogs = db.query(Dog).all()
    logger.info(f"Loaded {len(existing_dogs)} existing dogs for duplicate checking")
    
    for i, record in enumerate(records, 1):
        try:
            # Extract and clean basic fields
            name = clean_field_value(record.get('name'))
            sex = clean_field_value(record.get('sex'))
            reg_code = clean_field_value(record.get('regCode'))
            microchip = clean_field_value(record.get('microchip'))
            breeder = clean_field_value(record.get('breeder'))
            date_of_birth = parse_bulgarian_date(record.get('dateOfBirth'))
            
            # Skip records with missing essential data
            if not name:
                logger.warning(f"Record {i}: Skipping - missing name")
                stats['errors'] += 1
                continue
                
            if not sex or sex not in ['Male', 'Female']:
                logger.warning(f"Record {i}: Skipping - invalid sex '{sex}' for dog {name}")
                stats['errors'] += 1
                continue
            
            # Check for duplicates
            duplicate_dog = check_for_duplicates(record, existing_dogs, logger)
            if duplicate_dog:
                logger.info(f"Record {i}: Skipping duplicate - {name} already exists as {duplicate_dog.name} (ID: {duplicate_dog.id})")
                stats['skipped_duplicates'] += 1
                stats['skipped_records'].append({
                    'name': name,
                    'reason': 'duplicate',
                    'existing_id': duplicate_dog.id,
                    'existing_name': duplicate_dog.name
                })
                continue
            
            # Normalize name for storage (convert to uppercase)
            normalized_name = normalize_dog_name_for_storage(name)
            normalized_reg = normalize_registration_number(reg_code)
              # Create new dog record
            new_dog = Dog(
                name=normalized_name,
                sex=sex,
                breed='DALMATIAN',
                date_of_birth=date_of_birth,
                registration_number=normalized_reg,
                microchip=microchip,
                breeder=breeder
            )
            
            db.add(new_dog)
            db.flush()  # Get ID without committing
            
            # Add to existing dogs list for future duplicate checking
            existing_dogs.append(new_dog)
            
            logger.info(f"Record {i}: Imported {normalized_name} (ID: {new_dog.id}) - {normalized_reg}")
            stats['imported'] += 1
            
            # Commit in batches
            if stats['imported'] % 50 == 0:
                db.commit()
                logger.info(f"Committed batch of 50 records. Total imported: {stats['imported']}")
                
        except Exception as e:
            logger.error(f"Record {i}: Error importing {record.get('name', 'UNKNOWN')}: {e}")
            stats['errors'] += 1
            db.rollback()
    
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
    logger.info("BULGARIA IMPORT PHASE 1 (FIXED) - Dogs Only")
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
            stats = import_dogs_only(records, db, logger)
            
            # Print summary
            logger.info("\n" + "=" * 60)
            logger.info("IMPORT SUMMARY:")
            logger.info(f"Total records processed: {stats['total_records']}")
            logger.info(f"Successfully imported: {stats['imported']}")
            logger.info(f"Skipped (duplicates): {stats['skipped_duplicates']}")
            logger.info(f"Errors: {stats['errors']}")
            logger.info("=" * 60)
            
            if stats['skipped_records']:
                logger.info(f"\nSkipped records details:")
                for skip in stats['skipped_records'][:10]:  # Show first 10
                    logger.info(f"  - {skip['name']}: {skip['reason']} (existing: {skip.get('existing_name', 'N/A')})")
                if len(stats['skipped_records']) > 10:
                    logger.info(f"  ... and {len(stats['skipped_records']) - 10} more")
            
            return stats['errors'] == 0
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
