import sys
from pathlib import Path

# Add the parent directory to the Python path to import from the main project
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

import asyncio
from typing import Any, Optional

from fastmcp import FastMCP

# 导入本地规划模块
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入短规划流程
from gtplanner.agent.subflows.short_planning.flows.short_planning_flow import ShortPlanningFlow

# 定义请求模型
class LongPlanningRequest:
    def __init__(self, requirement: str, previous_flow: str, design_doc=None, language: str = None, user_id: str = None):
        self.requirement = requirement
        self.previous_flow = previous_flow
        self.design_doc = design_doc
        self.language = language
        self.user_id = user_id

class ShortPlanningRequest:
    def __init__(self, requirement: str, previous_flow: str = None, language: str = None, user_id: str = None):
        self.requirement = requirement
        self.previous_flow = previous_flow
        self.language = language
        self.user_id = user_id

# 创建规划流程实例
short_planning_flow = ShortPlanningFlow()

async def short_planning(request: ShortPlanningRequest) -> dict:
    """短规划处理函数"""
    try:
        # 准备共享状态
        shared_state = {
            "user_requirements": request.requirement,
            "previous_planning": request.previous_flow,
            "language": request.language or "zh",
            "user_id": request.user_id
        }

        # 运行短规划流程
        result = await short_planning_flow.run_async(shared_state)

        return {
            "flow": result,
            "language": request.language or "zh"
        }
    except Exception as e:
        return {
            "flow": f"Error: {str(e)}",
            "language": request.language or "zh"
        }

async def long_planning(request: LongPlanningRequest) -> dict:
    """长规划处理函数（暂时使用短规划逻辑）"""
    try:
        # 准备共享状态
        shared_state = {
            "user_requirements": request.requirement,
            "previous_planning": request.previous_flow,
            "design_doc": request.design_doc,
            "language": request.language or "zh",
            "user_id": request.user_id
        }

        # 运行短规划流程（长规划功能待实现）
        result = await short_planning_flow.run_async(shared_state)

        return {
            "flow": result,
            "language": request.language or "zh"
        }
    except Exception as e:
        return {
            "flow": f"Error: {str(e)}",
            "language": request.language or "zh"
        }

app = FastMCP()


@app.tool(
    description="Generate workflow based on user requirements and optional previous flow. Supports multiple languages (en, zh, es, fr, ja). If previous_flow is empty, generates new workflow; otherwise generates updated workflow based on modification requirements and existing flow."
)
async def generate_flow(
    requirement: str,
    previous_flow: Optional[str] = None,
    language: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict:
    """Generate workflow with multilingual support"""
    try:
        # Validate language if provided
        if language:
            from utils.multilingual_utils import validate_language_request

            is_valid, message = validate_language_request(language)
            if not is_valid:
                return {"error": message}

        # Create request object with multilingual support
        request = ShortPlanningRequest(
            requirement=requirement,
            previous_flow=previous_flow,
            language=language,
            user_id=user_id,
        )

        # Call short_planning function
        result = await short_planning(request)

        # Extract flow content and language info
        flow = result.get("flow", "No flow generated.")
        # Use detected language from result, fallback to request language only if not empty, otherwise default to "en"
        response_language = result.get("language", language if language else "en")

        return {"flow": flow, "language": response_language, "user_id": user_id}
    except Exception as e:
        return {"error": f"Failed to generate flow: {str(e)}"}


@app.tool(
    description="Generate detailed design document based on user requirements, workflow, and optional existing design document. Supports multiple languages (en, zh, es, fr, ja). Only proceed when user explicitly mentions generating detailed design document."
)
async def generate_design_doc(
    requirement: str,
    previous_flow: str,
    design_doc: Optional[Any] = None,
    language: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict:
    """Generate detailed design document with multilingual support"""
    try:
        # Validate language if provided
        if language:
            from utils.multilingual_utils import validate_language_request

            is_valid, message = validate_language_request(language)
            if not is_valid:
                return {"error": message}

        # Create request object with multilingual support
        request = LongPlanningRequest(
            requirement=requirement,
            previous_flow=previous_flow,
            design_doc=design_doc,
            language=language,
            user_id=user_id,
        )

        # Call long_planning function
        result = await long_planning(request)

        # Extract design document content and language info
        doc = result.get("flow", "No design document generated.")
        response_language = result.get("language", language or "en")

        return {"design_doc": doc, "language": response_language, "user_id": user_id}
    except Exception as e:
        return {"error": f"Failed to generate design document: {str(e)}"}


if __name__ == "__main__":
    asyncio.run(app.run_streamable_http_async(port=8001))
