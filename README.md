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

### 🧬 Inbreeding Analysis & COI Highlighting
Advanced coefficient of inbreeding (COI) analysis with visual highlighting:
- **Automatic common ancestor detection** across multiple generations
- **Visual color-coding** of inbred ancestors in pedigree matrix
- **Interactive tooltips** showing common ancestor frequency
- **Real-time COI calculations** for individual dogs
- **Multi-generation analysis** (configurable depth)
- **Smart highlighting system** with distinct colors for different common ancestors

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

### 🎨 User Interface Features
- **Responsive design** optimized for desktop and mobile devices
- **Interactive pedigree navigation** with hover effects and tooltips
- **Real-time search** and filtering capabilities
- **Modern, clean interface** following UX best practices
- **Accessibility features** for improved usability

## 🚀 How to Start the Project

### Prerequisites
- Python 3.8+
- MariaDB/MySQL server
- pip (Python package manager)

### Quick Start (Windows)

**Simplest way - Double-click one of these files:**
- `start.bat` - Regular startup (automatically handles venv)
- `start_dev.bat` - Development mode (auto-creates venv if needed)

**Or from command line:**
```cmd
start.bat
```

### Manual Setup (All Platforms)

#### 1. **Database Setup**
Create the database in MariaDB/MySQL:
```sql
CREATE DATABASE pedigree_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 2. **Configure Database Connection**
Edit `database.py` and update the DATABASE_URL:
```python
DATABASE_URL = "mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/pedigree_db"
```

#### 3. **Virtual Environment (Recommended)**
```bash
# Create venv
python -m venv venv

# Activate (Windows)
venv\Scripts\activate.bat

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 4. **Create Database Tables**
```bash
python create_database.py
```

#### 5. **Start Application**

**Option A: Use batch files (Windows only)**
```cmd
start.bat          # Simple startup
start_dev.bat      # Development mode with auto-setup
```

**Option B: Manual start (All platforms)**
```bash
python main.py
```

**Option C: Development with hot-reload**
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8007 --reload
```

### 🌐 Access Points
- **Main App**: http://127.0.0.1:8007
- **API Docs (Swagger)**: http://127.0.0.1:8007/docs
- **API Docs (ReDoc)**: http://127.0.0.1:8007/redoc
- **Health Check**: http://127.0.0.1:8007/health

### 📋 Startup Methods Comparison

| Method | Use Case | Auto venv | Auto deps | Platform |
|--------|----------|-----------|-----------|----------|
| `start.bat` | Quick start | ✅ | ❌ | Windows |
| `start_dev.bat` | Development | ✅ | ✅ | Windows |
| `python main.py` | Manual | ❌ | ❌ | All |
| uvicorn command | Development | ❌ | ❌ | All |

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

### Inbreeding Analysis System
The COI (Coefficient of Inbreeding) analysis provides advanced genealogical insights:

#### Common Ancestor Detection
```python
def detect_pedigree_inbreeding(dog, generations=4):
    """Detect common ancestors and calculate inbreeding patterns"""
    ancestor_paths = {}
    
    def traverse_pedigree(current_dog, path, level):
        if level > generations or not current_dog:
            return
            
        ancestor_id = current_dog.id
        if ancestor_id not in ancestor_paths:
            ancestor_paths[ancestor_id] = {'sire_paths': 0, 'dam_paths': 0}
            
        # Track path type (sire/dam lineage)
        path_type = 'sire_paths' if 's' in path else 'dam_paths'
        ancestor_paths[ancestor_id][path_type] += 1
