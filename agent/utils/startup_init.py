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
import os
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
        # 0. 检查 LLM 配置（优先检查）
        llm_config_result = await _check_llm_config(shared)
        init_result["components"]["llm_config"] = llm_config_result
        
        if not llm_config_result["available"]:
            init_result["errors"].append("LLM API Key 未配置")
            logger.warning("⚠️ LLM API Key 未配置，应用将无法生成内容")
            logger.warning("   请设置环境变量: LLM_API_KEY, LLM_BASE_URL, LLM_MODEL")
            logger.warning("   参考文档: 配置LLM_API_KEY指南.md")
        
        # 1. 检查向量服务配置
        vector_config_result = await _check_vector_service_config(shared)
        init_result["components"]["vector_service"] = vector_config_result
        
        if not vector_config_result["available"]:
            init_result["errors"].append("向量服务不可用")
            logger.warning("⚠️ 向量服务不可用，工具推荐功能将受限")
        
        # 2. 预加载工具索引（如果启用）
        if preload_index and vector_config_result["available"]:
            index_result = await _preload_tool_index(tools_dir, shared)
            init_result["components"]["tool_index"] = index_result
            
            if not index_result["success"]:
                init_result["errors"].append(f"工具索引预加载失败: {index_result.get('error', 'Unknown error')}")
        
        # 3. 其他初始化任务可以在这里添加
        
        # 判断整体初始化是否成功（允许 LLM 配置缺失作为警告而非错误）
        # 只有非 LLM 相关的错误才标记为失败
        critical_errors = [e for e in init_result["errors"] if "LLM" not in e and "向量服务" not in e]
        init_result["success"] = len(critical_errors) == 0
        
        if init_result["success"]:
            if len(init_result["errors"]) == 0:
                logger.info("✅ 应用初始化完成")
                if shared:
                    await emit_processing_status(shared, "✅ 应用初始化完成")
            else:
                logger.info(f"✅ 应用初始化完成（有 {len(init_result['errors'])} 个警告）")
                if shared:
                    await emit_processing_status(shared, f"✅ 应用初始化完成（有 {len(init_result['errors'])} 个警告）")
        else:
            logger.warning(f"⚠️ 应用初始化完成，但有 {len(critical_errors)} 个错误")
            if shared:
                await emit_processing_status(shared, f"⚠️ 应用初始化完成，但有 {len(critical_errors)} 个错误")
        
        return init_result
        
    except Exception as e:
        error_msg = f"应用初始化失败: {str(e)}"
        logger.error(error_msg)
        init_result["success"] = False
        init_result["errors"].append(error_msg)
        return init_result


async def _check_llm_config(shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """检查 LLM 配置"""
    try:
        if shared:
            await emit_processing_status(shared, "🔍 检查 LLM 配置...")
        
        # 检查环境变量
        api_key = os.getenv("LLM_API_KEY")
        base_url = os.getenv("LLM_BASE_URL")
        model = os.getenv("LLM_MODEL")
        
        llm_config = {
            "api_key": api_key,
            "base_url": base_url,
            "model": model
        }
        
        # 判断配置是否完整
        is_available = all([api_key, base_url, model])
        
        result = {
            "available": is_available,
            "config": {
                "api_key_set": bool(api_key),
                "base_url_set": bool(base_url),
                "model_set": bool(model)
            }
        }
        
        if not is_available:
            missing = []
            if not api_key:
                missing.append("LLM_API_KEY")
            if not base_url:
                missing.append("LLM_BASE_URL")
            if not model:
                missing.append("LLM_MODEL")
            result["missing"] = missing
            result["error"] = f"缺少配置: {', '.join(missing)}"
        
        if shared:
            status = "✅ LLM 配置可用" if is_available else "❌ LLM 配置不完整"
            await emit_processing_status(shared, status)
        
        logger.info(f"{'✅' if is_available else '❌'} LLM 配置检查: {result}")
        
        return result
        
    except Exception as e:
        return {
            "available": False,
            "error": f"LLM 配置检查失败: {str(e)}"
        }


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
