"""
医疗智能体后端服务启动脚本
"""
import uvicorn
from config import Config

if __name__ == "__main__":
    print("🏥 启动医疗智能体后端系统...")
    print(f"📍 服务地址: http://{Config.HOST}:{Config.PORT}")
    print(f"📖 API文档: http://{Config.HOST}:{Config.PORT}/docs")
    print(f"🔧 调试模式: {'开启' if Config.DEBUG else '关闭'}")
    print("-" * 50)
    
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG
    )