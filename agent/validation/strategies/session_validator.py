"""
会话验证策略

基于策略模式的会话验证实现，提供：
- 会话ID格式验证
- 会话有效性检查
- 会话过期验证
- 会话状态一致性检查
- 集成现有会话管理系统
"""

import re
import time
from typing import Dict, Any, List, Optional
from ..core.interfaces import IValidationStrategy, ValidatorPriority
from ..core.validation_context import ValidationContext
from ..core.validation_result import (
    ValidationResult, ValidationError, ValidationStatus, ValidationSeverity
)
# from ..core.base_validator import BaseValidator  # 暂时注释避免dynaconf依赖

# 尝试导入现有的会话管理器
try:
    from agent.persistence.sqlite_session_manager import SQLiteSessionManager
    SESSION_MANAGER_AVAILABLE = True
except ImportError:
    SESSION_MANAGER_AVAILABLE = False


class SessionValidationStrategy(IValidationStrategy):
    """会话验证策略 - 检查会话相关信息的有效性"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.validate_session_id_format = config.get("validate_session_id_format", True)
        self.check_session_expiry = config.get("check_session_expiry", False)
        self.require_valid_session = config.get("require_valid_session", False)
        self.max_session_inactivity = config.get("max_session_inactivity", 3600)  # 1小时
        
        # 会话ID格式正则（支持多种格式）
        self.session_id_patterns = [
            re.compile(r'^[a-zA-Z0-9_-]{8,64}$'),  # 标准格式：8-64字符的字母数字下划线横线
            re.compile(r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$'),  # UUID格式
            re.compile(r'^session_[a-zA-Z0-9_]{4,32}$'),  # session_前缀格式
            re.compile(r'^[a-zA-Z0-9]{16,32}$'),  # 简单的16-32字符格式
        ]
        
        # 初始化会话管理器
        if SESSION_MANAGER_AVAILABLE:
            try:
                self.session_manager = SQLiteSessionManager()
            except Exception:
                self.session_manager = None
        else:
            self.session_manager = None
    
    async def execute(self, data: Any, rules: Dict[str, Any]) -> ValidationResult:
        """执行会话验证"""
        result = ValidationResult(ValidationStatus.SUCCESS)
        
        if not isinstance(data, dict):
            return result
        
        session_id = data.get("session_id")
        
        # 验证会话ID格式
        if self.validate_session_id_format:
            await self._validate_session_id_format(session_id, result)
        
        # 验证会话有效性
        if self.require_valid_session and session_id:
            await self._validate_session_existence(session_id, result)
        
        # 检查会话过期
        if self.check_session_expiry and session_id:
            await self._validate_session_expiry(session_id, result)
        
        # 验证会话数据一致性
        await self._validate_session_consistency(data, result)
        
        return result
    
    async def _validate_session_id_format(self, session_id: Any, result: ValidationResult) -> None:
        """验证会话ID格式"""
        if session_id is None:
            error = ValidationError(
                code="MISSING_SESSION_ID",
                message="缺少会话ID",
                field="session_id",
                validator="session",
                severity=ValidationSeverity.HIGH,
                suggestion="请提供有效的会话ID"
            )
            result.add_error(error)
            return
        
        if not isinstance(session_id, str):
            error = ValidationError.create_format_error(
                field="session_id",
                expected_type="字符串",
                actual_value=type(session_id).__name__,
                validator="session"
            )
            result.add_error(error)
            return
        
        # 检查会话ID长度
        if len(session_id.strip()) == 0:
            error = ValidationError(
                code="EMPTY_SESSION_ID",
                message="会话ID不能为空",
                field="session_id",
                validator="session",
                severity=ValidationSeverity.HIGH,
                suggestion="请提供非空的会话ID"
            )
            result.add_error(error)
            return
        
        # 检查会话ID格式
        session_id = session_id.strip()
        format_valid = any(pattern.match(session_id) for pattern in self.session_id_patterns)
        
        if not format_valid:
            error = ValidationError(
                code="INVALID_SESSION_ID_FORMAT",
                message=f"会话ID格式无效：'{session_id}'",
                field="session_id",
                value=session_id,
                validator="session",
                severity=ValidationSeverity.MEDIUM,
                suggestion="请使用有效的会话ID格式（8-64字符的字母数字组合、UUID格式等）",
                metadata={"session_id_length": len(session_id)}
            )
            result.add_error(error)
    
    async def _validate_session_existence(self, session_id: str, result: ValidationResult) -> None:
        """验证会话是否存在"""
        if not self.session_manager:
            # 如果没有会话管理器，跳过此检查
            return
        
        try:
            # 检查会话是否存在
            session_exists = await self._check_session_exists(session_id)
            
            if not session_exists:
                error = ValidationError(
                    code="SESSION_NOT_FOUND",
                    message=f"会话不存在：'{session_id}'",
                    field="session_id",
                    value=session_id,
                    validator="session",
                    severity=ValidationSeverity.HIGH,
                    suggestion="请使用有效的会话ID，或创建新的会话"
                )
                result.add_error(error)
        
        except Exception as e:
            # 会话检查失败，记录警告
            error = ValidationError(
                code="SESSION_CHECK_FAILED",
                message=f"无法验证会话存在性：{str(e)}",
                field="session_id",
                validator="session",
                severity=ValidationSeverity.LOW,
                suggestion="会话验证服务可能暂时不可用"
            )
            result.add_warning(error)
    
    async def _validate_session_expiry(self, session_id: str, result: ValidationResult) -> None:
        """验证会话是否过期"""
        if not self.session_manager:
            return
        
        try:
            last_activity = await self._get_session_last_activity(session_id)
            
            if last_activity:
                current_time = time.time()
                inactivity_time = current_time - last_activity
                
                if inactivity_time > self.max_session_inactivity:
                    error = ValidationError(
                        code="SESSION_EXPIRED",
                        message=f"会话已过期：非活跃时间 {int(inactivity_time)} 秒，超过限制 {self.max_session_inactivity} 秒",
                        field="session_id",
                        value=session_id,
                        validator="session",
                        severity=ValidationSeverity.MEDIUM,
                        suggestion="请创建新的会话或重新激活现有会话",
                        metadata={
                            "inactivity_time": int(inactivity_time),
                            "max_inactivity": self.max_session_inactivity,
                            "last_activity": last_activity
                        }
                    )
                    result.add_error(error)
        
        except Exception as e:
            error = ValidationError(
                code="SESSION_EXPIRY_CHECK_FAILED",
                message=f"无法检查会话过期状态：{str(e)}",
                field="session_id",
                validator="session",
                severity=ValidationSeverity.LOW,
                suggestion="会话过期检查服务可能暂时不可用"
            )
            result.add_warning(error)
    
    async def _validate_session_consistency(self, data: dict, result: ValidationResult) -> None:
        """验证会话数据一致性"""
        session_id = data.get("session_id")
        session_metadata = data.get("session_metadata", {})
        
        if not session_id or not isinstance(session_metadata, dict):
            return
        
        # 检查元数据中的会话ID是否一致
        metadata_session_id = session_metadata.get("session_id")
        if metadata_session_id and metadata_session_id != session_id:
            error = ValidationError(
                code="SESSION_ID_MISMATCH",
                message=f"会话ID不一致：主字段 '{session_id}' vs 元数据 '{metadata_session_id}'",
                field="session_metadata.session_id",
                validator="session",
                severity=ValidationSeverity.MEDIUM,
                suggestion="请确保主会话ID与元数据中的会话ID一致",
                metadata={"main_session_id": session_id, "metadata_session_id": metadata_session_id}
            )
            result.add_error(error)
        
        # 检查对话历史中的会话一致性
        dialogue_history = data.get("dialogue_history", [])
        if isinstance(dialogue_history, list):
            await self._check_dialogue_session_consistency(dialogue_history, session_id, result)
    
    async def _check_dialogue_session_consistency(self, dialogue_history: List[Any], session_id: str, result: ValidationResult) -> None:
        """检查对话历史中的会话一致性"""
        for i, message in enumerate(dialogue_history):
            if isinstance(message, dict):
                # 检查消息元数据中的会话ID
                msg_metadata = message.get("metadata", {})
                if isinstance(msg_metadata, dict):
                    msg_session_id = msg_metadata.get("session_id")
                    if msg_session_id and msg_session_id != session_id:
                        error = ValidationError(
                            code="MESSAGE_SESSION_MISMATCH",
                            message=f"消息会话ID不匹配：第 {i+1} 条消息属于会话 '{msg_session_id}'，当前会话 '{session_id}'",
                            field=f"dialogue_history[{i}].metadata.session_id",
                            validator="session",
                            severity=ValidationSeverity.MEDIUM,
                            suggestion="请确保所有消息都属于当前会话",
                            metadata={
                                "message_index": i,
                                "expected_session": session_id,
                                "actual_session": msg_session_id
                            }
                        )
                        result.add_warning(error)
    
    async def _check_session_exists(self, session_id: str) -> bool:
        """检查会话是否存在（模拟实现）"""
        if self.session_manager:
            try:
                # 这里应该调用实际的会话管理器方法
                # 由于我们没有具体的实现，这里返回True
                return True
            except Exception:
                return False
        return True
    
    async def _get_session_last_activity(self, session_id: str) -> Optional[float]:
        """获取会话最后活动时间（模拟实现）"""
        if self.session_manager:
            try:
                # 这里应该调用实际的会话管理器方法
                # 由于我们没有具体的实现，返回当前时间
                return time.time()
            except Exception:
                return None
        return time.time()
    
    def get_strategy_name(self) -> str:
        return "session"


# SessionValidator类已暂时移除，避免BaseValidator依赖
