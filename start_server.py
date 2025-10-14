#!/usr/bin/env python3
"""
GTPlanner 服务器启动脚本

提供便捷的服务器启动和管理功能，支持多种运行模式。
"""

import os
import sys
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('gtplanner_server.log')
    ]
)
logger = logging.getLogger(__name__)


def setup_environment():
    """设置环境变量"""
    # 设置必要的环境变量
    os.environ.setdefault('PYTHONPATH', str(project_root))
    os.environ.setdefault('GT_PLANNER_VERBOSE', 'true')
    
    # 确保必要的目录存在
    static_dir = project_root / "static"
    static_dir.mkdir(exist_ok=True)
    
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)


def validate_dependencies():
    """验证依赖项"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'asyncio'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"缺少必要的依赖包: {', '.join(missing_packages)}")
        logger.error("请运行: pip install -r requirements.txt")
        return False
    
    return True


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    try:
        from fastapi_main import app
        logger.info("✅ FastAPI 应用创建成功")
        return app
    except Exception as e:
        logger.error(f"❌ 创建 FastAPI 应用失败: {e}")
        raise


def run_server(
    host: str = "0.0.0.0",
    port: int = 11211,
    reload: bool = False,
    workers: int = 1,
    log_level: str = "info"
):
    """运行服务器"""
    logger.info(f"🚀 启动 GTPlanner 服务器...")
    logger.info(f"   地址: http://{host}:{port}")
    logger.info(f"   重载模式: {'开启' if reload else '关闭'}")
    logger.info(f"   工作进程: {workers}")
    logger.info(f"   日志级别: {log_level}")
    
    try:
        uvicorn.run(
            "fastapi_main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,  # reload 模式下只能使用单进程
            log_level=log_level,
            access_log=True,
            server_header=False,
            date_header=False
        )
    except KeyboardInterrupt:
        logger.info("🛑 服务器已停止")
    except Exception as e:
        logger.error(f"❌ 服务器运行错误: {e}")
        raise


def run_development_server():
    """运行开发服务器"""
    logger.info("🔧 启动开发服务器模式")
    run_server(
        host="127.0.0.1",
        port=11211,
        reload=True,
        log_level="debug"
    )


def run_production_server(port: int = 11211, workers: int = 4):
    """运行生产服务器"""
    logger.info("🏭 启动生产服务器模式")
    run_server(
        host="0.0.0.0",
        port=port,
        reload=False,
        workers=workers,
        log_level="info"
    )


async def health_check():
    """健康检查"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:11211/health", timeout=5.0)
            if response.status_code == 200:
                logger.info("✅ 服务器健康检查通过")
                return True
            else:
                logger.error(f"❌ 服务器健康检查失败: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"❌ 健康检查错误: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="GTPlanner 服务器启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python start_server.py                    # 开发模式
  python start_server.py --prod             # 生产模式
  python start_server.py --port 8080        # 指定端口
  python start_server.py --host 0.0.0.0     # 指定主机
  python start_server.py --check            # 健康检查
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["dev", "prod"],
        default="dev",
        help="运行模式 (默认: dev)"
    )
    
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="服务器主机地址 (默认: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=11211,
        help="服务器端口 (默认: 11211)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="工作进程数 (默认: 4, 仅生产模式)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="日志级别 (默认: info)"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="执行健康检查"
    )
    
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="禁用自动重载 (开发模式)"
    )
    
    args = parser.parse_args()
    
    # 设置环境
    setup_environment()
    
    # 验证依赖
    if not validate_dependencies():
        sys.exit(1)
    
    # 健康检查
    if args.check:
        logger.info("🔍 执行健康检查...")
        success = asyncio.run(health_check())
        sys.exit(0 if success else 1)
    
    # 创建应用（验证导入）
    try:
        app = create_app()
    except Exception as e:
        logger.error(f"❌ 应用创建失败: {e}")
        sys.exit(1)
    
    # 根据模式运行服务器
    try:
        if args.mode == "dev":
            logger.info("🔧 开发模式启动")
            run_server(
                host=args.host,
                port=args.port,
                reload=not args.no_reload,
                log_level=args.log_level
            )
        else:
            logger.info("🏭 生产模式启动")
            run_server(
                host=args.host,
                port=args.port,
                reload=False,
                workers=args.workers,
                log_level=args.log_level
            )
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
