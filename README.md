# Dalmatian Pedigree Database

A web-based system for managing pedigree data for Dalmatian dogs, built with FastAPI and MariaDB.

## 🏗️ Architecture
- **Backend**: FastAPI (Python)
- **Database**: MariaDB (MySQL)
- **Frontend**: HTML/CSS/JavaScript with Jinja2 templates
- **ORM**: SQLAlchemy

## 🎯 Key Features

### 🧬 Dynamic Pedigree Matrix
The core feature of this system is a **fully dynamic, left-to-right genealogical pedigree matrix** that:
- Supports **1 to 9 generations** selectable via dropdown
- Uses **binary path algorithm** for mathematical ancestor positioning
- Generates matrix structure dynamically (2, 4, 8, 16, ... boxes per column)
- Follows **Finnish Kennel Club style** layout
- Built with **for-loops** (no hardcoded rows)
- Overcomes database JOIN limitations with **recursive ancestor loading**

### 🐕 Dog Management
- **Dog registration** with complete data (name, registration number, gender, birth date, color, kennel, tattoo, microchip, breeder)
- **Search and filtering** by various criteria
- **Detailed dog profiles** with all information
- **Add and edit** dog information

### 👨‍👩‍👧 Pedigree Relationships
- **Parent relationship management** (sire/dam)
- **Automatic validation** of pedigree data
- **Family relationship visualization**
- **Generation tracking** up to 9 levels

### 🏥 Health Testing
- **Multiple health test types**:
  - Hip Dysplasia
  - Elbow Dysplasia
  - BAER Test (hearing)
  - Spine Examination
  - DNA test for von Willebrand disease (vWD)
- **Result recording** with date, location, and notes
- **Health test history** for each dog
- **Result validation** by test type

### 📥 Data Import
- **Automatic import** from JSON files
- **Three-phase import process**:
  1. Import dogs
  2. Create parent relationships
  3. Import health tests
- **Validation and logging** of all operations
- **Estonian Kennel Union format support**

### 🔧 Administration
- **Database cleanup** (`quick_clear.py`)
- **Data verification** (`verify_import.py`)
- **Data and schema migrations**
- **Health test type management**

## 🚀 How to Start the Project

### Prerequisites
- Python 3.8+
- MariaDB/MySQL server
- pip (Python package manager)

### Complete Startup Instructions

Follow these steps to get the Dalmatian Pedigree Database running on your system:

#### 1. **Clone the Project**
```bash
git clone <repository-url>
cd PedigreeDatabase
```

#### 2. **Create and Activate Virtual Environment**

**Windows PowerShell:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> **Important**: Always activate the virtual environment before running or developing the project! You should see `(venv)` at the start of your terminal prompt when it is active.

#### 3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

#### 4. **Database Setup**
Create the database in MariaDB/MySQL:
```bash
mysql -u root -p
```
Then in MySQL console:
```sql
CREATE DATABASE pedigree_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

#### 5. **Configure Database Connection**
Edit the `database.py` file and update the DATABASE_URL:
```python
DATABASE_URL = "mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/pedigree_db"
```
Replace `YOUR_PASSWORD` with your MariaDB/MySQL root password.

#### 6. **Create Database Tables**
```bash
python create_database.py
```

#### 7. **Start the Application**
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8007 --reload
```

#### 8. **Access the Application**
Open your web browser and go to: `http://127.0.0.1:8007`

---

**To deactivate the virtual environment later:**
```bash
deactivate
```

**To restart the application (after initial setup):**
1. Navigate to project directory
2. Activate virtual environment (step 2 above)
3. Start the application (step 7 above)

## 🧬 Dynamic Pedigree Matrix - Technical Implementation

### Core Algorithm
The pedigree matrix uses a **binary path algorithm** for mathematical ancestor positioning:

```python
# Binary path navigation for ancestors
def get_ancestor_at_position(pedigree_data, generation, position):
    """Navigate to specific ancestor using binary path"""
    current = pedigree_data
    
    # Convert position to binary path
    for level in range(generation):
        if current is None:
            return None
        
        # Extract bit for current level
        bit = (position >> (generation - 1 - level)) & 1
        
        # Navigate: 0 = sire, 1 = dam
        if bit == 0:
            current = current.get('sire')
        else:
            current = current.get('dam')
    
    return current
```

### Key Features
- **Recursive Data Loading**: Overcomes MariaDB's 61-table JOIN limit
- **Pre-computed Matrix**: Efficient template access with `ancestor_matrix.get(gen, {}).get(cell_index, None)`
- **Dynamic Generation**: For-loop based matrix supporting 1-9 generations
- **Binary Positioning**: Mathematical approach to ancestor placement

### Database Optimization
The system avoids complex JOINs by loading ancestors recursively:

