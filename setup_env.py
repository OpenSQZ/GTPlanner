#!/usr/bin/env python3
"""
GTPlanner 环境配置向导
帮助用户快速配置所需的环境变量
"""

import os
import sys

def print_header():
    """打印欢迎信息"""
    print("=" * 60)
    print("GTPlanner 环境配置向导")
    print("=" * 60)
    print()

def check_existing_env():
    """检查现有环境变量"""
    print("检查当前环境配置...")
    print()
    
    api_key = os.getenv('LLM_API_KEY')
    base_url = os.getenv('LLM_BASE_URL')
    model = os.getenv('LLM_MODEL')
    
    if api_key:
        print(f"✓ LLM_API_KEY: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else ''}")
    else:
        print("✗ LLM_API_KEY: 未设置")
    
    if base_url:
        print(f"✓ LLM_BASE_URL: {base_url}")
    else:
        print("✗ LLM_BASE_URL: 未设置")
    
    if model:
        print(f"✓ LLM_MODEL: {model}")
    else:
        print("✗ LLM_MODEL: 未设置")
    
    print()
    
    if api_key and base_url and model:
        print("环境变量已配置，可以直接启动项目！")
        return True
    else:
        print("需要配置环境变量才能启动项目。")
        return False

def show_instructions():
    """显示配置说明"""
    print("配置环境变量：")
    print()
    print("方式 1: 使用环境变量")
    print()
    print("Windows PowerShell:")
    print("  $env:LLM_API_KEY='sk-your-api-key'")
    print("  $env:LLM_BASE_URL='https://api.openai.com/v1'")
    print("  $env:LLM_MODEL='gpt-4'")
    print()
    print("Linux/Mac:")
    print("  export LLM_API_KEY='sk-your-api-key'")
    print("  export LLM_BASE_URL='https://api.openai.com/v1'")
    print("  export LLM_MODEL='gpt-4'")
    print()
    print("方式 2: 创建 .env 文件")
    print()
    print("创建 .env 文件并添加以下内容：")
    print("  LLM_API_KEY=sk-your-api-key")
    print("  LLM_BASE_URL=https://api.openai.com/v1")
    print("  LLM_MODEL=gpt-4")
    print()
    print("=" * 60)
    print()

def main():
    """主函数"""
    print_header()
    
    # 检查现有配置
    is_configured = check_existing_env()
    
    if not is_configured:
        show_instructions()
        print("请按照上述方式配置环境变量后再运行项目。")
        sys.exit(1)
    else:
        print("环境配置检查通过！")
        print()
        print("可以使用以下命令启动项目：")
        print("  1. CLI 模式: python gtplanner.py")
        print("  2. FastAPI: python fastapi_main.py")
        print("  3. 启动脚本: start_windows.bat")
        sys.exit(0)

if __name__ == "__main__":
    main()

