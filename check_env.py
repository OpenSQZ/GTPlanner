#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GTPlanner Environment Check Script
Check Python version, dependencies and configuration
"""

import sys
import os
import importlib
from pathlib import Path

# Fix console encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def check_python_version():
    """Check Python version"""
    print("\n[1/5] Checking Python version...")
    version = sys.version_info
    
    print(f"  Current version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("  [X] Python version too low, requires >= 3.10")
        return False
    elif version.minor < 11:
        print("  [!] Python version below 3.11, may have issues, upgrade recommended")
        return True
    else:
        print("  [OK] Python version meets requirements (>= 3.11)")
        return True

def check_dependencies():
    """Check required dependencies"""
    print("\n[2/5] Checking dependencies...")
    
    required_packages = [
        ('openai', 'OpenAI'),
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('rich', 'Rich'),
        ('pocketflow', 'PocketFlow'),
        ('dynaconf', 'Dynaconf'),
        ('aiohttp', 'AIOHTTP'),
        ('pydantic', 'Pydantic'),
    ]
    
    missing = []
    installed = []
    
    for package, name in required_packages:
        try:
            importlib.import_module(package)
            print(f"  [OK] {name}")
            installed.append(package)
        except ImportError:
            print(f"  [X] {name} - not installed")
            missing.append(package)
    
    if missing:
        print(f"\n  [!] Missing {len(missing)} packages")
        print("  Install command: pip install " + " ".join(missing))
        return False
    
    print("  [OK] All dependencies installed")
    return True

def check_environment_variables():
    """检查环境变量"""
    print("\n[3/5] 检查环境变量...")
    
    required_vars = ['LLM_API_KEY', 'LLM_BASE_URL', 'LLM_MODEL']
    optional_vars = ['JINA_API_KEY', 'LANGFUSE_SECRET_KEY', 'LANGFUSE_PUBLIC_KEY']
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            masked = value[:8] + '...' if len(value) > 8 else value
            print(f"  ✅ {var}: {masked}")
        else:
            print(f"  ❌ {var}: 未设置")
            missing_required.append(var)
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            masked = value[:8] + '...' if len(value) > 8 else value
            print(f"  ✓ {var}: {masked}")
        else:
            print(f"  ○ {var}: 未设置（可选）")
            missing_optional.append(var)
    
    if missing_required:
        print("\n  ⚠️  需要设置以下环境变量:")
        for var in missing_required:
            print(f"    {var}")
        print("\n  设置方法:")
        print("    Windows PowerShell:")
        print(f"      $env:{missing_required[0]}=\"your-key\"")
        print("    Linux/Mac:")
        print(f"      export {missing_required[0]}=\"your-key\"")
        return False
    
    print("  ✅ 必需环境变量已配置")
    return True

def check_project_structure():
    """检查项目结构"""
    print("\n[4/5] 检查项目结构...")
    
    required_files = [
        'fastapi_main.py',
        'gtplanner.py',
        'agent/stateless_planner.py',
        'static/test_chat.html',
    ]
    
    missing = []
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - 不存在")
            missing.append(file)
    
    if missing:
        print(f"  ⚠️  缺少 {len(missing)} 个必需文件")
        return False
    
    print("  ✅ 项目结构完整")
    return True

def check_settings_file():
    """检查配置文件"""
    print("\n[5/5] 检查配置文件...")
    
    settings_file = Path('settings.toml')
    if settings_file.exists():
        print("  ✅ settings.toml 存在")
        return True
    else:
        print("  ⚠️  settings.toml 不存在")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("GTPlanner 环境检查")
    print("=" * 60)
    
    results = []
    
    # 检查 Python 版本
    results.append(('Python 版本', check_python_version()))
    
    # 检查依赖
    results.append(('依赖包', check_dependencies()))
    
    # 检查环境变量
    results.append(('环境变量', check_environment_variables()))
    
    # 检查项目结构
    results.append(('项目结构', check_project_structure()))
    
    # 检查配置文件
    results.append(('配置文件', check_settings_file()))
    
    # 总结
    print("\n" + "=" * 60)
    print("检查结果总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 项通过")
    
    if passed == total:
        print("\n🎉 环境检查通过！可以启动项目了。")
        print("\n启动方式:")
        print("  CLI: python gtplanner.py")
        print("  API: python fastapi_main.py")
        return 0
    else:
        print("\n⚠️  请先解决上述问题后再启动项目。")
        return 1

if __name__ == "__main__":
    sys.exit(main())

