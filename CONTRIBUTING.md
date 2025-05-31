# Contributing to Dalmatian Pedigree Database

Thank you for your interest in contributing to the Dalmatian Pedigree Database project! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- MariaDB/MySQL server
- Git

### Setting up the development environment
1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/dalmatian-pedigree-database.git
   cd dalmatian-pedigree-database
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up the database and run the application (see README.md)

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

### Manual testing
- Create test dogs with known pedigree relationships
- Verify parent-child relationships display correctly
- Test health test recording and display

## 📋 Areas for Contribution

### High Priority
- Additional country data importers (Germany, France, USA, etc.)
- Inbreeding coefficient calculations
- PDF export functionality
- User authentication system

### Medium Priority
- Advanced search filters
- Photo gallery integration
- Genetic test tracking
- Mobile app development

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