```python
def get_parents_recursively(db, dog_id, generation=0, max_generation=9):
    """Load dog parents recursively to avoid JOIN limits"""
    if generation > max_generation or dog_id is None:
        return None
        
    dog = db.query(Dog).filter(Dog.id == dog_id).first()
    if not dog:
        return None
    
    return {
        'dog': dog,
        'sire': get_parents_recursively(db, dog.sire_id, generation + 1, max_generation),
        'dam': get_parents_recursively(db, dog.dam_id, generation + 1, max_generation)
    }
```

## 📁 Project Structure

```
PedigreeDatabase/
├── main.py                     # FastAPI application entry point
├── database.py                 # Database configuration
├── models/__init__.py          # SQLAlchemy models (Dog, HealthTest, etc.)
├── routers/
│   ├── dogs.py                # Dog-related API endpoints  
│   └── health.py              # Health test API endpoints
├── templates/
│   └── dog_detail.html        # Dynamic pedigree matrix template
├── static/                    # CSS and JavaScript files
├── crud.py                    # Database operations with recursive pedigree
├── data_import/
│   └── importers/
│       └── estonia/           # Estonian Kennel Union data
└── utils.py                   # Helper functions
```

## 🔄 Data Import System

### Estonian Kennel Union Import

**Location**: `data_import/importers/estonia/`

**Run import**:
```bash
cd data_import/importers/estonia
python estonia_import.py
```

**Last import results (May 2025)**:
- ✅ **2,240 dogs** imported successfully
- ✅ **3,386 parent relationships** created
- ✅ **0 errors** during import
- ✅ **Estonian URLs** preserved for all records

## 📊 Database Schema

### Core Tables

**dogs**: Main dog records with pedigree relationships
- `sire_id` / `dam_id`: Parent relationship fields for recursive navigation

**health_test_types**: Standardized test definitions
**health_tests**: Individual test results linked to dogs

## 🧪 Testing and Verification

```bash
# Verify imported data
python verify_import.py

# Check project status  
python project_status.py

# Clear database
python quick_clear.py
```

## 📝 API Documentation

FastAPI provides automatic documentation at:
- **Swagger UI**: `http://localhost:8007/docs`
- **ReDoc**: `http://localhost:8007/redoc`

## ✅ Current Status (December 2024)

### ✅ Completed Features:
- **Dynamic Pedigree Matrix**: Fully functional 1-9 generation system
- **Binary Path Algorithm**: Mathematical ancestor positioning
- **Recursive Database Loading**: Overcomes JOIN limitations
- **Pre-computed Ancestor Matrix**: Efficient template rendering
- **Estonian Data Import**: 2,240 dogs with complete pedigree data
- **Health Test Management**: Comprehensive health testing system
- **Clean Project Structure**: All temporary/debug files removed

### 🎯 Ready for Production:
The system is fully functional with:
- Dynamic pedigree matrix supporting all generation levels
- Robust database operations optimized for large datasets
- Clean, maintainable codebase with proper documentation
- Comprehensive data import capabilities

## 🤝 Contributing

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- Developer of the Dalmatian pedigree management system

---

*Note: This system successfully implements a fully dynamic pedigree matrix that overcomes traditional database limitations through innovative recursive loading and binary path algorithms.*
3. **Достъп до уеб интерфейса**: `http://localhost:8000`

### За импорт на нови данни:
1. **Създайте папка за новата страна**: `data_import/importers/[country_name]/`
2. **Копирайте шаблона**: от `template_for_future_countries/`
3. **Адаптирайте скрипта**: към формата на вашите данни
4. **Стартирайте импорта**: `python [country_name]_import.py`

## 📱 Mobile/UX Implementation & Testing

### Overview
The pedigree page uses localStorage (with sessionStorage and cookie fallback) to remember the user's generation selection, with a full-width, mobile-optimized layout. All AJAX, error handling, and offline/online detection are production-ready and tested.

### Key Features
- Clean URLs (no query parameters for generation)
- User preference persistence (localStorage/sessionStorage/cookie)
- Mobile-first design: touch targets, font sizing, offline/online detection
- AJAX pedigree updates (no page reload)
- Loading spinners, error messages, connectivity warnings
- Full-width layout, dog info card in pedigree header, generation selector in header

### Testing & Validation
- `/test_mobile_storage.html` – Full mobile/browser test suite
- `/mobile_test.html` – Device capability and storage fallback test
- All major browsers and mobile devices tested
- Server logs confirm correct API usage and preference saving

### Production Readiness
- All features validated and tested (see `TEST_RESULTS_FINAL.md` for details)
- Implementation summary and validation in `IMPLEMENTATION_COMPLETE.md`
- Security: No sensitive data in storage, server-side validation
- Performance: Fast AJAX, minimal payload, efficient caching

---

**For contributors:**
- Review the mobile/UX implementation summary before working on pedigree or UI features
- Test all changes for mobile compatibility and offline/online switching
- Follow the UI/UX standards in `CONTRIBUTING.md`

---
