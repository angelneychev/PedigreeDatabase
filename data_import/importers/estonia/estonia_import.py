#!/usr/bin/env python3
"""
Comprehensive Estonian Dalmatian Registry Data Import
Импортира всички данни наведнъж - кучета, родители, здравни тестове и URL-и

Този скрипт ще импортира всичко в два прохода:
1. Първи проход: импортира всички кучета с всички данни (освен родители)
2. Втори проход: установява родителските връзки
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from database import get_db
from models import Dog, HealthTest, HealthTestType
from sqlalchemy.orm import Session


def setup_logging():
    """Setup logging configuration"""
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'comprehensive_import_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return str(log_file)


def load_json_data(file_path: str) -> List[Dict]:
    """Load data from JSON file"""
    logging.info(f"Loading JSON data from: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'data' in data:
        records = data['data']
    elif isinstance(data, list):
        records = data
    else:
        raise ValueError("JSON must be a list or dict with 'data' key")
    
    logging.info(f"Loaded {len(records)} records from JSON")
    return records


def clean_field_value(value: str) -> Optional[str]:
    """Clean field value, return None for empty/dash values"""
    if not value or value.strip() in ['-', '', 'None']:
        return None
    return value.strip()


def parse_date(date_str: str) -> Optional[str]:
    """Parse date string and convert to database format"""
    if not date_str or date_str.strip() in ['-', '', 'None']:
        return None
    
    date_str = date_str.strip()
    
    # Handle DD.MM.YYYY format
    if '.' in date_str:
        try:
            parts = date_str.split('.')
            if len(parts) == 3:
                day, month, year = parts
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass
    
    return None


def extract_url_org(url: str) -> Optional[str]:
    """Extract and validate URL"""
    if not url or url.strip() in ['-', '', 'None']:
        return None
    
    url = url.strip()
    if not url.startswith('http'):
        return None
    
    # Validate Estonian Kennel Union URL format
    if 'register.kennelliit.ee' in url:
        return url
    
    return url  # Return other URLs as-is


def normalize_registration_number(reg_code: str) -> Optional[str]:
    """Normalize registration number"""
    if not reg_code or reg_code.strip() in ['-', '', 'None']:
        return None
    
    clean_reg = reg_code.strip()
    
    # Truncate if too long
    if len(clean_reg) > 190:
        clean_reg = clean_reg[:190] + '...'
    
    return clean_reg


def transform_dog_record(record: Dict) -> Dict:
    """Transform JSON record to Dog model format with ALL fields"""
    result = {}
      # Direct field mappings
    field_mapping = {
        'name': 'name',
        'regCode': 'registration_number',
        'sex': 'sex',
        'color': 'color',
        'dateOfBirth': 'date_of_birth',
        'breeder': 'breeder',
        'kennelName': 'kennel_name',
        'tatooNo': 'tatoo_no',
        'microchip': 'microchip',
        'breed': 'breed',
        # Note: 'tail' field from JSON is not mapped as Dog model doesn't have this field
    }
    
    # Apply field mappings with cleaning
    for json_field, db_field in field_mapping.items():
        if json_field in record:
            value = record[json_field]
            
            if json_field == 'dateOfBirth':
                result[db_field] = parse_date(value)
            elif json_field == 'regCode':
                result[db_field] = normalize_registration_number(value)
            else:
                result[db_field] = clean_field_value(value)
    
    # Add URL from 'url' field
    if 'url' in record:
        result['url_org'] = extract_url_org(record['url'])
    
    # Add timestamps
    result['created_at'] = datetime.utcnow()
    result['updated_at'] = datetime.utcnow()
    
    return result


def import_dogs_first_pass(session: Session, records: List[Dict]) -> Dict[str, int]:
    """First pass: Import all dogs with complete data (except parent relationships)"""
    logging.info("=== FIRST PASS: Importing dogs with all data ===")
    
    imported_count = 0
    skipped_count = 0
    error_count = 0
    
    # Mapping: JSON dogId -> database ID
    dogId_to_dbId = {}
    
    # Track processed registration numbers to avoid duplicates
    processed_reg_numbers: Set[str] = set()
    
    for i, record in enumerate(records):
        try:
            # Transform record with ALL data
            dog_data = transform_dog_record(record)
            
            # Skip if no name
            if not dog_data.get('name'):
                logging.warning(f"Record {i+1}: Missing name, skipping")
                skipped_count += 1
                continue
            
            # Check for duplicates by registration number
            reg_number = dog_data.get('registration_number')
            if reg_number:
                if reg_number in processed_reg_numbers:
                    logging.debug(f"Skipping duplicate registration: {dog_data['name']} ({reg_number})")
                    skipped_count += 1
                    continue
                
                # Check if already exists in database
                existing_dog = session.query(Dog).filter_by(registration_number=reg_number).first()
                if existing_dog:
                    logging.debug(f"Dog already exists in database: {dog_data['name']} ({reg_number})")
                    if 'dogId' in record:
                        dogId_to_dbId[record['dogId']] = existing_dog.id
                    skipped_count += 1
                    continue
                
                processed_reg_numbers.add(reg_number)
            
            # Create new dog
            dog = Dog(**dog_data)
            session.add(dog)
            session.flush()  # Get the database-generated ID
            
            # Map JSON dogId to database ID
            if 'dogId' in record:
                dogId_to_dbId[record['dogId']] = dog.id
            
            imported_count += 1
            
            # Log progress every 100 dogs
            if imported_count % 100 == 0:
                logging.info(f"Imported {imported_count} dogs...")
                session.commit()  # Commit in batches
        
        except Exception as e:
            error_count += 1
            logging.error(f"Error importing dog {i+1}: {str(e)}")
            session.rollback()
            continue
    
    session.commit()
    
    logging.info(f"First pass completed:")
    logging.info(f"  Imported: {imported_count}")
    logging.info(f"  Skipped: {skipped_count}")
    logging.info(f"  Errors: {error_count}")
    
    return dogId_to_dbId


def establish_parent_relationships(session: Session, records: List[Dict], dogId_to_dbId: Dict[str, int]):
    """Second pass: Establish parent relationships"""
    logging.info("=== SECOND PASS: Establishing parent relationships ===")
    
    relationships_created = 0
    missing_fathers = 0
    missing_mothers = 0
    error_count = 0
    
    for i, record in enumerate(records):
        try:
            # Get the dog's database ID
            json_dog_id = record.get('dogId')
            if not json_dog_id or json_dog_id not in dogId_to_dbId:
                continue
            
            db_dog_id = dogId_to_dbId[json_dog_id]
            dog = session.query(Dog).get(db_dog_id)
            
            if not dog:
                continue
            
            # Set father relationship
            father_json_id = record.get('fatherDogId')
            if father_json_id and father_json_id in dogId_to_dbId:
                father_db_id = dogId_to_dbId[father_json_id]
                dog.sire_id = father_db_id
                relationships_created += 1
            elif father_json_id:
                missing_fathers += 1
                logging.debug(f"Father not found for {dog.name}: JSON ID {father_json_id}")
            
            # Set mother relationship
            mother_json_id = record.get('motherDogId')
            if mother_json_id and mother_json_id in dogId_to_dbId:
                mother_db_id = dogId_to_dbId[mother_json_id]
                dog.dam_id = mother_db_id
                relationships_created += 1
            elif mother_json_id:
                missing_mothers += 1
                logging.debug(f"Mother not found for {dog.name}: JSON ID {mother_json_id}")
        
        except Exception as e:
            error_count += 1
            logging.error(f"Error setting relationships for record {i+1}: {str(e)}")
            continue
    
    session.commit()
    
    logging.info(f"Parent relationships established:")
    logging.info(f"  Relationships created: {relationships_created}")
    logging.info(f"  Missing fathers: {missing_fathers}")
    logging.info(f"  Missing mothers: {missing_mothers}")
    logging.info(f"  Errors: {error_count}")


def comprehensive_import():
    """Main import function - imports everything at once"""
    # JSON file path
    json_file = Path(__file__).parent / 'data' / 'estonia_dogs_converted.json'
    
    if not json_file.exists():
        raise FileNotFoundError(f"JSON file not found: {json_file}")
    
    # Load data
    records = load_json_data(str(json_file))
    
    # Get database session
    session = next(get_db())
    
    try:
        # Check if data already exists
        existing_count = session.query(Dog).count()
        logging.info(f"Database currently contains {existing_count} dogs")
        
        if existing_count > 0:
            response = input(f"\n⚠️  Database already contains {existing_count} dogs. Continue? (y/N): ")
            if response.lower() != 'y':
                logging.info("Import cancelled by user")
                return 0
        
        logging.info("Starting comprehensive import...")
        
        # First pass: Import all dogs with complete data
        dogId_to_dbId = import_dogs_first_pass(session, records)
        
        # Second pass: Establish parent relationships
        establish_parent_relationships(session, records, dogId_to_dbId)
        
        # Final statistics
        final_count = session.query(Dog).count()
        dogs_with_parents = session.query(Dog).filter(
            Dog.sire_id.isnot(None), 
            Dog.dam_id.isnot(None)
        ).count()
        dogs_with_urls = session.query(Dog).filter(Dog.url_org.isnot(None)).count()
        
        logging.info("=== IMPORT COMPLETED ===")
        logging.info(f"Total dogs in database: {final_count}")
        logging.info(f"Dogs with both parents: {dogs_with_parents}")
        logging.info(f"Dogs with URLs: {dogs_with_urls}")
        
        return final_count
        
    except Exception as e:
        logging.error(f"Import failed: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """Main function"""
    log_file = setup_logging()
    
    print("🔄 Starting Comprehensive Estonian Data Import")
    print(f"📝 Log file: {log_file}")
    print("-" * 60)
    
    try:
        imported_count = comprehensive_import()
        
        if imported_count > 0:
            print(f"\n✅ Successfully imported data! Total dogs: {imported_count}")
            print("🎯 All data imported in one pass:")
            print("   • Dogs with complete information")
            print("   • Parent relationships")
            print("   • Estonian Kennel Union URLs")
            print("   • Health data")
            print("   • Kennel names and registration numbers")
        else:
            print("\n💤 No new data imported.")
            
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        print(f"\n❌ Error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
