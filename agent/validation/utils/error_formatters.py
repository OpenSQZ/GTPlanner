"""
错误格式化器

提供多种错误响应格式化功能：
- HTTP错误响应格式化
- 多语言错误消息
- 错误代码映射
- 建议信息生成
- 敏感信息脱敏
"""

import re
from typing import Dict, Any, Optional, List
from ..core.validation_context import ValidationContext
from ..core.validation_result import ValidationResult, ValidationError, ValidationSeverity

# 尝试导入现有的多语言系统
try:
    from utils.multilingual_utils import MultilingualManager
    MULTILINGUAL_AVAILABLE = True
except ImportError:
    MULTILINGUAL_AVAILABLE = False


class ErrorFormatter:
    """错误格式化器 - 统一的错误响应格式化
    
    提供多种格式化选项：
    - 标准HTTP错误响应格式
    - 多语言错误消息支持
    - 敏感信息自动脱敏
    - 用户友好的错误建议
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 格式化配置
        self.include_suggestions = self.config.get("include_suggestions", True)
        self.include_error_codes = self.config.get("include_error_codes", True)
        self.include_field_details = self.config.get("include_field_details", True)
        self.mask_sensitive_data = self.config.get("mask_sensitive_data", True)
        self.max_error_message_length = self.config.get("max_error_message_length", 500)
        self.include_validator_info = self.config.get("include_validator_info", False)
        
        # 初始化多语言管理器
        if MULTILINGUAL_AVAILABLE:
            try:
                self.multilingual_manager = MultilingualManager()
            except Exception:
                self.multilingual_manager = None
        else:
            self.multilingual_manager = None
        
        # 错误消息模板
        self.error_templates = self._load_error_templates()
    
    def _load_error_templates(self) -> Dict[str, Dict[str, str]]:
        """加载错误消息模板
        
        Returns:
            多语言错误消息模板字典
        """
        return {
            "XSS_DETECTED": {
                "en": "Cross-site scripting (XSS) attack detected",
                "zh": "检测到跨站脚本攻击（XSS）",
                "es": "Ataque de secuencias de comandos entre sitios (XSS) detectado",
                "fr": "Attaque de script inter-sites (XSS) détectée",
                "ja": "クロスサイトスクリプティング（XSS）攻撃が検出されました"
            },
            "SQL_INJECTION_DETECTED": {
                "en": "SQL injection attack detected",
                "zh": "检测到SQL注入攻击",
                "es": "Ataque de inyección SQL detectado",
                "fr": "Attaque par injection SQL détectée",
                "ja": "SQLインジェクション攻撃が検出されました"
            },
            "SIZE_LIMIT_EXCEEDED": {
                "en": "Size limit exceeded",
                "zh": "大小限制超出",
                "es": "Límite de tamaño excedido",
                "fr": "Limite de taille dépassée",
                "ja": "サイズ制限を超過しました"
            },
            "RATE_LIMIT_EXCEEDED": {
                "en": "Rate limit exceeded",
                "zh": "频率限制超出",
                "es": "Límite de velocidad excedido",
                "fr": "Limite de débit dépassée",
                "ja": "レート制限を超過しました"
            },
            "INVALID_FORMAT": {
                "en": "Invalid format",
                "zh": "格式无效",
                "es": "Formato inválido",
                "fr": "Format invalide",
                "ja": "無効な形式"
            },
            "MISSING_REQUIRED_FIELDS": {
                "en": "Missing required fields",
                "zh": "缺少必需字段",
                "es": "Faltan campos requeridos",
                "fr": "Champs requis manquants",
                "ja": "必須フィールドが不足しています"
            }
        }
    
    def format_response(self, result: ValidationResult, context: Optional[ValidationContext] = None) -> Dict[str, Any]:
        """格式化验证结果为HTTP响应
        
        Args:
            result: 验证结果
            context: 验证上下文（可选）
            
        Returns:
            格式化的HTTP响应字典
        """
        # 确定语言
        language = self._determine_language(context)
        
        if result.is_valid:
            return self._format_success_response(result, language)
        else:
            return self._format_error_response(result, context, language)
    
    def _format_success_response(self, result: ValidationResult, language: str) -> Dict[str, Any]:
        """格式化成功响应
        
        Args:
            result: 验证结果
            language: 语言代码
            
        Returns:
            成功响应字典
        """
        response = {
            "success": True,
            "status": result.status.value,
            "message": self._get_localized_message("VALIDATION_SUCCESS", language, "验证通过"),
            "execution_time": round(result.execution_time, 3)
        }
        
        # 添加警告信息
        if result.has_warnings:
            response["warnings"] = [
                self._format_error_item(warning, language, include_suggestion=False)
                for warning in result.warnings
            ]
            response["warning_count"] = len(result.warnings)
        
        # 添加请求ID
        if result.request_id:
            response["request_id"] = result.request_id
        
        return response
    
    def _format_error_response(self, result: ValidationResult, context: Optional[ValidationContext], language: str) -> Dict[str, Any]:
        """格式化错误响应
        
        Args:
            result: 验证结果
            context: 验证上下文
            language: 语言代码
            
        Returns:
            错误响应字典
        """
        response = {
            "success": False,
            "status": result.status.value,
            "message": self._get_localized_message("VALIDATION_FAILED", language, "验证失败"),
            "execution_time": round(result.execution_time, 3)
        }
        
        # 添加错误列表
        if result.has_errors:
            response["errors"] = [
                self._format_error_item(error, language)
                for error in result.errors
            ]
            response["error_count"] = len(result.errors)
        
        # 添加警告列表
        if result.has_warnings:
            response["warnings"] = [
                self._format_error_item(warning, language, include_suggestion=False)
                for warning in result.warnings
            ]
            response["warning_count"] = len(result.warnings)
        
        # 添加失败的验证器信息
        failed_validators = result.get_failed_validators()
        if failed_validators:
            response["failed_validators"] = failed_validators
        
        # 添加请求ID
        if result.request_id:
            response["request_id"] = result.request_id
        
        # 添加错误摘要
        error_summary = result.get_error_summary()
        if error_summary:
            response["error_summary"] = error_summary
        
        # 添加调试信息（非生产环境）
        if self.include_validator_info and context:
            response["debug_info"] = {
                "validation_path": result.execution_order,
                "validation_mode": context.validation_mode.value,
                "endpoint": context.request_path,
                "user_identifier": context.get_user_identifier()
            }
        
        return response
    
    def _format_error_item(self, error: ValidationError, language: str, include_suggestion: bool = True) -> Dict[str, Any]:
        """格式化单个错误项
        
        Args:
            error: 验证错误
            language: 语言代码
            include_suggestion: 是否包含建议
            
        Returns:
            格式化的错误项字典
        """
        # 获取本地化消息
        localized_message = self._get_localized_error_message(error.code, language, error.message)
        
        # 脱敏处理
        if self.mask_sensitive_data:
            localized_message = self._sanitize_message(localized_message)
        
        # 截断消息长度
        if len(localized_message) > self.max_error_message_length:
            localized_message = localized_message[:self.max_error_message_length] + "..."
        
        error_item = {
            "message": localized_message,
            "severity": error.severity.name
        }
        
        # 添加错误代码
        if self.include_error_codes:
            error_item["code"] = error.code
        
        # 添加字段信息
        if self.include_field_details and error.field:
            error_item["field"] = error.field
        
        # 添加验证器信息
        if self.include_validator_info and error.validator:
            error_item["validator"] = error.validator
        
        # 添加建议信息
        if include_suggestion and self.include_suggestions and error.suggestion:
            suggestion = self._get_localized_suggestion(error.code, language, error.suggestion)
            if self.mask_sensitive_data:
                suggestion = self._sanitize_message(suggestion)
            error_item["suggestion"] = suggestion
        
        return error_item
    
    def _determine_language(self, context: Optional[ValidationContext]) -> str:
        """确定响应语言
        
        Args:
            context: 验证上下文
            
        Returns:
            语言代码
        """
        if context:
            return context.get_language_preference()
        
        # 默认语言
        return "zh"  # 根据用户规则，默认使用中文
    
    def _get_localized_message(self, message_key: str, language: str, default_message: str) -> str:
        """获取本地化消息
        
        Args:
            message_key: 消息键
            language: 语言代码
            default_message: 默认消息
            
        Returns:
            本地化的消息
        """
        # 简单的本地化实现
        if language == "en":
            return {
                "VALIDATION_SUCCESS": "Validation passed",
                "VALIDATION_FAILED": "Validation failed"
            }.get(message_key, default_message)
        elif language == "zh":
            return {
                "VALIDATION_SUCCESS": "验证通过",
                "VALIDATION_FAILED": "验证失败"
            }.get(message_key, default_message)
        else:
            return default_message
    
    def _get_localized_error_message(self, error_code: str, language: str, default_message: str) -> str:
        """获取本地化错误消息
        
        Args:
            error_code: 错误代码
            language: 语言代码
            default_message: 默认消息
            
        Returns:
            本地化的错误消息
        """
        if error_code in self.error_templates:
            template = self.error_templates[error_code]
            return template.get(language, template.get("zh", default_message))
        
        return default_message
    
    def _get_localized_suggestion(self, error_code: str, language: str, default_suggestion: str) -> str:
        """获取本地化建议信息
        
        Args:
            error_code: 错误代码
            language: 语言代码
            default_suggestion: 默认建议
            
        Returns:
            本地化的建议信息
        """
        # 建议信息的本地化模板
        suggestion_templates = {
            "XSS_DETECTED": {
                "en": "Please remove HTML tags and JavaScript code",
                "zh": "请移除HTML标签和JavaScript代码",
                "es": "Por favor elimine las etiquetas HTML y el código JavaScript",
                "fr": "Veuillez supprimer les balises HTML et le code JavaScript",
                "ja": "HTMLタグとJavaScriptコードを削除してください"
            },
            "SQL_INJECTION_DETECTED": {
                "en": "Please avoid SQL keywords and special characters",
                "zh": "请避免使用SQL关键字和特殊字符",
                "es": "Por favor evite las palabras clave SQL y caracteres especiales",
                "fr": "Veuillez éviter les mots-clés SQL et les caractères spéciaux",
                "ja": "SQLキーワードと特殊文字の使用を避けてください"
            },
            "SIZE_LIMIT_EXCEEDED": {
                "en": "Please reduce the content size",
                "zh": "请减少内容大小",
                "es": "Por favor reduzca el tamaño del contenido",
                "fr": "Veuillez réduire la taille du contenu",
                "ja": "コンテンツのサイズを小さくしてください"
            }
        }
        
        if error_code in suggestion_templates:
            template = suggestion_templates[error_code]
            return template.get(language, template.get("zh", default_suggestion))
        
        return default_suggestion
    
    def _sanitize_message(self, message: str) -> str:
        """清理消息中的敏感信息
        
        Args:
            message: 原始消息
            
        Returns:
            清理后的消息
        """
        if not self.mask_sensitive_data:
            return message
        
        # 替换邮箱地址
        message = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', message)
        
        # 替换信用卡号
        message = re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[CARD]', message)
        
        # 替换身份证号
        message = re.sub(r'\b\d{17}[\dXx]\b', '[ID_CARD]', message)
        message = re.sub(r'\b\d{15}\b', '[ID_CARD]', message)
        
        # 替换手机号
        message = re.sub(r'\b1[3-9]\d{9}\b', '[PHONE]', message)
        
        # 替换IP地址
        message = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP_ADDRESS]', message)
        
        # 替换可能的密码或令牌（简单模式）
        message = re.sub(r'\b[A-Za-z0-9+/]{20,}={0,2}\b', '[TOKEN]', message)
        
        return message
    
    def format_error_for_logging(self, error: ValidationError, context: Optional[ValidationContext] = None) -> Dict[str, Any]:
        """为日志记录格式化错误
        
        Args:
            error: 验证错误
            context: 验证上下文
            
        Returns:
            日志格式的错误字典
        """
        log_error = {
            "code": error.code,
            "message": error.message,
            "severity": error.severity.name,
            "validator": error.validator
        }
        
        if error.field:
            log_error["field"] = error.field
        
        if error.suggestion:
            log_error["suggestion"] = error.suggestion
        
        if error.metadata:
            # 过滤敏感的元数据
            filtered_metadata = {}
            for key, value in error.metadata.items():
                if key not in ["match", "actual_value", "pattern"] or not self.mask_sensitive_data:
                    filtered_metadata[key] = value
            log_error["metadata"] = filtered_metadata
        
        if context:
            log_error["context"] = {
                "request_id": context.request_id,
                "endpoint": context.request_path,
                "user_id": context.user_id,
                "session_id": context.session_id
            }
        
        return log_error
    
    def format_validation_summary(self, result: ValidationResult, language: str = "zh") -> str:
        """格式化验证结果摘要
        
        Args:
            result: 验证结果
            language: 语言代码
            
        Returns:
            验证结果摘要字符串
        """
        if result.is_valid:
            base_message = self._get_localized_message("VALIDATION_SUCCESS", language, "验证通过")
            
            if result.has_warnings:
                warning_message = f"，但有 {len(result.warnings)} 个警告" if language == "zh" else f", but with {len(result.warnings)} warnings"
                return base_message + warning_message
            
            return base_message
        
        else:
            base_message = self._get_localized_message("VALIDATION_FAILED", language, "验证失败")
            
            if language == "zh":
                return f"{base_message}：{len(result.errors)} 个错误"
            else:
                return f"{base_message}: {len(result.errors)} errors"
    
    def create_user_friendly_message(self, result: ValidationResult, language: str = "zh") -> str:
        """创建用户友好的消息
        
        Args:
            result: 验证结果
            language: 语言代码
            
        Returns:
            用户友好的消息字符串
        """
        if result.is_valid:
            return self._get_localized_message("VALIDATION_SUCCESS", language, "请求验证通过")
        
        # 根据错误类型生成友好消息
        if result.has_critical_errors:
            critical_errors = [error for error in result.errors if error.severity == ValidationSeverity.CRITICAL]
            
            if any(error.code.startswith("XSS") for error in critical_errors):
                if language == "zh":
                    return "请求包含不安全的内容，请移除HTML标签和脚本代码"
                else:
                    return "Request contains unsafe content, please remove HTML tags and script code"
            
            elif any(error.code.startswith("SQL") for error in critical_errors):
                if language == "zh":
                    return "请求包含不安全的数据库查询，请检查输入内容"
                else:
                    return "Request contains unsafe database queries, please check input content"
        
        # 根据最常见的错误类型生成消息
        error_summary = result.get_error_summary()
        if error_summary:
            most_common_error = max(error_summary.items(), key=lambda x: x[1])[0]
            
            if most_common_error.startswith("SIZE"):
                if language == "zh":
                    return "请求内容过大，请减少数据量"
                else:
                    return "Request content is too large, please reduce data size"
            
            elif most_common_error.startswith("MISSING"):
                if language == "zh":
                    return "请求缺少必需的字段，请检查数据格式"
                else:
                    return "Request is missing required fields, please check data format"
            
            elif most_common_error.startswith("RATE_LIMIT"):
                if language == "zh":
                    return "请求过于频繁，请稍后重试"
                else:
                    return "Requests are too frequent, please try again later"
        
        # 默认错误消息
        if language == "zh":
            return f"请求验证失败，发现 {len(result.errors)} 个问题"
        else:
            return f"Request validation failed with {len(result.errors)} issues"
    
    def format_for_api_response(self, result: ValidationResult, context: Optional[ValidationContext] = None) -> Dict[str, Any]:
        """为API响应格式化（简化版本）
        
        Args:
            result: 验证结果
            context: 验证上下文
            
        Returns:
            API响应格式的字典
        """
        language = self._determine_language(context)
        
        if result.is_valid:
            return {
                "valid": True,
                "message": self._get_localized_message("VALIDATION_SUCCESS", language, "验证通过")
            }
        else:
            return {
                "valid": False,
                "message": self.create_user_friendly_message(result, language),
                "error_codes": [error.code for error in result.errors],
                "request_id": result.request_id
            }


def create_error_formatter(config: Optional[Dict[str, Any]] = None) -> ErrorFormatter:
    """创建错误格式化器的便捷函数
    
    Args:
        config: 格式化器配置
        
    Returns:
        错误格式化器实例
    """
    return ErrorFormatter(config)
