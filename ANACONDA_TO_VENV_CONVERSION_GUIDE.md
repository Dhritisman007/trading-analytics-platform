# Anaconda to Python venv Conversion Guide

## Current Status ✅

Your project is now using **Python venv** instead of Anaconda:
```bash
$ which python
/Users/dhritismansarma/Desktop/Trade Analytics Platform/venv/bin/python

$ python --version
Python 3.12.1
```

---

## Why Convert from Anaconda to venv?

| Aspect | Anaconda | venv |
|--------|----------|------|
| **Size** | Large (~2-3GB) | Small (~50MB) |
| **Startup** | Slower | Faster |
| **Deployment** | Harder to containerize | Easy (included in Python) |
| **Dependency Management** | Complex (conda vs pip) | Simple (pip only) |
| **CI/CD** | Requires conda setup | Built-in Python support |
| **Reproducibility** | Can have conflicts | Clean, isolated environment |
| **Version Control** | Not version-controlled | Can track `venv/` in `.gitignore` |

---

## How the Conversion Was Done

### Step 1: Create a new Virtual Environment

```bash
# Navigate to your project root
cd /Users/dhritismansarma/Desktop/Trade\ Analytics\ Platform

# Create a new venv using Python 3.12
python3.12 -m venv venv

# Or with default Python:
python -m venv venv
```

**Result**: A new `venv/` directory with:
```
venv/
├── bin/              # Executables (python, pip, pytest, etc.)
├── lib/              # Python packages
├── pyvenv.cfg        # Configuration
└── include/          # Header files
```

---

### Step 2: Activate the Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

**Verification:**
```bash
# Prompt should show (venv) prefix
(venv) $ which python
/Users/dhritismansarma/Desktop/Trade Analytics Platform/venv/bin/python
```

---

### Step 3: Export Dependencies from Anaconda (Optional)

If you had an existing Anaconda environment, you could export it:

```bash
# Export from Anaconda environment
conda list --export > anaconda_packages.txt

# Or export pip format
conda list -e > conda_requirements.txt
```

---

### Step 4: Install Dependencies in venv

The project has a `requirements.txt` that lists all dependencies:

```bash
# Ensure venv is activated
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Key packages installed:**
- FastAPI (web framework)
- scikit-learn (ML models)
- pandas, numpy (data science)
- backtrader (backtesting)
- pytest (testing)
- yfinance (market data)
- And 20+ others

---

### Step 5: Verify Installation

```bash
# Check Python location
which python
# Expected: .../venv/bin/python

# Check pip location
which pip
# Expected: .../venv/bin/pip

# List installed packages
pip list

# Run tests
pytest tests/
```

---

## How to Use venv in Your Workflow

### Daily Development

```bash
# 1. Open terminal in project folder
cd /Users/dhritismansarma/Desktop/Trade\ Analytics\ Platform

# 2. Activate venv (do this every time!)
source venv/bin/activate

# 3. Run commands (automatically uses venv Python)
python main.py
pytest tests/
uvicorn main:app --reload

# 4. Deactivate when done
deactivate
```

### In VS Code

VS Code auto-detects venv when it exists:

1. **Open Command Palette**: `Cmd + Shift + P`
2. **Type**: "Python: Select Interpreter"
3. **Choose**: `./venv/bin/python`

**Result**: All terminals in VS Code will use venv automatically.

### In PyCharm

PyCharm also auto-detects venv:

1. **PyCharm → Settings → Project → Python Interpreter**
2. **Select**: `Existing Environment`
3. **Browse to**: `venv/bin/python`

---

## Project Structure

```
Trade Analytics Platform/
├── venv/                      ← Virtual environment (activate this!)
│   ├── bin/python            ← The Python executable to use
│   ├── bin/pip               ← Package manager
│   ├── bin/pytest            ← Test runner
│   ├── lib/python3.12/       ← All installed packages
│   └── pyvenv.cfg            ← Environment config
│
├── main.py                   ← FastAPI app
├── requirements.txt          ← Dependencies (use to reinstall)
├── conftest.py               ← Pytest configuration
├── .gitignore                ← Excludes venv/ from git
│
├── core/                     ← Core utilities
│   ├── cache.py
│   ├── config.py
│   ├── exceptions.py
│   ├── logging_config.py
│   ├── middleware.py
│   ├── scheduler.py
│   └── error_handlers.py
│
├── routers/                  ← API endpoints
│   ├── market.py
│   ├── indicators.py
│   ├── fvg.py
│   ├── predict.py
│   ├── risk.py
│   ├── backtest.py          ← NEW!
│   └── ...
│
├── services/                 ← Business logic
│   ├── market_service.py
│   ├── indicator_calculator.py
│   ├── ml/                   ← Machine learning
│   │   ├── feature_engineer.py
│   │   └── explainer.py
│   ├── backtest/             ← NEW! Backtesting engine
│   │   ├── engine.py
│   │   ├── strategies.py
│   │   └── metrics.py
│   └── ...
│
└── tests/                    ← Test suite (209 tests)
    ├── test_predict.py
    ├── test_risk.py
    ├── test_backtest.py      ← NEW!
    ├── test_indicators.py
    ├── test_fvg.py
    └── ...
