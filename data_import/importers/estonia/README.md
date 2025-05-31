# Estonian Kennel Union Data Import

This directory contains the import system for Estonian Kennel Union data.

## 📁 Directory Structure

```
estonia/
├── estonia_import.py     # Import script for Estonian data
├── data/                 # Place JSON data files here
│   ├── .gitkeep         # Preserves directory structure
│   └── *.json           # Data files (ignored by Git)
├── logs/                 # Import logs (ignored by Git)
│   └── .gitkeep         # Preserves directory structure
└── README.md            # This file
```

## 📥 Data File Placement

1. **Download data** from Estonian Kennel Union
2. **Place JSON files** in the `data/` directory
3. **Example filename**: `dalmatian_dogs_estonia_27052025.json`
4. **Run import**: `python estonia_import.py`

## ⚠️ Important Notes

- **Data files are excluded from Git** (too large for GitHub)
- **Directory structure is preserved** with .gitkeep files
- **Logs are automatically generated** during import
- **Only code and documentation** are tracked in version control

## 🚀 Usage

```bash
# Navigate to estonia directory
cd data_import/importers/estonia

# Place your data file in data/ directory
# data/dalmatian_dogs_estonia_DDMMYYYY.json

# Run the import
python estonia_import.py
```

## 📊 Expected Results

- Import statistics logged to console
- Detailed logs saved to `logs/` directory
- Data imported to main database
- Parent relationships established