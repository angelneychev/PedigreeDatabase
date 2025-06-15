# Quick Start Guide

## 🚀 Getting Started in 30 seconds

### Windows Users (Simplest)
1. **Double-click** `start_dev.bat` 
   - Auto-creates venv if needed
   - Auto-installs dependencies  
   - Starts development server

2. **Or double-click** `start.bat`
   - Uses existing venv (if available)
   - Quick startup

3. **Open browser**: http://127.0.0.1:8007

---

## ⚡ What Each File Does

| File | Purpose | Auto Setup | When to Use |
|------|---------|------------|-------------|
| `start_dev.bat` | Development mode | ✅ Full auto | First time, development |
| `start.bat` | Regular startup | ❌ Manual setup | Daily use, production |

---

## 🔧 Manual Setup (if batch files don't work)

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it (Windows)
venv\Scripts\activate.bat

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup database (one time only)
python create_database.py

# 5. Start application
python main.py
```

---

## 🌐 Access Points

- **Main App**: http://127.0.0.1:8007
- **API Docs**: http://127.0.0.1:8007/docs
- **Health Check**: http://127.0.0.1:8007/health

---

## ❓ Problems?

1. **Python not found**: Install Python 3.8+ with "Add to PATH"
2. **Database errors**: Setup MariaDB/MySQL first
3. **Permission errors**: Run as Administrator
4. **Port busy**: Change port in `main.py` or kill process

See `README.md` for detailed troubleshooting.
