# 📦 BlueScope Installation Guide

Complete installation instructions for BlueScope on all supported platforms.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Windows Installation](#windows-installation)
3. [Linux Installation](#linux-installation)
4. [macOS Installation](#macos-installation)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## 🖥️ System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 11+
- **Python**: 3.11 or higher (3.14 recommended)
- **RAM**: 4GB
- **Disk Space**: 100MB for application + 500MB for dependencies
- **Display**: 1280x720 minimum resolution

### Recommended Requirements
- **OS**: Windows 11
- **Python**: 3.14
- **RAM**: 8GB
- **Disk Space**: 1GB
- **Display**: 1920x1080 or higher

---

## 🪟 Windows Installation

### Method 1: Quick Install (Recommended)

1. **Download BlueScope**
   ```bash
   git clone https://github.com/yourusername/bluescope.git
   cd bluescope
   ```

2. **Run Installer**
   ```bash
   # Double-click one of these:
   LAUNCH.bat           # Simplest - auto-installs everything
   start-simple.bat     # Full installer with progress
   ```

3. **Done!** The application will launch automatically.

### Method 2: Manual Installation

1. **Install Python**
   - Download from [python.org](https://www.python.org/downloads/)
   - ✅ Check "Add Python to PATH" during installation
   - Verify: `python --version` (should show 3.11+)

2. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/bluescope.git
   cd bluescope
   ```

3. **Create Virtual Environment**
   ```bash
   python -m venv venv
   ```

4. **Activate Virtual Environment**
   ```bash
   venv\Scripts\activate
   ```

5. **Install Dependencies**
   
   **Option A: Minimal Install (Quick Start)**
   ```bash
   pip install -r requirements-minimal.txt
   ```
   
   **Option B: Full Install (All Features)**
   ```bash
   pip install -r requirements.txt
   ```

6. **Launch Application**
   ```bash
   python main.py
   ```

---

## 🐧 Linux Installation

### Ubuntu/Debian

1. **Install Python and Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3-pip git
   ```

2. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/bluescope.git
   cd bluescope
   ```

3. **Create Virtual Environment**
   ```bash
   python3.11 -m venv venv
   ```

4. **Activate Virtual Environment**
   ```bash
   source venv/bin/activate
   ```

5. **Install Dependencies**
   ```bash
   # Minimal install
   pip install -r requirements-minimal.txt
   
   # OR full install
   pip install -r requirements.txt
   ```

6. **Launch Application**
   ```bash
   python main.py
   ```

### Fedora/RHEL

1. **Install Python**
   ```bash
   sudo dnf install python3.11 python3-pip git
   ```

2. **Follow steps 2-6 from Ubuntu instructions above**

---

## 🍎 macOS Installation

### Using Homebrew (Recommended)

1. **Install Homebrew** (if not installed)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python**
   ```bash
   brew install python@3.11
   ```

3. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/bluescope.git
   cd bluescope
   ```

4. **Create Virtual Environment**
   ```bash
   python3.11 -m venv venv
   ```

5. **Activate Virtual Environment**
   ```bash
   source venv/bin/activate
   ```

6. **Install Dependencies**
   ```bash
   # Minimal install
   pip install -r requirements-minimal.txt
   
   # OR full install
   pip install -r requirements.txt
   ```

7. **Launch Application**
   ```bash
   python main.py
   ```

---

## ✅ Verification

### Run Verification Script

```bash
python verify_installation.py
```

### Expected Output

```
============================================================
BlueScope Installation Verification
============================================================
🐍 Checking Python version...
   ✅ Python 3.14.0

📦 Checking core dependencies...
   ✅ PyQt6 (6.10.1)
   ✅ NumPy (2.4.0)
   ✅ python-dotenv (1.2.1)
   ✅ PyYAML (6.0.3)

🤖 Checking ML dependencies (optional)...
   ✅ scikit-learn (1.8.0)
   ✅ PyTorch (2.9.1)
   ✅ scipy (1.16.3)

📁 Checking project structure...
   ✅ main.py
   ✅ frontend/ui/main_window.py
   ✅ analytics/behavior_engine/main.py
   ✅ config/settings.yaml

🔍 Checking module imports...
   ✅ frontend.ui.main_window
   ✅ analytics.behavior_engine.main
   ✅ analytics.anomaly_engine.main

============================================================
Verification Summary
============================================================
Python Version.......................... ✅ PASS
Core Dependencies....................... ✅ PASS
ML Dependencies......................... ✅ PASS
Project Structure....................... ✅ PASS
Module Imports.......................... ✅ PASS
============================================================

🎉 All checks passed! BlueScope is ready to use.
```

### Manual Verification

1. **Check Python Version**
   ```bash
   python --version
   # Should show: Python 3.11.0 or higher
   ```

2. **Check Installed Packages**
   ```bash
   pip list
   # Should include: PyQt6, numpy, python-dotenv, PyYAML
   ```

3. **Test Import**
   ```bash
   python -c "from PyQt6.QtWidgets import QApplication; print('PyQt6 OK')"
   # Should print: PyQt6 OK
   ```

4. **Launch Application**
   ```bash
   python main.py
   # GUI should appear
   ```

---

## 🔧 Troubleshooting

### Common Issues

#### Issue 1: "Python not found"

**Windows:**
```bash
# Add Python to PATH manually
# 1. Search "Environment Variables" in Windows
# 2. Edit "Path" variable
# 3. Add: C:\Users\YourName\AppData\Local\Programs\Python\Python311
```

**Linux/Mac:**
```bash
# Use full path
/usr/bin/python3.11 -m venv venv
```

#### Issue 2: "pip: command not found"

```bash
# Windows
python -m pip install --upgrade pip

# Linux/Mac
python3.11 -m pip install --upgrade pip
```

#### Issue 3: "Failed to create virtual environment"

```bash
# Install venv module
# Ubuntu/Debian
sudo apt install python3.11-venv

# Then retry
python3.11 -m venv venv
```

#### Issue 4: "ImportError: No module named 'PyQt6'"

```bash
# Activate venv first
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Then install
pip install PyQt6
```

#### Issue 5: "Permission denied" (Linux/Mac)

```bash
# Don't use sudo with pip in venv
# Instead, ensure venv is activated:
source venv/bin/activate
pip install -r requirements-minimal.txt
```

#### Issue 6: GUI doesn't appear

**Check display:**
```bash
# Linux - ensure X11 is running
echo $DISPLAY
# Should show: :0 or similar

# If empty, set it:
export DISPLAY=:0
```

**Check PyQt6:**
```bash
python -c "from PyQt6.QtWidgets import QApplication; print('OK')"
```

#### Issue 7: Slow installation

```bash
# Use faster mirror
pip install -r requirements-minimal.txt -i https://pypi.org/simple

# Or install without cache
pip install --no-cache-dir -r requirements-minimal.txt
```

---

## 🚀 Post-Installation

### Optional: Install ML Features

If you installed minimal version and want ML features:

```bash
# Activate venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install ML packages
pip install scikit-learn torch scipy
```

### Optional: Create Desktop Shortcut

**Windows:**
1. Right-click `LAUNCH.bat`
2. Select "Create shortcut"
3. Move shortcut to Desktop
4. Rename to "BlueScope"

**Linux:**
Create `~/.local/share/applications/bluescope.desktop`:
```ini
[Desktop Entry]
Name=BlueScope
Exec=/path/to/bluescope/venv/bin/python /path/to/bluescope/main.py
Icon=/path/to/bluescope/icon.png
Type=Application
Categories=Development;
```

**macOS:**
Create an Automator application that runs:
```bash
cd /path/to/bluescope && source venv/bin/activate && python main.py
```

---

## 📚 Next Steps

After installation:

1. **Read the Quick Start**: See `QUICKSTART.md`
2. **Configure Settings**: Edit `config/settings.yaml`
3. **Launch Application**: Run `python main.py` or use batch files
4. **Explore Features**: Check out all 5 tabs in the GUI

---

## 💡 Tips

### Tip 1: Keep Python Updated
```bash
# Check for updates regularly
python --version
```

### Tip 2: Update Dependencies
```bash
pip install --upgrade -r requirements-minimal.txt
```

### Tip 3: Use Virtual Environment
Always activate the virtual environment before running BlueScope:
```bash
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### Tip 4: Check Logs
If something goes wrong, check:
```bash
logs/bluescope.log
```

---

## 📞 Getting Help

- **Documentation**: See `README.md`
- **Issues**: [GitHub Issues](https://github.com/yourusername/bluescope/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/bluescope/discussions)

---

**Installation complete! Enjoy using BlueScope! 🔵**
