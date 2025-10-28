#!/usr/bin/env python3
"""
GTPlanner 服务启动脚本
自动配置环境并启动 FastAPI 服务
"""

import os
import sys
import subprocess

def check_and_setup():
    """检查环境并设置"""
    print("检查环境配置...")
    
    # 设置默认值（如果未配置）
    if not os.getenv('LLM_API_KEY'):
        print("⚠️  警告: 未设置 LLM_API_KEY")
        print()
        print("请在启动前设置环境变量：")
        print("  $env:LLM_API_KEY='your-api-key'")
        print("  $env:LLM_BASE_URL='https://api.openai.com/v1'")
        print("  $env:LLM_MODEL='gpt-4'")
        print()
        
        # 问用户是否继续
        response = input("是否继续启动服务？(需要手动配置 API Key) [y/N]: ")
        if response.lower() != 'y':
            print("已取消启动")
            sys.exit(0)
    
    print("✓ 环境检查完成")
    print()

def start_api():
    """启动 FastAPI 服务"""
    print("=" * 60)
    print("正在启动 GTPlanner FastAPI 服务...")
    print("=" * 60)
    print()
    print("服务地址: http://0.0.0.0:11211")
    print("API 文档: http://0.0.0.0:11211/docs")
    print()
    print("按 Ctrl+C 停止服务")
    print()
    
    try:
        # 启动 FastAPI 服务
        subprocess.run([sys.executable, 'fastapi_main.py'])
    except KeyboardInterrupt:
        print()
        print("服务已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    check_and_setup()
    
    # 检查核心模块
    try:
        print("检查核心模块...")
        from agent.stateless_planner import StatelessGTPlanner
        print("✓ 核心模块正常")
        print()
    except Exception as e:
        print(f"✗ 核心模块加载失败: {e}")
        print("请先安装依赖: pip install -r requirements.txt")
        sys.exit(1)
    
    start_api()

if __name__ == "__main__":
    main()

