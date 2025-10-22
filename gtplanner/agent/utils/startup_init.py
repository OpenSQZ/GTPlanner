"""
应用启动初始化模块

负责在应用启动时进行必要的初始化工作，包括：
- 工具索引预热
- 系统状态检查
- 配置验证

使用方式：
在应用主入口调用 initialize_application() 函数
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from agent.utils.tool_index_manager import tool_index_manager, ensure_tool_index
from utils.config_manager import get_vector_service_config
from agent.streaming import emit_processing_status

logger = logging.getLogger(__name__)


async def initialize_application(
    tools_dir: str = "tools",
    preload_index: bool = True,
    shared: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    应用启动初始化
    
    Args:
        tools_dir: 工具目录路径
        preload_index: 是否预加载工具索引
        shared: 共享状态，用于事件发送
        
    Returns:
        初始化结果字典
    """
    init_result = {
        "success": True,
        "components": {},
        "errors": []
    }
    
    logger.info("🚀 开始应用初始化...")
    
    try:
        # 1. 检查向量服务配置
        vector_config_result = await _check_vector_service_config(shared)
        init_result["components"]["vector_service"] = vector_config_result
        
        if not vector_config_result["available"]:
            init_result["errors"].append("向量服务不可用")
        
        # 2. 预加载工具索引（如果启用）
        if preload_index and vector_config_result["available"]:
            index_result = await _preload_tool_index(tools_dir, shared)
            init_result["components"]["tool_index"] = index_result
            
            if not index_result["success"]:
                init_result["errors"].append(f"工具索引预加载失败: {index_result.get('error', 'Unknown error')}")
        
        # 3. 其他初始化任务可以在这里添加
        
        # 判断整体初始化是否成功
        init_result["success"] = len(init_result["errors"]) == 0
        
        if init_result["success"]:
            logger.info("✅ 应用初始化完成")
            if shared:
                await emit_processing_status(shared, "✅ 应用初始化完成")
        else:
            logger.warning(f"⚠️ 应用初始化完成，但有 {len(init_result['errors'])} 个问题")
            if shared:
                await emit_processing_status(shared, f"⚠️ 应用初始化完成，但有 {len(init_result['errors'])} 个问题")
        
        return init_result
        
    except Exception as e:
        error_msg = f"应用初始化失败: {str(e)}"
        logger.error(error_msg)
        init_result["success"] = False
        init_result["errors"].append(error_msg)
        return init_result


async def _check_vector_service_config(shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """检查向量服务配置"""
    try:
        if shared:
            await emit_processing_status(shared, "🔍 检查向量服务配置...")
        
        vector_config = get_vector_service_config()
        base_url = vector_config.get("base_url")
        
        if not base_url:
            return {
                "available": False,
                "error": "向量服务URL未配置",
                "config": vector_config
            }
        
        # 检查向量服务可用性
        import requests
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            available = response.status_code == 200
        except Exception as e:
            available = False
            error = str(e)
        
        result = {
            "available": available,
            "config": vector_config
        }
        
        if not available:
            result["error"] = f"向量服务不可用: {error if 'error' in locals() else 'Unknown error'}"
        
        if shared:
            status = "✅ 向量服务可用" if available else f"❌ 向量服务不可用"
            await emit_processing_status(shared, status)
        
        return result
        
    except Exception as e:
        return {
            "available": False,
            "error": f"向量服务配置检查失败: {str(e)}"
        }


async def _preload_tool_index(tools_dir: str, shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """预加载工具索引"""
    try:
        if shared:
            await emit_processing_status(shared, "🔨 预加载工具索引...")
        
        # 使用索引管理器确保索引存在
        index_name = await ensure_tool_index(
            tools_dir=tools_dir,
            force_reindex=False,  # 启动时不强制重建，让管理器智能判断
            shared=shared
        )
        
        # 获取索引信息
        index_info = tool_index_manager.get_index_info()
        
        return {
            "success": True,
            "index_name": index_name,
            "index_info": index_info
        }
        
    except Exception as e:
        error_msg = f"工具索引预加载失败: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg
        }


def initialize_application_sync(
    tools_dir: str = "tools",
    preload_index: bool = True
) -> Dict[str, Any]:
    """
    同步版本的应用初始化（用于非异步环境）
    
    Args:
        tools_dir: 工具目录路径
        preload_index: 是否预加载工具索引
        
    Returns:
        初始化结果字典
    """
    try:
        # 创建新的事件循环或使用现有的
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            initialize_application(tools_dir, preload_index)
        )
        
    except Exception as e:
        return {
            "success": False,
            "components": {},
            "errors": [f"同步初始化失败: {str(e)}"]
        }


async def get_application_status() -> Dict[str, Any]:
    """获取应用状态"""
    return {
        "tool_index": {
            "ready": tool_index_manager.is_index_ready(),
            "info": tool_index_manager.get_index_info()
        },
        "vector_service": await _check_vector_service_config()
    }


# 便捷函数
async def ensure_application_ready(shared: Dict[str, Any] = None) -> bool:
    """确保应用就绪"""
    if not tool_index_manager.is_index_ready():
        init_result = await initialize_application(shared=shared)
        return init_result["success"]
    return True


if __name__ == "__main__":
    # 测试初始化
    import asyncio
    
    async def test_init():
        result = await initialize_application()
        print("初始化结果:", result)
        
        status = await get_application_status()
        print("应用状态:", status)
    
    asyncio.run(test_init())