```

#### Visual Highlighting System
```javascript
// Dynamic tooltip and color assignment
function updatePedigreeTable(data) {
    const inbreedingData = data.inbreeding_data || {};
    
    // Apply highlighting to common ancestors
    Object.keys(inbreedingData).forEach(ancestorId => {
        const inbredInfo = inbreedingData[ancestorId];
        const element = document.querySelector(`[data-dog-id="${ancestorId}"]`);
        
        if (element) {
            element.style.backgroundColor = inbredInfo.color;
            element.setAttribute('data-coi', inbredInfo.count);
            element.classList.add('common-ancestor');
        }
    });
}
```

#### API Integration
```python
@router.get("/api/dogs/{dog_id}/pedigree/{generations}")
async def get_dog_pedigree_api(dog_id: int, generations: int):
    """Enhanced API with inbreeding analysis"""
    
    # Detect inbreeding patterns
    inbreeding_data = detect_pedigree_inbreeding(pedigree_dog, generations)
    
    # Add COI data to ancestor matrix
    ancestor_matrix_with_coi = add_coi_data_to_matrix(ancestor_matrix, db)
    
    return {
        "dog": dog_dict,
        "ancestor_matrix": ancestor_matrix_with_coi,
        "inbreeding_data": inbreeding_data,  # Common ancestors with highlighting
        "pedigree_completeness": pedigree_completeness
    }
```
    
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
- **Inbreeding Detection**: Real-time common ancestor analysis
- **Visual Highlighting**: Color-coded pedigree display with interactive tooltips
- **COI Calculations**: Individual and pedigree-wide coefficient analysis

### Frontend Integration
The system provides seamless integration between backend analysis and frontend visualization:

```css
/* CSS for inbreeding highlighting */
.common-ancestor {
    border: 2px solid #333;
    position: relative;
}

.common-ancestor::after {
    content: "Common ancestor - appears " attr(data-coi) " times";
    position: absolute;
    background: rgba(0,0,0,0.8);
    color: white;
    padding: 5px;
    border-radius: 3px;
    top: -30px;
    left: 50%;
    transform: translateX(-50%);
    white-space: nowrap;
    z-index: 1000;
    opacity: 0;
    transition: opacity 0.3s;
}

.common-ancestor:hover::after {
    opacity: 1;
}
```

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
│   ├── dogs.py                # Dog-related API endpoints with COI analysis  
│   └── health.py              # Health test API endpoints
├── templates/
│   ├── dog_detail.html        # Dynamic pedigree matrix with COI highlighting
│   └── pedigree_horizontal.html # Static pedigree display
├── static/
│   ├── css/style.css          # Includes COI highlighting styles and tooltips
│   └── js/app.js              # Frontend JavaScript for dynamic interactions
├── crud.py                    # Database operations with recursive pedigree
├── utils.py                   # Helper functions including COI calculations
├── data_import/
│   └── importers/
│       └── estonia/           # Estonian Kennel Union data
└── coi_test.html              # Test page for COI functionality
```

### Key Files for COI System:
- **`utils.py`**: Contains `detect_pedigree_inbreeding()` and COI calculation functions
- **`routers/dogs.py`**: Enhanced API endpoints with inbreeding data
- **`templates/dog_detail.html`**: JavaScript for dynamic highlighting
- **`static/css/style.css`**: CSS for visual highlighting and tooltips

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

### Performance & Limitations

**COI Analysis Performance:**
- Supports up to **9 generations** of analysis
- Optimized for **real-time highlighting** in browser
- Typical analysis time: **<200ms** for 4-generation COI
- Database queries optimized with **recursive loading**

**System Limitations:**
- MariaDB JOIN limit (61 tables) overcome with recursive approach
- Memory usage increases exponentially with generation depth
- Recommended maximum: **6 generations** for complex pedigrees
- Large datasets may require query optimization

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

### COI Highlighting Testing

To test the inbreeding analysis and highlighting system:

1. **Access test dog**: Visit `http://localhost:8007/dogs/4888` (ALPHADIRATO EXACT COPY)
2. **Check API endpoint**: `http://localhost:8007/api/dogs/4888/pedigree/4`
3. **Verify highlighting**: Look for colored ancestors in pedigree matrix
4. **Test tooltips**: Hover over highlighted ancestors to see common ancestor information

