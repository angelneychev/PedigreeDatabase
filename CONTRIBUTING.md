## 🚀 How to Start the Project

### Prerequisites
- Python 3.8+
- MariaDB/MySQL server
- Git
- pip (Python package manager)

### Complete Development Setup

Follow these detailed steps to set up the Dalmatian Pedigree Database for development:

#### 1. **Fork and Clone the Repository**
```bash
git clone https://github.com/yourusername/dalmatian-pedigree-database.git
cd dalmatian-pedigree-database
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

> **Critical**: Always activate the virtual environment before running, testing, or developing the project! You should see `(venv)` at the start of your terminal prompt.

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

#### 7. **Start the Development Server**
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8007 --reload
```

#### 8. **Access the Application**
Open your web browser and go to: `http://127.0.0.1:8007`

---

**For daily development:**
1. Navigate to project directory
2. Activate virtual environment (step 2 above)
3. Start the development server (step 7 above)

**To deactivate the virtual environment:**
```bash
deactivate
```

## 🏗️ Development Environment (venv)

Always use a Python virtual environment for development and testing. This ensures all dependencies are isolated and the project works the same on every machine.

**Create and activate venv (Windows PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Create and activate venv (Linux/macOS):**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

> Always activate the virtual environment before running, testing, or developing the project! You should see `(venv)` at the start of your terminal prompt.

---

## 🖥️ UI/UX Standards

- All new UI work must follow the current standard: **full-width layout**, dog info card integrated in the pedigree header, and generation selector in the header (numbers only, no text).
- AJAX-based pedigree updates (no page reloads, no URL parameters for generation)
- Mobile-first: test on mobile browsers, ensure touch targets and offline handling
- See `README.md` for screenshots and technical details

## 📱 Mobile/Storage Testing

- Test localStorage, sessionStorage, and cookie fallback for generation selection
- Use `/test_mobile_storage.html` and `/mobile_test.html` for device/browser validation
- All new features must be tested for mobile compatibility and offline/online switching

## 🧪 Mobile/UX Implementation & Testing

- See `README.md` for a summary of the mobile localStorage implementation, test results, and production readiness.
- All contributors must review the latest implementation notes before working on pedigree or UI features.
# Contributing to Dalmatian Pedigree Database

Thank you for your interest in contributing to the Dalmatian Pedigree Database project! This document provides guidelines for contributing to the project.

## 🛠️ Getting Started for Contributors

# Contributing to Dalmatian Pedigree Database

Thank you for your interest in contributing to the Dalmatian Pedigree Database project! This document provides guidelines for contributing to the project.

## 🛠️ Getting Started for Contributors

### Prerequisites for Development
- Python 3.8+
- MariaDB/MySQL server
- Git
- Code editor (VS Code recommended)
- Basic knowledge of FastAPI, SQLAlchemy, HTML/CSS

### Quick Setup for Development
1. **Fork and clone** the repository
2. **Follow setup instructions** in README.md to get the project running
3. **Create development branch**: `git checkout -b feature/your-feature-name`

### Development Workflow
1. Follow the complete setup instructions above
2. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes and test thoroughly
4. Commit with clear messages
5. Push to your fork and create a Pull Request

## 🛠️ Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and single-purpose

### Commit Messages
- Use clear, descriptive commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Include relevant details about what changed and why

### Pull Request Process
1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Test your changes thoroughly
4. Commit your changes with clear messages
5. Push to your fork
6. Create a Pull Request with:
   - Clear title and description
   - Reference any related issues
   - Include screenshots for UI changes

## 🧬 Core Features

### Dynamic Pedigree Matrix
The core feature uses a binary path algorithm for ancestor positioning. When working on pedigree-related features:
- Understand the recursive database loading approach
- Test with multiple generation levels (1-9)
- Ensure matrix structure remains consistent

### Inbreeding Analysis & COI System
The COI (Coefficient of Inbreeding) highlighting system provides visual analysis of common ancestors:

#### Key Components:
- **Backend**: `detect_pedigree_inbreeding()` in `utils.py` - detects common ancestors
- **API**: Enhanced pedigree endpoint returns `inbreeding_data` with highlighting info
- **Frontend**: JavaScript processes inbreeding data and applies visual highlighting
- **CSS**: Tooltip system shows common ancestor frequency on hover

#### Testing COI Features:
```bash
# Test API endpoint
curl http://localhost:8007/api/dogs/{Id}}/pedigree/4

# Expected response includes:
# "inbreeding_data": {
#   "4992": {"count": 2, "color": "#FFE6E6", "color_index": 1},
#   "4987": {"count": 2, "color": "#E6F3FF", "color_index": 2}
# }
```

#### Development Guidelines for COI:
- Always test with dogs that have known inbreeding (e.g., dog ID 4888)
- Verify both API response structure and frontend highlighting
- Ensure tooltips display correctly on hover
- Test across different generation levels (3-6 generations recommended)
- Colors should be distinct and accessible

### Data Import System
When adding new data sources:
- Create a new folder in `data_import/importers/[country]/`
- Follow the existing Estonian import structure
- Include proper validation and logging
- Document the data format in README
- **⚠️ Important**: Place data files in `data/` directory - they are excluded from Git
- Data files are too large for GitHub and should be stored locally only

## 🧪 Testing

### Before submitting
- Test the pedigree matrix with different generation levels
- Verify data import functionality
- Check responsive design on different screen sizes
- Test database operations
- **Test COI highlighting**: Verify common ancestors are highlighted with correct tooltips
- **Test API endpoints**: Ensure inbreeding data is returned correctly

### Manual testing
- Create test dogs with known pedigree relationships
- Verify parent-child relationships display correctly
- Test health test recording and display
- **Test inbreeding detection**: Use dog ID 4888 which has known common ancestors
- **Verify tooltips**: Hover over highlighted ancestors to confirm tooltip content

## 📋 Areas for Contribution

### High Priority
- Additional country data importers (Germany, France, USA, etc.)
- User authentication system
- Advanced COI analysis features (Wright's coefficient, relationship calculations)

### Medium Priority
- Advanced search filters with COI-based sorting
- Photo gallery integration
- Genetic test tracking and integration with COI analysis
- Mobile app development
- Breeding recommendation system based on COI analysis

### Recently Completed ✅
- **COI Highlighting System**: Visual inbreeding analysis with tooltips
- **Common Ancestor Detection**: Multi-generation analysis across pedigree
- **Interactive Pedigree Matrix**: Real-time highlighting and hover effects

### Documentation
- API documentation improvements
- User guides
- Installation tutorials
- Video demonstrations

## 🐛 Bug Reports

When reporting bugs:
1. Check existing issues first
2. Provide clear reproduction steps
3. Include system information (OS, Python version, etc.)
4. Add screenshots for UI bugs
5. Describe expected vs actual behavior

## 💡 Feature Requests

For new features:
1. Search existing issues and discussions
2. Describe the use case and benefits
3. Consider implementation complexity
4. Provide mockups for UI features

## 🔧 Troubleshooting

### Common Issues

**COI Highlighting Not Working:**
```bash
# Check API response
curl http://localhost:8007/api/dogs/{Id}}/pedigree/4

# Expected: inbreeding_data should contain entries
# If empty, check utils.py detect_pedigree_inbreeding function
```

**Database Connection Issues:**
```bash
# Verify database is running
mysql -u root -p

# Check database.py configuration
# Ensure DATABASE_URL matches your setup
```

**Virtual Environment Issues:**
```powershell
# Windows: Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# You should see (venv) in your prompt
```

**API Endpoints Not Working:**
```bash
# Restart development server
python -m uvicorn main:app --host 127.0.0.1 --port 8007 --reload

# Check server logs for errors
```

### Performance Issues

**Slow COI Analysis:**
- Reduce generation depth (try 4 instead of 6+)
- Check database indexes on parent relationships
- Monitor memory usage with large pedigrees

**Database Query Optimization:**
- Ensure proper indexes on `sire_id` and `dam_id` columns
- Use EXPLAIN on slow queries
- Consider query result caching for frequently accessed pedigrees

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Jinja2 Templates](https://jinja.palletsprojects.com/)
- [Bootstrap CSS Framework](https://getbootstrap.com/)

## 🤝 Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain a welcoming environment

## 📞 Contact

For questions or discussions:
- Open an issue for technical questions
- Use discussions for general questions
- Contact maintainers for sensitive issues

Thank you for contributing to the Dalmatian Pedigree Database! 🐕
