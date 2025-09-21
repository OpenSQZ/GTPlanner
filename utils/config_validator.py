"""
配置验证器

提供配置文件验证、环境变量检查和配置完整性验证功能。
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # fallback
    except ImportError:
        import toml as tomllib  # fallback
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConfigValidationResult:
    """配置验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    missing_required: List[str]
    invalid_values: List[str]


class ConfigValidator:
    """配置验证器"""
    
    # 必需的环境变量
    REQUIRED_ENV_VARS = [
        "LLM_API_KEY",
        "LLM_BASE_URL", 
        "LLM_MODEL"
    ]
    
    # 可选的环境变量
    OPTIONAL_ENV_VARS = [
        "JINA_API_KEY",
        "VECTOR_SERVICE_BASE_URL",
        "VECTOR_SERVICE_INDEX_NAME",
        "VECTOR_SERVICE_VECTOR_FIELD",
        "VECTOR_SERVICE_TIMEOUT"
    ]
    
    # 有效的日志级别
    VALID_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    # 配置文件路径
    CONFIG_FILES = ["settings.toml", "settings.local.toml", ".secrets.toml"]
    
    def __init__(self):
        self.validation_rules = {
            "logging.level": self._validate_log_level,
            "openai.log_level": self._validate_log_level,
            "logging.max_file_size": self._validate_positive_int,
            "logging.backup_count": self._validate_positive_int,
        }
    
    def validate_all(self) -> ConfigValidationResult:
        """验证所有配置"""
        errors = []
        warnings = []
        missing_required = []
        invalid_values = []
        
        # 验证环境变量
        env_result = self._validate_environment_variables()
        errors.extend(env_result["errors"])
        warnings.extend(env_result["warnings"])
        missing_required.extend(env_result["missing_required"])
        
        # 验证配置文件
        config_result = self._validate_config_files()
        errors.extend(config_result["errors"])
        warnings.extend(config_result["warnings"])
        invalid_values.extend(config_result["invalid_values"])
        
        # 验证配置值
        values_result = self._validate_config_values()
        errors.extend(values_result["errors"])
        invalid_values.extend(values_result["invalid_values"])
        
        is_valid = len(errors) == 0 and len(missing_required) == 0
        
        return ConfigValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            missing_required=missing_required,
            invalid_values=invalid_values
        )
    
    def _validate_environment_variables(self) -> Dict[str, List[str]]:
        """验证环境变量"""
        errors = []
        warnings = []
        missing_required = []
        
        # 检查必需的环境变量
        for var in self.REQUIRED_ENV_VARS:
            value = os.getenv(var)
            if not value:
                missing_required.append(f"缺少必需的环境变量: {var}")
            elif var == "LLM_API_KEY" and len(value) < 10:
                warnings.append(f"环境变量 {var} 的值可能无效（长度过短）")
            elif var == "LLM_BASE_URL" and not value.startswith(("http://", "https://")):
                errors.append(f"环境变量 {var} 必须是有效的URL")
        
        # 检查可选的环境变量
        for var in self.OPTIONAL_ENV_VARS:
            value = os.getenv(var)
            if value:
                if var.endswith("_URL") and not value.startswith(("http://", "https://")):
                    warnings.append(f"环境变量 {var} 应该是有效的URL")
                elif var.endswith("_TIMEOUT"):
                    try:
                        timeout = int(value)
                        if timeout <= 0:
                            warnings.append(f"环境变量 {var} 应该是正整数")
                    except ValueError:
                        warnings.append(f"环境变量 {var} 应该是数字")
        
        return {
            "errors": errors,
            "warnings": warnings,
            "missing_required": missing_required
        }
    
    def _validate_config_files(self) -> Dict[str, List[str]]:
        """验证配置文件"""
        errors = []
        warnings = []
        invalid_values = []
        
        for config_file in self.CONFIG_FILES:
            if Path(config_file).exists():
                try:
                    with open(config_file, 'rb') as f:
                        config = tomllib.load(f)
                    
                    # 验证TOML语法
                    logger.info(f"配置文件 {config_file} 语法正确")
                    
                    # 检查是否有明显的配置错误
                    self._check_config_content(config, config_file, errors, warnings, invalid_values)
                    
                except Exception as e:
                    errors.append(f"配置文件 {config_file} TOML语法错误: {e}")
                except Exception as e:
                    errors.append(f"读取配置文件 {config_file} 失败: {e}")
        
        return {
            "errors": errors,
            "warnings": warnings,
            "invalid_values": invalid_values
        }
    
    def _check_config_content(self, config: Dict, filename: str, errors: List[str], 
                            warnings: List[str], invalid_values: List[str]):
        """检查配置内容"""
        # 检查是否有拼写错误的配置项
        common_typos = {
            "DEBUGE": "DEBUG",
            "INFFO": "INFO",
            "WARRNING": "WARNING"
        }
        
        def check_nested_dict(d: Dict, path: str = ""):
            for key, value in d.items():
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, dict):
                    check_nested_dict(value, current_path)
                elif isinstance(value, str):
                    # 检查拼写错误
                    for typo, correct in common_typos.items():
                        if typo in value:
                            warnings.append(f"配置文件 {filename} 中 {current_path} 可能包含拼写错误: {typo} -> {correct}")
                    
                    # 检查日志级别
                    if "log_level" in key.lower() and value not in self.VALID_LOG_LEVELS:
                        invalid_values.append(f"配置文件 {filename} 中 {current_path} 的值 '{value}' 不是有效的日志级别")
        
        check_nested_dict(config)
    
    def _validate_config_values(self) -> Dict[str, List[str]]:
        """验证配置值"""
        errors = []
        invalid_values = []
        
        try:
            from utils.unified_config import get_config_manager
            config_manager = get_config_manager()
            
            # 验证OpenAI配置
            openai_config = config_manager.get_openai_config()
            if not openai_config.get("api_key"):
                errors.append("OpenAI API密钥未配置")
            
            if not openai_config.get("base_url"):
                errors.append("OpenAI Base URL未配置")
            
            if not openai_config.get("model"):
                errors.append("OpenAI模型未配置")
            
            # 验证日志配置
            log_config = config_manager.get_logging_config()
            log_level = log_config.get("level", "INFO")
            if log_level not in self.VALID_LOG_LEVELS:
                invalid_values.append(f"日志级别 '{log_level}' 无效")
            
        except Exception as e:
            errors.append(f"验证配置值时出错: {e}")
        
        return {
            "errors": errors,
            "invalid_values": invalid_values
        }
    
    def _validate_log_level(self, value: str) -> Tuple[bool, str]:
        """验证日志级别"""
        if value in self.VALID_LOG_LEVELS:
            return True, ""
        return False, f"无效的日志级别: {value}，有效值: {', '.join(self.VALID_LOG_LEVELS)}"
    
    def _validate_positive_int(self, value: Any) -> Tuple[bool, str]:
        """验证正整数"""
        try:
            int_value = int(value)
            if int_value > 0:
                return True, ""
            return False, "值必须是正整数"
        except (ValueError, TypeError):
            return False, "值必须是整数"
    
    def generate_config_template(self, output_path: str = "settings.template.toml"):
        """生成配置模板文件"""
        template = """# GTPlanner 配置模板
# 复制此文件为 settings.toml 并根据需要修改配置

[default]
debug = true

[default.logging]
level = "INFO"  # 有效值: DEBUG, INFO, WARNING, ERROR, CRITICAL
file_enabled = true
console_enabled = false
max_file_size = 10485760  # 10MB
backup_count = 5

[default.openai]
debug_enabled = true
log_requests = true
log_responses = true
log_level = "DEBUG"  # 有效值: DEBUG, INFO, WARNING, ERROR, CRITICAL
log_to_file = true
log_to_console = false

[default.llm]
# 使用环境变量配置，确保安全性
base_url = "@format {env[LLM_BASE_URL]}"
api_key = "@format {env[LLM_API_KEY]}"
model = "@format {env[LLM_MODEL]}"

[default.jina]
# 可选配置
api_key = "@format {env[JINA_API_KEY]}"
search_base_url = "https://s.jina.ai/"
web_base_url = "https://r.jina.ai/"

[default.vector_service]
# 可选配置
base_url = "@format {env[VECTOR_SERVICE_BASE_URL]}"
index_name = "@format {env[VECTOR_SERVICE_INDEX_NAME]}"
vector_field = "@format {env[VECTOR_SERVICE_VECTOR_FIELD]}"
timeout = "@format {env[VECTOR_SERVICE_TIMEOUT]}"
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(template)
        
        logger.info(f"配置模板已生成: {output_path}")


def validate_startup_config() -> bool:
    """启动时验证配置"""
    validator = ConfigValidator()
    result = validator.validate_all()
    
    if result.errors:
        logger.error("配置验证失败:")
        for error in result.errors:
            logger.error(f"  ❌ {error}")
    
    if result.missing_required:
        logger.error("缺少必需配置:")
        for missing in result.missing_required:
            logger.error(f"  ❌ {missing}")
    
    if result.warnings:
        logger.warning("配置警告:")
        for warning in result.warnings:
            logger.warning(f"  ⚠️ {warning}")
    
    if result.invalid_values:
        logger.error("无效配置值:")
        for invalid in result.invalid_values:
            logger.error(f"  ❌ {invalid}")
    
    if result.is_valid:
        logger.info("✅ 配置验证通过")
    else:
        logger.error("❌ 配置验证失败，请检查上述错误")
    
    return result.is_valid


if __name__ == "__main__":
    # 命令行工具
    import argparse
    
    parser = argparse.ArgumentParser(description="GTPlanner配置验证工具")
    parser.add_argument("--generate-template", action="store_true", help="生成配置模板文件")
    parser.add_argument("--validate", action="store_true", help="验证当前配置")
    
    args = parser.parse_args()
    
    if args.generate_template:
        validator = ConfigValidator()
        validator.generate_config_template()
        print("✅ 配置模板已生成: settings.template.toml")
    
    if args.validate or not any(vars(args).values()):
        # 默认执行验证
        is_valid = validate_startup_config()
        exit(0 if is_valid else 1)
