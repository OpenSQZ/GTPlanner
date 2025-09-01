"""
GTPlanner 基本功能测试
"""
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_import_gtplanner():
    """测试 gtplanner 模块导入"""
    try:
        import gtplanner
        assert True, "gtplanner 模块导入成功"
    except ImportError as e:
        pytest.fail(f"gtplanner 模块导入失败: {e}")


def test_import_fastapi_main():
    """测试 fastapi_main 模块导入"""
    try:
        import fastapi_main
        assert True, "fastapi_main 模块导入成功"
    except ImportError as e:
        pytest.fail(f"fastapi_main 模块导入失败: {e}")


def test_import_agent():
    """测试 agent 模块导入"""
    try:
        import agent
        assert True, "agent 模块导入成功"
    except ImportError as e:
        pytest.fail(f"agent 模块导入失败: {e}")


def test_import_utils():
    """测试 utils 模块导入"""
    try:
        import utils
        assert True, "utils 模块导入成功"
    except ImportError as e:
        pytest.fail(f"utils 模块导入失败: {e}")


def test_project_structure():
    """测试项目结构"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 检查关键文件是否存在
    key_files = [
        'gtplanner.py',
        'fastapi_main.py',
        'pyproject.toml',
        'README.md'
    ]
    
    for file in key_files:
        file_path = os.path.join(project_root, file)
        assert os.path.exists(file_path), f"关键文件 {file} 不存在"
    
    # 检查关键目录是否存在
    key_dirs = [
        'agent',
        'utils',
        'api'
    ]
    
    for dir_name in key_dirs:
        dir_path = os.path.join(project_root, dir_name)
        assert os.path.exists(dir_path), f"关键目录 {dir_name} 不存在"


if __name__ == "__main__":
    pytest.main([__file__])
