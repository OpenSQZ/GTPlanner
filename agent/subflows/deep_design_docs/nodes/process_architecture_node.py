"""
Process Architecture Node

管理Architecture Agent的执行，协调Agent设计文档的生成。
"""

import time
from typing import Dict, Any
from pocketflow import AsyncNode
from agent.streaming import (
    emit_processing_status,
    emit_error
)


class ProcessArchitectureNode(AsyncNode):
    """架构处理节点 - 管理Agent设计文档生成"""

    def __init__(self):
        super().__init__()
        self.name = "ProcessArchitectureNode"
        self.description = "管理Agent设计文档生成流程"

        # 延迟初始化架构设计流程，避免循环导入
        self.architecture_flow = None
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：验证输入并准备流程执行"""
        try:
            # 检查必需的输入 - 支持多种输入源
            has_user_requirements = "user_requirements" in shared and shared["user_requirements"]
            has_short_planning = "short_planning" in shared and shared["short_planning"]

            if not (has_user_requirements or has_short_planning):
                return {"error": "缺少必需的输入: 需要 user_requirements 或 short_planning 中的任意一个"}

            # 获取输入数据
            user_requirements = shared.get("user_requirements", shared.get("short_planning", ""))
            research_findings = shared.get("research_findings", {})
            confirmation_document = shared.get("confirmation_document", "")
            recommended_tools = shared.get("recommended_tools", [])

            return {
                "user_requirements": user_requirements,
                "research_findings": research_findings,
                "confirmation_document": confirmation_document,
                "recommended_tools": recommended_tools,
                "processing_start_time": time.time(),
                "streaming_session": shared.get("streaming_session")
            }
            
        except Exception as e:
            return {"error": f"Architecture processing preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行阶段：运行架构设计流程"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])

            # 发送处理状态事件
            streaming_session = prep_result.get("streaming_session")
            if streaming_session:
                from agent.streaming import emit_processing_status_from_prep
                await emit_processing_status_from_prep(prep_result, "🔄 开始Agent设计文档生成...")

            # 动态导入避免循环导入
            if self.architecture_flow is None:
                from ..flows.deep_design_docs_flow import ArchitectureFlow
                self.architecture_flow = ArchitectureFlow()

            # 创建流程共享状态
            flow_shared = {
                "user_requirements": prep_result["user_requirements"],
                "research_findings": prep_result["research_findings"],
                "confirmation_document": prep_result["confirmation_document"],
                "recommended_tools": prep_result.get("recommended_tools", []),  # 添加推荐工具
                "streaming_session": prep_result.get("streaming_session")  # 添加流式会话
            }

            # 异步执行架构设计流程
            flow_result = await self.architecture_flow.run_async(flow_shared)
            
            if flow_result == "success":
                # 构建流程执行摘要
                flow_summary = {
                    "status": "completed",
                    "generated_files": flow_shared.get("generated_files", []),
                    "agent_design_document": flow_shared.get("agent_design_document", ""),
                    "output_directory": flow_shared.get("output_directory", "")
                }
                
                return {
                    "processing_success": True,
                    "flow_result": flow_result,
                    "flow_summary": flow_summary,
                    "flow_shared": flow_shared,
                    "processing_time": time.time() - prep_result["processing_start_time"]
                }
            else:
                raise Exception(f"Architecture flow failed with result: {flow_result}")
                
        except Exception as e:
            return {
                "processing_success": False,
                "error": f"Architecture processing execution failed: {str(e)}",
                "processing_time": time.time() - prep_result.get("processing_start_time", time.time())
            }
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：更新共享状态"""
        try:
            if not exec_res.get("processing_success", False):
                # 处理失败
                error_msg = exec_res.get("error", "Unknown error")
                shared["architecture_processing_error"] = error_msg

                
                await emit_error(shared, f"❌ 架构设计处理失败: {error_msg}")
                return "error"
            
            # 处理成功，更新共享状态
            flow_summary = exec_res["flow_summary"]
            flow_shared = exec_res["flow_shared"]
            
            # 保存生成的设计文档
            if "agent_design_document" in flow_shared:
                shared["agent_design_document"] = flow_shared["agent_design_document"]
            
            # 保存生成的文件信息
            if "generated_files" in flow_shared:
                shared["generated_files"] = flow_shared["generated_files"]
            
            if "output_directory" in flow_shared:
                shared["output_directory"] = flow_shared["output_directory"]
            
         
            
            # 添加系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []
            
            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "architecture_processing",
                "status": "completed",
                "message": "Agent设计文档生成完成",
                "details": {
                    "processing_time": exec_res["processing_time"],
                    "generated_files": len(flow_summary.get("generated_files", [])),
                    "output_directory": flow_summary.get("output_directory", "")
                }
            })
            
            await emit_processing_status(shared, f"✅ Agent设计处理完成")
            await emit_processing_status(shared, f"   处理时间: {exec_res['processing_time']:.2f}秒")

            if flow_summary.get("generated_files"):
                files_count = len(flow_summary["generated_files"])
                await emit_processing_status(shared, f"   生成文件: {files_count}个")
                await emit_processing_status(shared, f"   输出目录: {flow_summary.get('output_directory', '')}")

            return "success"

        except Exception as e:
            shared["architecture_post_error"] = str(e)
            await emit_error(shared, f"❌ 架构设计后处理失败: {str(e)}")
            return "error"
