"""
需求分析节点抽象基类

提取需求分析节点的共同逻辑，减少代码重复，支持流式和非流式处理。
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

from agent.base_node import BaseAgentNode
from utils.openai_client import get_openai_client
from agent.prompts import get_prompt, PromptTypes
from agent.prompts.text_manager import get_text_manager
from agent.streaming import emit_design_document, emit_processing_status


class AnalysisType(Enum):
    """分析类型枚举"""
    QUICK = "quick"
    DEEP = "deep"
    AGENT = "agent"


class ProcessingMode(Enum):
    """处理模式枚举"""
    STANDARD = "standard"
    STREAMING = "streaming"


class BaseRequirementsAnalysisNode(BaseAgentNode, ABC):
    """
    需求分析节点抽象基类
    
    提取所有需求分析节点的共同逻辑：
    1. 数据准备和验证
    2. LLM调用
    3. 结果处理和存储
    4. 错误处理
    """
    
    def __init__(
        self,
        node_name: str,
        analysis_type: AnalysisType,
        processing_mode: ProcessingMode = ProcessingMode.STANDARD,
        required_fields: Optional[List[str]] = None
    ):
        """
        初始化需求分析节点
        
        Args:
            node_name: 节点名称
            analysis_type: 分析类型
            processing_mode: 处理模式
            required_fields: 必需字段列表
        """
        super().__init__(node_name)
        self.analysis_type = analysis_type
        self.processing_mode = processing_mode
        self.required_fields = required_fields or ["user_requirements"]
        
        # 配置映射
        self.prompt_type_mapping = {
            AnalysisType.QUICK: PromptTypes.Agent.QUICK_REQUIREMENTS_ANALYSIS,
            AnalysisType.DEEP: PromptTypes.Agent.DEEP_REQUIREMENTS_ANALYSIS,
            AnalysisType.AGENT: PromptTypes.Agent.DEEP_REQUIREMENTS_ANALYSIS
        }
    
    async def _prep_impl(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备阶段：收集和验证需求信息
        
        Args:
            shared: 共享状态字典
            
        Returns:
            准备结果字典
        """
        try:
            # 提取基础数据
            prep_data = self._extract_base_data(shared)
            
            # 验证必需字段
            validation_error = self._validate_required_fields(prep_data)
            if validation_error:
                return {"error": validation_error}
            
            # 格式化工具和研究信息
            prep_data.update(self._format_additional_data(shared, prep_data.get("language")))
            
            # 子类特定的准备逻辑
            additional_data = await self._prep_specific(shared, prep_data)
            prep_data.update(additional_data)
            
            return prep_data
            
        except Exception as e:
            return {"error": f"准备阶段失败: {str(e)}"}
    
    async def _exec_impl(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：分析需求
        
        Args:
            prep_result: 准备阶段结果
            
        Returns:
            执行结果字典
        """
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建提示词
            prompt = self._build_analysis_prompt(prep_result)
            
            # 调用LLM分析
            if self.processing_mode == ProcessingMode.STREAMING:
                analysis_result = await self._analyze_with_streaming(prompt, prep_result)
            else:
                analysis_result = await self._analyze_standard(prompt, prep_result)
            
            # 子类特定的结果处理
            processed_result = await self._process_analysis_result(analysis_result, prep_result)
            
            return {
                "analysis_result": processed_result,
                "analysis_success": True,
                "analysis_type": self.analysis_type.value,
                "processing_mode": self.processing_mode.value
            }
            
        except Exception as e:
            return {"error": f"{self.analysis_type.value}需求分析失败: {str(e)}"}
    
    async def _post_impl(
        self,
        shared: Dict[str, Any],
        prep_res: Dict[str, Any],
        exec_res: Dict[str, Any]
    ) -> str:
        """
        后处理阶段：保存分析结果
        
        Args:
            shared: 共享状态字典
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果
            
        Returns:
            处理结果状态
        """
        try:
            if "error" in exec_res:
                error_key = f"{self.analysis_type.value}_analysis_error"
                shared[error_key] = exec_res["error"]
                print(f"❌ {self.analysis_type.value}需求分析失败: {exec_res['error']}")
                return "error"
            
            # 保存分析结果
            result_key = self._get_result_key()
            analysis_result = exec_res["analysis_result"]
            shared[result_key] = analysis_result
            
            # 生成设计文档（如果需要）
            if self._should_generate_document():
                await self._generate_design_document(shared, analysis_result)
            
            # 更新系统消息
            self._update_system_messages(shared)
            
            # 子类特定的后处理
            await self._post_specific(shared, prep_res, exec_res)
            
            return "success"
            
        except Exception as e:
            print(f"❌ {self.analysis_type.value}需求分析后处理失败: {str(e)}")
            return "error"
    
    def _extract_base_data(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """提取基础数据"""
        return {
            "user_requirements": shared.get("user_requirements", ""),
            "short_planning": shared.get("short_planning", ""),
            "research_findings": shared.get("research_findings", {}),
            "recommended_tools": shared.get("recommended_tools", []),
            "language": shared.get("language"),
            "streaming_session": shared.get("streaming_session")
        }
    
    def _validate_required_fields(self, prep_data: Dict[str, Any]) -> Optional[str]:
        """验证必需字段"""
        for field in self.required_fields:
            if not prep_data.get(field):
                return f"缺少必需字段: {field}"
        return None
    
    def _format_additional_data(self, shared: Dict[str, Any], language: str) -> Dict[str, Any]:
        """格式化工具和研究信息"""
        text_manager = get_text_manager()
        
        tools_info = text_manager.build_tools_content(
            recommended_tools=shared.get("recommended_tools", []),
            language=language
        )
        
        research_summary = text_manager.build_research_content(
            research_findings=shared.get("research_findings", {}),
            language=language
        )
        
        return {
            "tools_info": tools_info,
            "research_summary": research_summary
        }
    
    def _build_analysis_prompt(self, prep_result: Dict[str, Any]) -> str:
        """构建分析提示词"""
        prompt_type = self.prompt_type_mapping[self.analysis_type]
        
        return get_prompt(
            prompt_type,
            language=prep_result.get("language"),
            user_requirements=prep_result["user_requirements"],
            short_planning=prep_result["short_planning"],
            tools_info=prep_result["tools_info"],
            research_summary=prep_result["research_summary"]
        )
    
    async def _analyze_standard(self, prompt: str, prep_result: Dict[str, Any]) -> str:
        """标准分析模式"""
        client = get_openai_client()
        response = await client.chat_completion(
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content if response.choices else ""
    
    async def _analyze_with_streaming(self, prompt: str, prep_result: Dict[str, Any]) -> str:
        """流式分析模式"""
        # 发送处理状态
        streaming_session = prep_result.get("streaming_session")
        if streaming_session:
            await emit_processing_status(
                prep_result,
                f"🔍 开始{self.analysis_type.value}需求分析..."
            )
        
        # 执行标准分析（可以扩展为真正的流式处理）
        return await self._analyze_standard(prompt, prep_result)
    
    def _get_result_key(self) -> str:
        """获取结果存储键"""
        key_mapping = {
            AnalysisType.QUICK: "requirements",
            AnalysisType.DEEP: "analysis_markdown",
            AnalysisType.AGENT: "analysis_markdown"
        }
        return key_mapping.get(self.analysis_type, "analysis_result")
    
    def _should_generate_document(self) -> bool:
        """是否应该生成设计文档"""
        return self.analysis_type == AnalysisType.QUICK
    
    async def _generate_design_document(self, shared: Dict[str, Any], analysis_result: str):
        """生成设计文档"""
        if self.analysis_type == AnalysisType.QUICK:
            await emit_design_document(
                shared,
                "quick_requirements_analysis.md",
                analysis_result
            )
    
    def _update_system_messages(self, shared: Dict[str, Any]):
        """更新系统消息"""
        if "system_messages" not in shared:
            shared["system_messages"] = []
        
        shared["system_messages"].append({
            "timestamp": time.time(),
            "stage": f"{self.analysis_type.value}_requirements_analysis",
            "status": "completed",
            "message": f"{self.analysis_type.value}需求分析完成"
        })
    
    # 抽象方法 - 子类需要实现
    
    @abstractmethod
    async def _prep_specific(self, shared: Dict[str, Any], prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        子类特定的准备逻辑
        
        Args:
            shared: 共享状态字典
            prep_data: 基础准备数据
            
        Returns:
            额外的准备数据
        """
        pass
    
    @abstractmethod
    async def _process_analysis_result(self, analysis_result: str, prep_result: Dict[str, Any]) -> str:
        """
        子类特定的结果处理
        
        Args:
            analysis_result: LLM分析结果
            prep_result: 准备阶段结果
            
        Returns:
            处理后的结果
        """
        pass
    
    async def _post_specific(
        self,
        shared: Dict[str, Any],
        prep_res: Dict[str, Any],
        exec_res: Dict[str, Any]
    ):
        """
        子类特定的后处理逻辑
        
        Args:
            shared: 共享状态字典
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果
        """
        pass
