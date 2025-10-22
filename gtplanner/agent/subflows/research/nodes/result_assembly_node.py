"""
结果组装节点 - Research Agent的2d步骤

负责将搜索结果、URL内容和LLM分析结果组装成单个关键词的完整报告
"""

import time
from pocketflow import AsyncNode


class ResultAssemblyNode(AsyncNode):
    """结果组装节点 - 2d步骤"""
    
    def __init__(self):
        super().__init__()
        self.name = "ResultAssemblyNode"
    
    async def prep_async(self, shared):
        """准备结果组装"""
        # 从共享变量中获取所有必要数据
        current_keyword = shared.get("current_keyword", "")
        search_result = shared.get("first_search_result", {})
        url_content = shared.get("url_content", "")
        llm_analysis = shared.get("llm_analysis", {})
        
        return {
            "keyword": current_keyword,
            "url": search_result.get("url", ""),
            "title": search_result.get("title", ""),
            "content": url_content,
            "analysis": llm_analysis
        }
    
    async def exec_async(self, prep_res):
        """执行结果组装"""
        # 简化的关键词报告结构
        analysis = prep_res.get("analysis", {})

        keyword_report = {
            "keyword": prep_res["keyword"],
            "source": {
                "url": prep_res["url"],
                "title": prep_res["title"]
            },
            "summary": analysis.get("summary", ""),
            "key_points": analysis.get("key_points", []),
            "recommendations": analysis.get("recommendations", []),
            "processed_at": time.time()
        }

        return {"keyword_report": keyword_report}
    
    async def post_async(self, shared, prep_res, exec_res):
        """保存组装结果到共享变量"""
        if "error" in exec_res:
            # 记录错误到shared字典
            if "errors" not in shared:
                shared["errors"] = []
            shared["errors"].append({
                "source": "ResultAssemblyNode",
                "error": exec_res["error"],
                "timestamp": time.time()
            })
            return "error"

        # 保存关键词报告
        keyword_report = exec_res["keyword_report"]
        shared["keyword_report"] = keyword_report

        # 简化的research_findings格式
        shared["research_findings"] = {
            "keyword": keyword_report["keyword"],
            "summary": keyword_report["summary"],
            "key_points": keyword_report["key_points"],
            "recommendations": keyword_report["recommendations"],
            "source": keyword_report["source"]
        }

        return "assembly_complete"
