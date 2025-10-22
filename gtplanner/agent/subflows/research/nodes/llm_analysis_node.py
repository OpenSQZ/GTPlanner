"""
LLM分析节点 - Research Agent的2c步骤

负责使用LLM分析URL解析后的内容，提取关键洞察和技术细节
"""

import asyncio
from pocketflow import AsyncNode

from utils.openai_client import get_openai_client
from agent.streaming import (
    emit_processing_status,
    emit_error
)

# 导入多语言提示词系统
from agent.prompts import get_prompt, PromptTypes


class LLMAnalysisNode(AsyncNode):
    """LLM分析节点 - 2c步骤"""
    
    def __init__(self):
        super().__init__()
        self.name = "LLMAnalysisNode"
    
    async def prep_async(self, shared):
        """准备LLM分析"""
        # 从共享变量中获取URL解析结果
        url_content = shared.get("url_content", "")
        current_keyword = shared.get("current_keyword", "")
        analysis_requirements = shared.get("analysis_requirements", "")
        language = shared.get("language")  # 获取语言设置

        if not url_content:
            return {"error": "No URL content available for analysis"}

        return {
            "url_content": url_content,
            "current_keyword": current_keyword,
            "analysis_requirements": analysis_requirements,
            "language": language  # 添加语言设置
        }
    
    async def exec_async(self, prep_res):
        """执行LLM分析"""
        if "error" in prep_res:
            return {"error": prep_res["error"]}

        url_content = prep_res["url_content"]
        keyword = prep_res["current_keyword"]
        analysis_requirements = prep_res["analysis_requirements"]
        language = prep_res["language"]

        # 使用LLM进行内容分析 - 异步调用
        try:
            analysis_result = await self._analyze_content_with_llm_async(
                url_content, keyword, analysis_requirements, language
            )

            return {
                "analysis": analysis_result,
                "keyword": keyword
            }

        except Exception as e:
            error_msg = f"LLM分析执行失败: {str(e)}"
            print(f"❌ {error_msg}")

            # 返回错误结果而不是抛出异常，让post_async处理
            return {
                "error": error_msg,
                "keyword": keyword,
                "failed_stage": "llm_analysis"
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        """保存LLM分析结果到共享变量"""
        try:
            if "error" in exec_res:
                # 记录执行阶段的错误
                error_info = {
                    "source": "LLMAnalysisNode.exec",
                    "error": exec_res["error"],
                    "keyword": prep_res.get("current_keyword", "unknown"),
                    "timestamp": prep_res.get("timestamp", ""),
                    "stage": "execution"
                }

                if "errors" not in shared:
                    shared["errors"] = []
                shared["errors"].append(error_info)

                # 设置分析失败状态
                shared["llm_analysis_status"] = "failed"
                shared["llm_analysis_error"] = exec_res["error"]

                print(f"❌ LLM分析执行失败: {exec_res['error']}")
                return "error"

            # 保存分析结果到共享变量
            analysis_result = exec_res["analysis"]
            keyword = exec_res["keyword"]

            shared["llm_analysis"] = analysis_result
            shared["analyzed_keyword"] = keyword
            shared["llm_analysis_status"] = "success"

            print(f"✅ LLM分析完成: {keyword}")
            return "analysis_complete"

        except Exception as e:
            # 记录后处理阶段的错误
            error_info = {
                "source": "LLMAnalysisNode.post",
                "error": str(e),
                "keyword": prep_res.get("current_keyword", "unknown"),
                "timestamp": prep_res.get("timestamp", ""),
                "stage": "post_processing"
            }

            if "errors" not in shared:
                shared["errors"] = []
            shared["errors"].append(error_info)

            # 设置分析失败状态
            shared["llm_analysis_status"] = "failed"
            shared["llm_analysis_post_error"] = str(e)

            print(f"❌ LLM分析后处理失败: {e}")
            return "error"
    
    async def _analyze_content_with_llm_async(self, content, keyword, requirements, language=None):
        """异步使用LLM分析内容，使用多语言模板系统"""
        # 使用新的多语言模板系统获取提示词
        prompt = get_prompt(
            PromptTypes.Agent.RESEARCH_ANALYSIS,
            language=language,
            keyword=keyword,
            requirements=requirements,
            content=content[:2000]
        )

        try:
            client = get_openai_client()
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                ##todo 公司网关 kimi 会报错不支持json_object response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content if response.choices else ""

            # 确保返回标准格式
            if isinstance(result, str):
                import json
                result = json.loads(result)

            # 标准化返回格式
            return {
                "summary": result.get("summary", f"关于{keyword}的分析"),
                "key_points": result.get("key_points", []),
                "relevance": result.get("relevance", "相关性分析"),
                "recommendations": result.get("recommendations", []),
                "keyword": keyword
            }
        except Exception as e:
            # 抛出异常，让上层处理
            raise Exception(f"LLM内容分析失败: {str(e)}")