**Expected behavior**:
- Common ancestors should be highlighted with distinct colors
- Tooltips should display "Common ancestor - appears X times"
- API should return `inbreeding_data` with 14+ common ancestors
- Different colors indicate different common ancestor lineages

## ❓ Frequently Asked Questions

**Q: How accurate are the COI calculations?**
A: The system detects common ancestors across the specified generation range and highlights them visually. For precise Wright's coefficient calculations, future versions will include mathematical COI percentages.

**Q: Why are some ancestors not highlighted?**
A: Only ancestors that appear multiple times in the pedigree (common ancestors) are highlighted. Unique ancestors don't contribute to inbreeding and remain unhighlighted.

**Q: Can I export pedigrees with COI data?**
A: PDF export functionality is planned for future development. Currently, visual analysis is available through the web interface.

**Q: How many generations should I analyze?**
A: For most breeding decisions, 4-5 generations provide sufficient COI analysis. Higher generation counts (6+) may impact performance with complex pedigrees.

## 📝 API Documentation

FastAPI provides automatic documentation at:
- **Swagger UI**: `http://localhost:8007/docs`
- **ReDoc**: `http://localhost:8007/redoc`

### Key API Endpoints

#### Pedigree API with COI Analysis
```
GET /api/dogs/{dog_id}/pedigree/{generations}
```
**Parameters:**
- `dog_id`: Integer - Dog identifier
- `generations`: Integer (1-9) - Number of generations to analyze

**Response includes:**
```json
{
  "dog": {...},
  "ancestor_matrix": {...},
  "inbreeding_data": {
    "4992": {
      "count": 2,
      "color": "#FFE6E6", 
      "color_index": 1,
      "sire_paths": 1,
      "dam_paths": 1
    }
  },
  "pedigree_completeness": {...}
}
```

#### Dog Management API
```
GET /api/dogs/              # List dogs with pagination
POST /api/dogs/             # Create new dog
GET /api/dogs/{dog_id}      # Get dog details
PUT /api/dogs/{dog_id}      # Update dog
DELETE /api/dogs/{dog_id}   # Delete dog
```

### API Usage Examples

**Test inbreeding analysis:**
```bash
curl http://localhost:8007/api/dogs/4888/pedigree/4
```

**Create new dog:**
```bash
curl -X POST "http://localhost:8007/api/dogs/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Dog", "sex": "Male", "breed": "DALMATIAN"}'
```

## ✅ Current Status (June 2025)

### ✅ Completed Features:
- **Dynamic Pedigree Matrix**: Fully functional 1-9 generation system
- **Binary Path Algorithm**: Mathematical ancestor positioning
- **Recursive Database Loading**: Overcomes JOIN limitations
- **Pre-computed Ancestor Matrix**: Efficient template rendering
- **COI Highlighting System**: Visual inbreeding analysis with tooltips
- **Common Ancestor Detection**: Multi-generation analysis across pedigree
- **Interactive User Interface**: Hover effects and real-time feedback
- **Estonian Data Import**: 2,240 dogs with complete pedigree data
- **Health Test Management**: Comprehensive health testing system
- **Clean Project Structure**: All temporary/debug files removed

### 🎯 Ready for Production:
The system is fully functional with:
- Dynamic pedigree matrix supporting all generation levels
- Advanced inbreeding analysis with visual highlighting
- Interactive tooltips showing common ancestor information
- Robust database operations optimized for large datasets
- Clean, maintainable codebase with proper documentation
- Comprehensive data import capabilities
- Mobile-responsive design with touch-friendly interface

### 🚀 Future Development:
- **Enhanced COI Analysis**: Wright's coefficient calculations and relationship matrices
- **Breeding Recommendations**: COI-based mate selection suggestions  
- **PDF Export**: Professional pedigree certificates with COI data
- **Multi-country Support**: Additional kennel club data import systems
- **Genetic Integration**: DNA test results correlation with pedigree analysis

