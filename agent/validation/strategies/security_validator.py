"""
安全验证策略

基于策略模式的安全验证实现，提供：
- XSS攻击检测（正则模式匹配）
- SQL注入检测（关键字和模式识别）
- 敏感信息检测（邮箱、电话、身份证等）
- CSRF保护验证
- 恶意脚本检测
"""

import re
from typing import Dict, Any, List, Optional, Pattern
from ..core.interfaces import IValidationStrategy, ValidatorPriority
from ..core.validation_context import ValidationContext
from ..core.validation_result import (
    ValidationResult, ValidationError, ValidationStatus, ValidationSeverity
)
# from ..core.base_validator import BaseValidator  # 暂时注释避免dynaconf依赖


class SecurityValidationStrategy(IValidationStrategy):
    """安全验证策略 - 检测XSS、SQL注入等安全威胁"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.xss_patterns = self._compile_xss_patterns()
        self.sql_injection_patterns = self._compile_sql_patterns()
        self.sensitive_patterns = self._compile_sensitive_patterns()
        self.script_patterns = self._compile_script_patterns()
    
    def _compile_xss_patterns(self) -> List[Pattern]:
        """编译XSS检测模式"""
        patterns = [
            # 脚本标签
            r'<script[^>]*>.*?</script>',
            r'<script[^>]*>',
            # JavaScript伪协议
            r'javascript\s*:',
            # 事件处理器
            r'on\w+\s*=',
            r'on\w+\s*\(',
            # 危险标签
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<applet[^>]*>',
            r'<meta[^>]*>',
            # 样式注入
            r'<style[^>]*>.*?</style>',
            r'style\s*=.*?expression\s*\(',
            # 数据URI
            r'data\s*:.*?base64',
            # VBScript
            r'vbscript\s*:',
        ]
        return [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in patterns]
    
    def _compile_sql_patterns(self) -> List[Pattern]:
        """编译SQL注入检测模式"""
        patterns = [
            # 经典SQL注入
            r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b.*\b(from|where|into|values|set)\b',
            # 逻辑注入
            r'[\'\"]\s*(or|and)\s*[\'\"]\s*=\s*[\'\"]\s*[\'\"]\s*',
            r'[\'\"]\s*(or|and)\s*\d+\s*=\s*\d+',
            r'\b(or|and)\s+\d+\s*=\s*\d+',
            # 注释注入
            r';\s*(drop|delete|update|insert|create|alter)',
            r'--\s*',
            r'/\*.*?\*/',
            r'#.*$',
            # 堆叠查询
            r';\s*(select|insert|update|delete)',
            # 函数注入
            r'\b(concat|substring|ascii|char|length|database|version|user|system_user)\s*\(',
            # 时间延迟注入
            r'\b(sleep|benchmark|waitfor|delay)\s*\(',
            # 联合查询
            r'\bunion\b.*\bselect\b',
        ]
        return [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in patterns]
    
    def _compile_sensitive_patterns(self) -> List[Pattern]:
        """编译敏感信息检测模式"""
        patterns = [
            # 邮箱地址
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # 信用卡号
            r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            # 身份证号（中国）
            r'\b\d{17}[\dXx]\b',
            r'\b\d{15}\b',
            # 手机号（中国）
            r'\b1[3-9]\d{9}\b',
            # IP地址
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            # SSN（美国社会安全号）
            r'\b\d{3}-\d{2}-\d{4}\b',
            # 银行卡号
            r'\b\d{16,19}\b',
        ]
        return [re.compile(pattern) for pattern in patterns]
    
    def _compile_script_patterns(self) -> List[Pattern]:
        """编译恶意脚本检测模式"""
        patterns = [
            # 混淆代码
            r'eval\s*\(',
            r'setTimeout\s*\(',
            r'setInterval\s*\(',
            # 编码绕过
            r'\\u[0-9a-fA-F]{4}',
            r'\\x[0-9a-fA-F]{2}',
            r'&#\d+;',
            r'&#x[0-9a-fA-F]+;',
            # 危险函数
            r'document\.write',
            r'document\.cookie',
            r'window\.location',
            r'document\.location',
        ]
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    async def execute(self, data: Any, rules: Dict[str, Any]) -> ValidationResult:
        """执行安全验证"""
        result = ValidationResult(ValidationStatus.SUCCESS)
        
        # 转换数据为字符串
        content = self._extract_content(data)
        if not content:
            return result
        
        # XSS检测
        if self.config.get("enable_xss_protection", True):
            await self._check_xss(content, result)
        
        # SQL注入检测
        if self.config.get("enable_sql_injection_detection", True):
            await self._check_sql_injection(content, result)
        
        # 敏感信息检测
        if self.config.get("enable_sensitive_data_detection", False):
            await self._check_sensitive_data(content, result)
        
        # 恶意脚本检测
        if self.config.get("enable_script_detection", True):
            await self._check_malicious_scripts(content, result)
        
        return result
    
    def _extract_content(self, data: Any) -> str:
        """提取待验证的内容"""
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            # 提取字典中的字符串值
            contents = []
            self._extract_dict_strings(data, contents)
            return " ".join(contents)
        elif isinstance(data, list):
            # 提取列表中的字符串值
            contents = []
            for item in data:
                if isinstance(item, str):
                    contents.append(item)
                elif isinstance(item, dict):
                    self._extract_dict_strings(item, contents)
            return " ".join(contents)
        else:
            return str(data)
    
    def _extract_dict_strings(self, data: dict, contents: List[str]) -> None:
        """递归提取字典中的字符串值"""
        for key, value in data.items():
            if isinstance(value, str):
                contents.append(value)
            elif isinstance(value, dict):
                self._extract_dict_strings(value, contents)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        contents.append(item)
                    elif isinstance(item, dict):
                        self._extract_dict_strings(item, contents)
    
    async def _check_xss(self, content: str, result: ValidationResult) -> None:
        """检查XSS攻击"""
        for pattern in self.xss_patterns:
            match = pattern.search(content)
            if match:
                error = ValidationError(
                    code="XSS_DETECTED",
                    message="检测到潜在的跨站脚本攻击（XSS）代码",
                    value=match.group(0)[:100],  # 只显示前100个字符
                    validator="security",
                    severity=ValidationSeverity.CRITICAL,
                    suggestion="请移除HTML标签、JavaScript代码和事件处理器",
                    metadata={"pattern": pattern.pattern, "match": match.group(0)}
                )
                result.add_error(error)
                break  # 只报告第一个匹配的XSS
    
    async def _check_sql_injection(self, content: str, result: ValidationResult) -> None:
        """检查SQL注入"""
        for pattern in self.sql_injection_patterns:
            match = pattern.search(content)
            if match:
                error = ValidationError(
                    code="SQL_INJECTION_DETECTED",
                    message="检测到潜在的SQL注入攻击",
                    value=match.group(0)[:100],
                    validator="security",
                    severity=ValidationSeverity.CRITICAL,
                    suggestion="请避免使用SQL关键字和特殊字符，使用参数化查询",
                    metadata={"pattern": pattern.pattern, "match": match.group(0)}
                )
                result.add_error(error)
                break  # 只报告第一个匹配的SQL注入
    
    async def _check_sensitive_data(self, content: str, result: ValidationResult) -> None:
        """检查敏感信息"""
        detected_types = []
        
        for i, pattern in enumerate(self.sensitive_patterns):
            match = pattern.search(content)
            if match:
                sensitive_type = [
                    "邮箱地址", "信用卡号", "身份证号", "身份证号", 
                    "手机号", "IP地址", "社会安全号", "银行卡号"
                ][i]
                detected_types.append(sensitive_type)
        
        if detected_types:
            error = ValidationError(
                code="SENSITIVE_DATA_DETECTED",
                message=f"检测到可能的敏感信息：{', '.join(detected_types)}",
                validator="security",
                severity=ValidationSeverity.HIGH,
                suggestion="请避免在请求中包含敏感个人信息，或对其进行脱敏处理",
                metadata={"detected_types": detected_types}
            )
            result.add_warning(error)  # 敏感信息作为警告处理
    
    async def _check_malicious_scripts(self, content: str, result: ValidationResult) -> None:
        """检查恶意脚本"""
        for pattern in self.script_patterns:
            match = pattern.search(content)
            if match:
                error = ValidationError(
                    code="MALICIOUS_SCRIPT_DETECTED",
                    message="检测到潜在的恶意脚本代码",
                    value=match.group(0)[:100],
                    validator="security",
                    severity=ValidationSeverity.HIGH,
                    suggestion="请移除JavaScript函数调用和DOM操作代码",
                    metadata={"pattern": pattern.pattern, "match": match.group(0)}
                )
                result.add_error(error)
                break
    
    def get_strategy_name(self) -> str:
        return "security"


# SecurityValidator类已暂时移除，避免BaseValidator依赖
