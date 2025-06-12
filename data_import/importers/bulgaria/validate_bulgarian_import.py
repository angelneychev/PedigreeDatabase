#!/usr/bin/env python3
"""
Правилна валидация на българския импорт
Проверява данните по CSV файла и регистрационни номера, БЕЗ използване на поле за националност
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from database import get_db
from models import Dog
from sqlalchemy.orm import Session

def normalize_for_comparison(text):
    """Normalize text for comparison - same logic as import scripts"""
    if not text or text.strip() == '':
        return None
    
    # Convert to uppercase and remove extra spaces
    normalized = text.strip().upper()
    
    # Handle registration number normalization
    if any(char.isdigit() for char in normalized):
        # This looks like a registration number
        # Remove spaces and normalize common patterns
        normalized = normalized.replace(' ', '')
        
        # Handle specific Norwegian patterns
        if normalized.startswith('N') and '/' in normalized:
            # Convert "N17385/06" to "NO17385/06"
            normalized = normalized.replace('N', 'NO', 1)
    
    return normalized

def run_validation():
    """Run validation based on CSV data and registration numbers"""
    
    csv_file = Path(__file__).parent / "data" / "Registar_BDK_2025_raboten.csv"
    
    print("=== ВАЛИДАЦИЯ НА БЪЛГАРСКИЯ ИМПОРТ ===")
    print(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if not csv_file.exists():
        print(f"❌ CSV файлът не е намерен: {csv_file}")
        return
    
    # Get database session
    db = next(get_db())
    
    try:
        # 1. Зареди CSV данните
        csv_dogs = []
        bulgarian_reg_numbers = set()
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            
            for row in csv_reader:
                csv_dogs.append(row)
                reg_code = row['regCode'].strip() if row['regCode'] else None
                if reg_code:
                    bulgarian_reg_numbers.add(reg_code)
        
        print(f"📄 Записи в CSV файла: {len(csv_dogs)}")
        print(f"📋 Уникални български регистрационни номера: {len(bulgarian_reg_numbers)}")
        print()
        
        # 2. Намери всички кучета с български регистрационни номера в базата данни
        imported_dogs = []
        for reg_num in bulgarian_reg_numbers:
            dog = db.query(Dog).filter(Dog.registration_number == reg_num).first()
            if dog:
                imported_dogs.append(dog)
        
        print(f"🐕 Импортирани кучета в базата данни: {len(imported_dogs)}")
        
        # 3. Провери за липсващи кучета
        missing_dogs = []
        for row in csv_dogs:
            reg_code = row['regCode'].strip() if row['regCode'] else None
            dog_name = row['name'].strip()
            
            found = False
            if reg_code:
                # Search by registration number
                dog = db.query(Dog).filter(Dog.registration_number == reg_code).first()
                if dog:
                    found = True
            
            if not found:
                # Search by name if no reg number or not found
                dog = db.query(Dog).filter(Dog.name == dog_name).first()
                if dog:
                    found = True
            
            if not found:
                missing_dogs.append(f"{dog_name} ({reg_code})")
        
        print(f"❌ Липсващи кучета: {len(missing_dogs)}")
        if missing_dogs and len(missing_dogs) <= 10:
            for missing in missing_dogs:
                print(f"   - {missing}")
        elif len(missing_dogs) > 10:
            print(f"   Първите 10: {missing_dogs[:10]}")
        
        print()
        
        # 4. Провери родителските връзки
        print("=== АНАЛИЗ НА РОДИТЕЛСКИТЕ ВРЪЗКИ ===")
        
        dogs_with_both_parents = 0
        dogs_with_father_only = 0
        dogs_with_mother_only = 0
        orphaned_dogs = 0
        total_relationships = 0
        missing_relationships = []
        
        for row in csv_dogs:
            reg_code = row['regCode'].strip() if row['regCode'] else None
            dog_name = row['name'].strip()
            father_name = row['fatherName'].strip() if row['fatherName'] else None
            mother_name = row['motherName'].strip() if row['motherName'] else None
            
            # Find the dog in database
            dog = None
            if reg_code:
                dog = db.query(Dog).filter(Dog.registration_number == reg_code).first()
            if not dog:
                dog = db.query(Dog).filter(Dog.name == dog_name).first()
            
            if not dog:
                continue
            
            has_father = dog.sire_id is not None
            has_mother = dog.dam_id is not None
            
            if has_father and has_mother:
                dogs_with_both_parents += 1
                total_relationships += 2
            elif has_father:
                dogs_with_father_only += 1
                total_relationships += 1
            elif has_mother:
                dogs_with_mother_only += 1
                total_relationships += 1
            else:
                orphaned_dogs += 1
            
            # Check for missing relationships
            if father_name and not has_father:
                missing_relationships.append(f"{dog_name} - липсва баща: {father_name}")
            if mother_name and not has_mother:
                missing_relationships.append(f"{dog_name} - липсва майка: {mother_name}")
        
        print(f"👨‍👩‍👧‍👦 Кучета с двамата родители: {dogs_with_both_parents}")
        print(f"👨‍👧‍👦 Кучета само с баща: {dogs_with_father_only}")
        print(f"👩‍👧‍👦 Кучета само с майка: {dogs_with_mother_only}")
        print(f"🚼 Кучета без родители: {orphaned_dogs}")
        print(f"🔗 Общо установени връзки: {total_relationships}")
        print(f"❌ Липсващи връзки: {len(missing_relationships)}")
        
        if missing_relationships and len(missing_relationships) <= 10:
            print("\nЛипсващи връзки:")
            for missing in missing_relationships:
                print(f"   - {missing}")
        elif len(missing_relationships) > 10:
            print(f"\nПървите 10 липсващи връзки: {missing_relationships[:10]}")
        
        # 5. Изчисли статистики
        print()
        print("=== ФИНАЛНИ СТАТИСТИКИ ===")
        
        expected_dogs = len(csv_dogs)
        imported_count = len(imported_dogs)
        import_success_rate = (imported_count / expected_dogs) * 100 if expected_dogs > 0 else 0
        
        expected_relationships = sum(1 for row in csv_dogs if row['fatherName'].strip()) + sum(1 for row in csv_dogs if row['motherName'].strip())
        relationship_success_rate = (total_relationships / expected_relationships) * 100 if expected_relationships > 0 else 0
        
        print(f"📊 Очаквани кучета от CSV: {expected_dogs}")
        print(f"📊 Импортирани кучета: {imported_count}")
        print(f"🎯 Успешност на импорта: {import_success_rate:.1f}%")
        print(f"🔗 Очаквани връзки: {expected_relationships}")
        print(f"🔗 Установени връзки: {total_relationships}")
        print(f"🎯 Успешност на връзките: {relationship_success_rate:.1f}%")
        print()
        
        # 6. Примерни записи
        print("=== ПРИМЕРНИ ИМПОРТИРАНИ КУЧЕТА ===")
        sample_dogs = imported_dogs[:5] if len(imported_dogs) >= 5 else imported_dogs
        
        for dog in sample_dogs:
            father_name = "Неизвестен"
            mother_name = "Неизвестна"
            
            if dog.sire_id:
                father = db.query(Dog).filter(Dog.id == dog.sire_id).first()
                if father:
                    father_name = father.name
            
            if dog.dam_id:
                mother = db.query(Dog).filter(Dog.id == dog.dam_id).first()
                if mother:
                    mother_name = mother.name
            
            print(f"🐕 {dog.name} ({dog.registration_number})")
            print(f"   👨 Баща: {father_name}")
            print(f"   👩 Майка: {mother_name}")
            print()
        
        print("=== ВАЛИДАЦИЯТА ЗАВЪРШЕНА ===")
        
        # Overall success indicator
        overall_success = (
            import_success_rate > 95 and 
            relationship_success_rate > 95 and 
            len(missing_dogs) == 0
        )
        
        print(f"🏆 Общ резултат: {'УСПЕШЕН' if overall_success else 'ЧАСТИЧНО УСПЕШЕН'}")
        
    except Exception as e:
        print(f"❌ Грешка при валидацията: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run_validation()
