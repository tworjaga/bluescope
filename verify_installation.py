#!/usr/bin/env python3
"""
BlueScope Installation Verification Script
Checks all dependencies and components
"""

import sys
import importlib
from pathlib import Path

def check_python_version():
    """Check Python version"""
    print(" Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print(f"    Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"    Python {version.major}.{version.minor}.{version.micro} (requires 3.11+)")
        return False

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"    {package_name} ({version})")
        return True
    except ImportError:
        print(f"    {package_name} - NOT INSTALLED")
        return False

def check_core_dependencies():
    """Check core dependencies"""
    print("\n Checking core dependencies...")
    packages = [
        ('PyQt6', 'PyQt6'),
        ('NumPy', 'numpy'),
        ('python-dotenv', 'dotenv'),
        ('PyYAML', 'yaml'),
    ]
    
    results = []
    for pkg_name, import_name in packages:
        results.append(check_package(pkg_name, import_name))
    
    return all(results)

def check_ml_dependencies():
    """Check ML dependencies"""
    print("\n Checking ML dependencies (optional)...")
    packages = [
        ('scikit-learn', 'sklearn'),
        ('PyTorch', 'torch'),
        ('scipy', 'scipy'),
    ]
    
    results = []
    for pkg_name, import_name in packages:
        results.append(check_package(pkg_name, import_name))
    
    return all(results)

def check_project_structure():
    """Check project structure"""
    print("\n Checking project structure...")
    
    required_paths = [
        'main.py',
        'frontend/ui/main_window.py',
        'frontend/ui/device_table.py',
        'frontend/ui/packet_table.py',
        'frontend/ui/statistics_panel.py',
        'frontend/ui/graphs.py',
        'frontend/ui/anomaly_panel.py',
        'frontend/themes/dark_theme.py',
        'analytics/behavior_engine/main.py',
        'analytics/anomaly_engine/main.py',
        'config/settings.yaml',
        'requirements.txt',
        'requirements-minimal.txt',
    ]
    
    all_exist = True
    for path in required_paths:
        file_path = Path(path)
        if file_path.exists():
            print(f"    {path}")
        else:
            print(f"    {path} - MISSING")
            all_exist = False
    
    return all_exist

def check_imports():
    """Check if main modules can be imported"""
    print("\n Checking module imports...")
    
    modules = [
        'frontend.ui.main_window',
        'frontend.ui.device_table',
        'frontend.ui.packet_table',
        'frontend.ui.statistics_panel',
        'frontend.ui.graphs',
        'frontend.ui.anomaly_panel',
        'frontend.themes.dark_theme',
        'analytics.behavior_engine.main',
        'analytics.anomaly_engine.main',
    ]
    
    all_imported = True
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"    {module}")
        except Exception as e:
            print(f"    {module} - ERROR: {e}")
            all_imported = False
    
    return all_imported

def main():
    """Main verification function"""
    print("=" * 60)
    print("BlueScope Installation Verification")
    print("=" * 60)
    
    results = {
        'Python Version': check_python_version(),
        'Core Dependencies': check_core_dependencies(),
        'ML Dependencies': check_ml_dependencies(),
        'Project Structure': check_project_structure(),
        'Module Imports': check_imports(),
    }
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    for check, passed in results.items():
        status = " PASS" if passed else " FAIL"
        print(f"{check:.<40} {status}")
    
    print("=" * 60)
    
    if all(results.values()):
        print("\n All checks passed! BlueScope is ready to use.")
        print("\nTo start BlueScope:")
        print("  1. Double-click: start-simple.bat")
        print("  2. Or run: python main.py")
        return 0
    else:
        print("\n  Some checks failed. Please install missing dependencies:")
        if not results['Core Dependencies']:
            print("  pip install -r requirements-minimal.txt")
        if not results['ML Dependencies']:
            print("  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
