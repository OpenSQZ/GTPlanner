"""
GTPlanner 主入口类

提供GTPlanner系统的主要接口，封装整个处理流程。
"""

from typing import Dict, Any, Union
from datetime import datetime
from .shared import get_shared_state, reset_shared_state
from .flows import ReActOrchestratorRefactored


class GTPlanner:
    """GTPlanner 主控制器"""
    
    def __init__(self, reset_state: bool = True):
        """
        初始化GTPlanner
        
        Args:
            reset_state: 是否重置共享状态，默认True
        """
        if reset_state:
            reset_shared_state()
            
        self.shared_state = get_shared_state()
        self.orchestrator = ReActOrchestratorRefactored()
        
    def process_user_request(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户请求

        Args:
            user_input: 用户输入的需求描述

        Returns:
            处理结果字典
        """
        try:
            # 添加用户消息到对话历史
            self.shared_state.add_user_message(user_input)
            
            # 更新处理阶段
            self.shared_state.update_stage("processing_user_request")
            
            # 执行主流程
            result = self.orchestrator.run(self.shared_state)
            
            # 更新处理阶段
            self.shared_state.update_stage("completed")
            
            return {
                "success": True,
                "result": result,
                "session_id": self.shared_state.session_id,
                "timestamp": datetime.now().isoformat(),
                "error_count": self.shared_state.error_count
            }
            
        except Exception as e:
            # 记录错误
            self.shared_state.record_error(e, "process_user_request")
            self.shared_state.update_stage("error")
            
            return {
                "success": False,
                "result": None,
                "session_id": self.shared_state.session_id,
                "timestamp": datetime.now().isoformat(),
                "error_count": self.shared_state.error_count,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.shared_state.to_dict()
    
    def save_state(self, filepath: str):
        """保存状态到文件"""
        self.shared_state.save_to_file(filepath)
    
    def get_dialogue_history(self) -> Union[Dict[str, Any], list]:
        """获取对话历史"""
        return self.shared_state.dialogue_history



    def get_research_findings(self) -> Union[Dict[str, Any], None]:
        """获取研究发现"""
        return self.shared_state.research_findings

    def get_architecture_draft(self) -> Union[Dict[str, Any], None]:
        """获取架构草稿"""
        return self.shared_state.architecture_draft
    
    def reset(self):
        """重置系统状态"""
        reset_shared_state()
        self.shared_state = get_shared_state()


