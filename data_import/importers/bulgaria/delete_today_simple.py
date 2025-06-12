#!/usr/bin/env python3
"""
Изтриване на всички записи импортирани днес (2025-06-12)
"""

import sys
import os
from datetime import datetime, date
import logging

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, func
from database import engine
from models import Dog

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/delete_today_records_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def delete_today_records():
    """Изтрива всички записи импортирани днес"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Намери всички кучета импортирани днес
        today = date.today()
        today_dogs = session.query(Dog).filter(
            func.date(Dog.created_at) == today
        ).all()
        
        logger.info(f"FIND: Намерени {len(today_dogs)} кучета импортирани днес ({today})")
        
        if len(today_dogs) == 0:
            logger.info("OK: Няма записи за изтриване")
            return
        
        # Покажи първите 10 записа за потвърждение
        logger.info("LIST: Примери от записите за изтриване:")
        for i, dog in enumerate(today_dogs[:10], 1):
            logger.info(f"  {i}. {dog.name} (ID: {dog.id}) - {dog.registration_number}")
        
        if len(today_dogs) > 10:
            logger.info(f"  ... и още {len(today_dogs) - 10} записа")
        
        # Автоматично потвърждение
        logger.info(f"AUTO: Автоматично изтриване на {len(today_dogs)} записа...")
        
        # Изтрий записите
        deleted_count = 0
        for dog in today_dogs:
            logger.info(f"DELETE: Изтривам {dog.name} (ID: {dog.id})")
            session.delete(dog)
            deleted_count += 1
        
        # Commit промените
        session.commit()
        logger.info(f"SUCCESS: Успешно изтрити {deleted_count} записа")
        
        # Проверка дали изтриването е успешно
        remaining_today = session.query(Dog).filter(
            func.date(Dog.created_at) == today
        ).count()
        
        logger.info(f"CHECK: Останали {remaining_today} записа от днес")
        
        if remaining_today == 0:
            logger.info("COMPLETE: Всички днешни записи са успешно изтрити!")
        else:
            logger.warning(f"WARNING: Все още има {remaining_today} записа от днес")
        
    except Exception as e:
        session.rollback()
        logger.error(f"ERROR: Грешка при изтриването: {e}")
        raise
    finally:
        session.close()

def main():
    logger.info("START: ЗАПОЧВА ИЗТРИВАНЕ НА ДНЕШНИТЕ ЗАПИСИ")
    logger.info("=" * 50)
    
    try:
        delete_today_records()
        logger.info("FINISHED: ИЗТРИВАНЕТО ЗАВЪРШИ УСПЕШНО!")
    except Exception as e:
        logger.error(f"FAILED: ГРЕШКА ПРИ ИЗТРИВАНЕТО: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
