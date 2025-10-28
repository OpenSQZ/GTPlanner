#!/usr/bin/env python3
"""
测试 LLM 配置
"""

import os
import sys

def check_config():
    """检查 LLM 配置"""
    print("=" * 60)
    print("LLM 配置检查")
    print("=" * 60)
    
    # 检查环境变量
    api_key = os.getenv('LLM_API_KEY')
    base_url = os.getenv('LLM_BASE_URL')
    model = os.getenv('LLM_MODEL')
    
    print(f"LLM_API_KEY: {'已设置 ✅' if api_key else '未设置 ❌'}")
    print(f"LLM_BASE_URL: {'已设置 ✅' if base_url else '未设置 ❌'}")
    print(f"LLM_MODEL: {'已设置 ✅' if model else '未设置 ❌'}")
    
    if api_key:
        # 只显示前10个字符
        print(f"  API Key: {api_key[:10]}...")
    if base_url:
        print(f"  Base URL: {base_url}")
    if model:
        print(f"  Model: {model}")
    
    print("-" * 60)
    
    # 判断配置是否完整
    is_complete = all([api_key, base_url, model])
    
    if is_complete:
        print("✅ 配置完整，可以启动服务")
        print("\n启动命令：")
        print("  python fastapi_main.py")
        return True
    else:
        print("❌ 配置不完整")
        print("\n缺失配置：")
        if not api_key:
            print("  - LLM_API_KEY")
        if not base_url:
            print("  - LLM_BASE_URL")
        if not model:
            print("  - LLM_MODEL")
        return False

if __name__ == "__main__":
    success = check_config()
    sys.exit(0 if success else 1)