## 🤝 Contributing

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

Development team focused on creating comprehensive pedigree management solutions for dog breeding communities.

---

*This system implements a fully dynamic pedigree matrix with advanced inbreeding analysis, overcoming traditional database limitations through innovative recursive loading and binary path algorithms. The COI highlighting system provides breeders with essential genetic information for making informed breeding decisions.*
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

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Cannot Start the Application

**Problem**: `start.bat` fails or shows "Python not found"
```
Solution: 
1. Install Python 3.8+ and ensure it's in your PATH
2. Try: python --version (should show Python version)
3. If not found, reinstall Python with "Add to PATH" option
```

**Problem**: Virtual environment activation fails
```
Solution:
1. Delete venv folder: rmdir /s venv
2. Recreate: python -m venv venv
3. Use start_dev.bat (auto-creates venv)
```

**Problem**: Database connection errors
```
Solution:
1. Check MariaDB/MySQL is running
2. Verify database exists: pedigree_db
3. Check credentials in database.py
4. Test connection: mysql -u root -p
```

#### Missing Dependencies

**Problem**: "ModuleNotFoundError" when starting
```
Solution:
1. Activate venv: venv\Scripts\activate.bat
2. Install deps: pip install -r requirements.txt
3. Or use start_dev.bat (auto-installs)
```

**Problem**: FastAPI or uvicorn not found
```
Solution:
pip install fastapi uvicorn[standard]
```

#### Port Issues

**Problem**: "Address already in use" on port 8007
```
Solution:
1. Find process: netstat -ano | findstr :8007
2. Kill process: taskkill /PID <process_id> /F
3. Or change port in main.py
```

#### Template/Static File Issues

**Problem**: CSS/JS files not loading or 404 errors
```
Solution:
1. Check file paths in main.py are relative: templates/, static/
2. Ensure you're in PedigreeDatabase directory when starting
3. Use start.bat (handles directory automatically)
```

#### Virtual Environment Issues

**Problem**: "(venv)" not showing in prompt
```
Solution:
1. Close terminal and reopen
2. Run: venv\Scripts\activate.bat
3. Check: echo %VIRTUAL_ENV%
```

**Problem**: Permission denied on venv activation (PowerShell)
```
Solution:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Performance Issues

**Problem**: Slow pedigree loading for large genealogies
```
Solution:
1. Reduce generation count in dropdown (start with 4-5)
2. Check database has proper indexes
3. Consider pagination for large datasets
```

### Development Issues

**Problem**: Hot-reload not working in development
```
Solution:
1. Use: python -m uvicorn main:app --reload
2. Or modify main.py to add reload=True
3. Ensure you're editing files in the correct directory
```

**Problem**: Database changes not reflected
```
Solution:
1. Delete: dalmatian_pedigree.db
2. Run: python create_database.py
3. Re-import data if needed
```

### Getting Help

If you encounter issues not covered here:
1. Check the Git repository issues section
2. Review the console output for error messages
3. Ensure all prerequisites are properly installed
4. Try the manual setup method if batch files fail

---

## 🧹 Project Cleanup (Latest)

### Repository Optimization
- **June 15, 2025**: Comprehensive cleanup of empty and duplicate files
- Removed 12 empty tracked files from Git repository
- Cleaned duplicate files from parent directory structure
- Enhanced inbreeding color visualization with distinct color palette
- Repository now contains only functional code (41 core files)

### Color System Improvements
- Fixed inbreeding level color conflicts in pedigree visualization
- Updated CSS with distinct colors for inbreeding levels 1-10
- Improved visual distinction between common ancestors
- Enhanced user experience for complex pedigree analysis

---

**For contributors:**
- Review the mobile/UX implementation summary before working on pedigree or UI features
- Test all changes for mobile compatibility and offline/online switching
- Follow the UI/UX standards in `CONTRIBUTING.md`

---
