#!/usr/bin/env python3
"""
GTPlanner Environment Check Script
"""

import sys
import os
import importlib
from pathlib import Path

def main():
    print("=" * 60)
    print("GTPlanner Environment Check")
    print("=" * 60)
    
    all_ok = True
    
    # Check Python version
    print("\n[1/5] Python Version")
    version = sys.version_info
    print(f"  Current: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("  [X] Requires Python >= 3.10")
        all_ok = False
    elif version.minor < 11:
        print("  [!] Below 3.11 (upgrade recommended)")
    else:
        print("  [OK] Version OK")
    
    # Check dependencies
    print("\n[2/5] Dependencies")
    required = [
        ('openai', 'OpenAI'),
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('rich', 'Rich'),
        ('pocketflow', 'PocketFlow'),
        ('dynaconf', 'Dynaconf'),
        ('aiohttp', 'AIOHTTP'),
    ]
    
    missing = []
    for package, name in required:
        try:
            importlib.import_module(package)
            print(f"  [OK] {name}")
        except ImportError:
            print(f"  [X] {name} - not installed")
            missing.append(package)
            all_ok = False
    
    if missing:
        print(f"\n  Install: pip install {' '.join(missing)}")
    
    # Check environment variables
    print("\n[3/5] Environment Variables")
    required_vars = ['LLM_API_KEY', 'LLM_BASE_URL', 'LLM_MODEL']
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            masked = value[:10] + '...' if len(value) > 10 else value
            print(f"  [OK] {var}: {masked}")
        else:
            print(f"  [X] {var}: not set")
            all_ok = False
    
    # Check project structure
    print("\n[4/5] Project Structure")
    required_files = [
        'fastapi_main.py',
        'gtplanner.py',
        'agent/stateless_planner.py',
        'static/test_chat.html',
    ]
    
    for file in required_files:
        if Path(file).exists():
            print(f"  [OK] {file}")
        else:
            print(f"  [X] {file} - missing")
            all_ok = False
    
    # Check settings
    print("\n[5/5] Configuration")
    if Path('settings.toml').exists():
        print("  [OK] settings.toml exists")
    else:
        print("  [!] settings.toml missing")
    
    # Summary
    print("\n" + "=" * 60)
    if all_ok:
        print("Result: [OK] Environment check passed!")
        print("\nStart with:")
        print("  CLI: python gtplanner.py")
        print("  API: python fastapi_main.py")
        return 0
    else:
        print("Result: [X] Please fix the issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main())