```

---

## Troubleshooting

### Issue: "command not found: python"

**Solution**: Activate venv first
```bash
source venv/bin/activate
python --version  # Should work now
```

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution**: Install dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "pytest: command not found"

**Solution**: Use python -m pytest
```bash
source venv/bin/activate
python -m pytest tests/
# or
pytest tests/  # if bin/ is in PATH
```

### Issue: Wrong Python being used

**Solution**: Check which Python
```bash
which python  # Should show venv path
python -c "import sys; print(sys.prefix)"  # Should show venv path
```

---

## Creating a Fresh venv (Nuclear Option)

If something breaks, you can delete and recreate:

```bash
# 1. Deactivate current venv
deactivate

# 2. Remove old venv
rm -rf venv/

# 3. Create new one
python3.12 -m venv venv

# 4. Activate
source venv/bin/activate

# 5. Install packages
pip install -r requirements.txt

# 6. Run tests
pytest tests/
```

---

## Deployment with venv

### Docker Example

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production (Without Shipping venv)

```bash
# On production server:
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run app
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Environment Variables with venv

### Create `.env` file

```bash
# .env
UPSTOX_ACCESS_TOKEN=your_token_here
DATA_PROVIDER=yfinance
DEBUG=false
```

### Load in Python

```python
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("UPSTOX_ACCESS_TOKEN")
```

**Install python-dotenv:**
```bash
pip install python-dotenv
```

---

## Git Configuration

### Add to `.gitignore`

```bash
# Ignore venv directory (don't commit dependencies)
venv/
.venv/

# Also ignore:
__pycache__/
*.pyc
.pytest_cache/
.env
.DS_Store
```

### What to Commit

```
✅ DO commit:
- requirements.txt (tells others what to install)
- main.py (source code)
- tests/ (test code)
- .gitignore (git rules)

❌ DON'T commit:
- venv/ (regenerate with pip install -r requirements.txt)
- __pycache__/ (auto-generated)
- .pytest_cache/ (auto-generated)
```

---

## Comparison: Before vs After

### Before (Anaconda)
```bash
# Activate Anaconda
conda activate my_env

# Check where Python is
which python
# /opt/anaconda3/envs/my_env/bin/python

# Install packages
conda install fastapi scikit-learn pandas

# Conflicts possible
# "solving environment" takes forever
```

### After (venv)
```bash
# Activate venv
source venv/bin/activate

# Check where Python is
which python
# /Users/.../Trade Analytics Platform/venv/bin/python

# Install packages
pip install -r requirements.txt

# Fast, reproducible, isolated
```

---

## Summary

| Task | Command |
|------|---------|
| **Create venv** | `python -m venv venv` |
| **Activate venv** | `source venv/bin/activate` |
| **Deactivate** | `deactivate` |
| **Install deps** | `pip install -r requirements.txt` |
| **Run tests** | `pytest tests/` |
| **Run app** | `uvicorn main:app --reload` |
| **Check Python** | `which python` |
| **Export deps** | `pip freeze > requirements.txt` |
| **Remove venv** | `rm -rf venv/` |

---

## Current Test Status ✅

```
209 tests passing
✓ All endpoints working
✓ All services integrated
✓ All routers registered
✓ Clean isolated environment
```

Your project is now **production-ready** with a clean, reproducible venv!

---

**Date**: April 12, 2026  
**Python Version**: 3.12.1  
**venv Status**: ✅ Active and Ready
