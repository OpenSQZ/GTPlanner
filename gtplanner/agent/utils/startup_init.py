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

from gtplanner.utils.config_manager import get_vector_service_config
from gtplanner.agent.streaming import emit_processing_status

logger = logging.getLogger(__name__)


async def initialize_application(
    preload_index: bool = False,  # 默认不预加载索引
    shared: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    应用启动初始化

    Args:
        preload_index: 是否检查预制件索引（已弃用，保留仅为兼容性）
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
        # 1. 检查 AGENT_BUILDER_API_KEY 环境变量
        api_key_result = await _check_agent_builder_api_key(shared)
        init_result["components"]["agent_builder_api_key"] = api_key_result

        if not api_key_result["configured"]:
            init_result["errors"].append("AGENT_BUILDER_API_KEY 未配置")

        # 2. 检查向量服务配置
        vector_config_result = await _check_vector_service_config(shared)
        init_result["components"]["vector_service"] = vector_config_result

        if not vector_config_result["available"]:
            init_result["errors"].append("向量服务不可用")

        # 注意：预制件索引由 CI/CD 构建，不在启动时加载
        # 如需重建索引，请运行: python prefabs/releases/scripts/build_index.py

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


async def _check_agent_builder_api_key(shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """检查 AGENT_BUILDER_API_KEY 环境变量"""
    import os

    try:
        if shared:
            await emit_processing_status(shared, "🔑 检查 AGENT_BUILDER_API_KEY 配置...")

        api_key = os.getenv("AGENT_BUILDER_API_KEY")

        # 检查是否配置
        if not api_key or not api_key.strip():
            logger.warning("⚠️  AGENT_BUILDER_API_KEY 未配置")
            logger.warning("⚠️  call_prefab_function 工具将不可用")
            logger.warning("📝 请访问 https://the-agent-builder.com/workspace/api/keys 获取 API Key")
            logger.warning("💡 然后设置环境变量: export AGENT_BUILDER_API_KEY='your-api-key'")

            if shared:
                await emit_processing_status(
                    shared,
                    "⚠️  AGENT_BUILDER_API_KEY 未配置，call_prefab_function 工具将不可用\n"
                    "📝 请访问 https://the-agent-builder.com/workspace/api/keys 获取 API Key"
                )

            return {
                "configured": False,
                "message": "AGENT_BUILDER_API_KEY 未配置",
                "guide_url": "https://the-agent-builder.com/workspace/api/keys"
            }

        # 检查格式（应该以 sk- 开头）
        if not api_key.startswith("sk-"):
            logger.warning("⚠️  AGENT_BUILDER_API_KEY 格式可能不正确（应以 'sk-' 开头）")

            if shared:
                await emit_processing_status(shared, "⚠️  AGENT_BUILDER_API_KEY 格式可能不正确")

            return {
                "configured": True,
                "valid_format": False,
                "message": "API Key 格式可能不正确（应以 'sk-' 开头）"
            }

        logger.info("✅ AGENT_BUILDER_API_KEY 已配置")
        if shared:
            await emit_processing_status(shared, "✅ AGENT_BUILDER_API_KEY 已配置")

        return {
            "configured": True,
            "valid_format": True,
            "message": "API Key 已正确配置"
        }

    except Exception as e:
        logger.error(f"检查 AGENT_BUILDER_API_KEY 时出错: {str(e)}")
        return {
            "configured": False,
            "error": f"检查失败: {str(e)}"
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


def initialize_application_sync() -> Dict[str, Any]:
    """
    同步版本的应用初始化（用于非异步环境）

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
            initialize_application()
        )
        
    except Exception as e:
        return {
            "success": False,
            "components": {},
            "errors": [f"同步初始化失败: {str(e)}"]
        }


async def get_application_status() -> Dict[str, Any]:
    """获取应用状态"""
    vector_config = get_vector_service_config()
    return {
        "agent_builder_api_key": await _check_agent_builder_api_key(),
        "prefab_index": {
            "index_name": vector_config.get("prefabs_index_name", "document_gtplanner_prefabs"),
            "note": "索引由 CI/CD 构建，不在运行时管理"
        },
        "vector_service": await _check_vector_service_config()
    }


# 便捷函数
async def ensure_application_ready(shared: Dict[str, Any] = None) -> bool:
    """确保应用就绪"""
    init_result = await initialize_application(shared=shared)
    return init_result["success"]


if __name__ == "__main__":
    # 测试初始化
    import asyncio

    async def test_init():
        result = await initialize_application()
        # 只打印成功状态，不打印完整结果（避免泄露敏感信息）
        print(f"初始化{'成功' if result['success'] else '失败'}")
        if not result['success']:
            print(f"错误: {result['errors']}")

        status = await get_application_status()
        # 只打印索引信息，不打印完整状态（避免泄露 API Key 等敏感信息）
        print(f"索引名称: {status['prefab_index']['index_name']}")
        print(f"向量服务: {'可用' if status['vector_service']['available'] else '不可用'}")

    asyncio.run(test_init())
