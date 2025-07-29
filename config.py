"""
配置管理系统
统一管理所有配置项
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


@dataclass
class DatabaseConfig:
    """数据库配置"""
    db_path: str = "gtplanner.db"
    backup_enabled: bool = True
    backup_interval: int = 24  # 小时
    max_connections: int = 10


@dataclass
class CacheConfig:
    """缓存配置"""
    cache_dir: str = "cache"
    max_memory_size: int = 100
    default_ttl: int = 3600  # 秒
    cleanup_interval: int = 3600  # 秒


@dataclass
class LoggingConfig:
    """日志配置"""
    log_dir: str = "logs"
    log_level: str = "INFO"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class APIConfig:
    """API配置"""
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com"
    timeout: int = 30
    max_retries: int = 3


@dataclass
class WebConfig:
    """Web配置"""
    host: str = "localhost"
    port: int = 5000
    debug: bool = False
    threaded: bool = True


@dataclass
class SystemConfig:
    """系统配置"""
    # 核心配置
    knowledge_base_file: str = "gtplanner_knowledge_base.json"
    badcase_file: str = "gtplanner_badcases.json"
    
    # 性能配置
    max_concurrent_queries: int = 10
    query_timeout: int = 30
    
    # 功能配置
    auto_feedback_enabled: bool = True
    cache_enabled: bool = True
    database_enabled: bool = True
    
    # 安全配置
    max_query_length: int = 1000
    rate_limit_per_minute: int = 60


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.database = DatabaseConfig()
        self.cache = CacheConfig()
        self.logging = LoggingConfig()
        self.api = APIConfig()
        self.web = WebConfig()
        self.system = SystemConfig()
        
        self.load_config()
        self.load_environment_variables()
    
    def load_config(self) -> None:
        """从配置文件加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 更新各个配置类
                if 'database' in config_data:
                    for key, value in config_data['database'].items():
                        if hasattr(self.database, key):
                            setattr(self.database, key, value)
                
                if 'cache' in config_data:
                    for key, value in config_data['cache'].items():
                        if hasattr(self.cache, key):
                            setattr(self.cache, key, value)
                
                if 'logging' in config_data:
                    for key, value in config_data['logging'].items():
                        if hasattr(self.logging, key):
                            setattr(self.logging, key, value)
                
                if 'api' in config_data:
                    for key, value in config_data['api'].items():
                        if hasattr(self.api, key):
                            setattr(self.api, key, value)
                
                if 'web' in config_data:
                    for key, value in config_data['web'].items():
                        if hasattr(self.web, key):
                            setattr(self.web, key, value)
                
                if 'system' in config_data:
                    for key, value in config_data['system'].items():
                        if hasattr(self.system, key):
                            setattr(self.system, key, value)
                
            except Exception as e:
                print(f"加载配置文件失败: {e}")
    
    def load_environment_variables(self) -> None:
        """从环境变量加载配置"""
        # API配置
        if os.getenv('DEEPSEEK_API_KEY'):
            self.api.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        
        if os.getenv('DEEPSEEK_BASE_URL'):
            self.api.deepseek_base_url = os.getenv('DEEPSEEK_BASE_URL')
        
        # Web配置
        if os.getenv('WEB_HOST'):
            self.web.host = os.getenv('WEB_HOST')
        
        if os.getenv('WEB_PORT'):
            try:
                self.web.port = int(os.getenv('WEB_PORT'))
            except ValueError:
                pass
        
        # 数据库配置
        if os.getenv('DB_PATH'):
            self.database.db_path = os.getenv('DB_PATH')
        
        # 日志配置
        if os.getenv('LOG_LEVEL'):
            self.logging.log_level = os.getenv('LOG_LEVEL')
    
    def save_config(self) -> None:
        """保存配置到文件"""
        config_data = {
            'database': asdict(self.database),
            'cache': asdict(self.cache),
            'logging': asdict(self.logging),
            'api': asdict(self.api),
            'web': asdict(self.web),
            'system': asdict(self.system)
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get_config(self, section: str) -> Dict[str, Any]:
        """获取指定部分的配置"""
        if section == 'database':
            return asdict(self.database)
        elif section == 'cache':
            return asdict(self.cache)
        elif section == 'logging':
            return asdict(self.logging)
        elif section == 'api':
            return asdict(self.api)
        elif section == 'web':
            return asdict(self.web)
        elif section == 'system':
            return asdict(self.system)
        else:
            return {}
    
    def update_config(self, section: str, key: str, value: Any) -> bool:
        """更新配置"""
        try:
            if section == 'database' and hasattr(self.database, key):
                setattr(self.database, key, value)
            elif section == 'cache' and hasattr(self.cache, key):
                setattr(self.cache, key, value)
            elif section == 'logging' and hasattr(self.logging, key):
                setattr(self.logging, key, value)
            elif section == 'api' and hasattr(self.api, key):
                setattr(self.api, key, value)
            elif section == 'web' and hasattr(self.web, key):
                setattr(self.web, key, value)
            elif section == 'system' and hasattr(self.system, key):
                setattr(self.system, key, value)
            else:
                return False
            
            return True
        except Exception:
            return False
    
    def validate_config(self) -> Dict[str, list]:
        """验证配置"""
        errors = {}
        
        # 验证API配置
        if not self.api.deepseek_api_key:
            if 'api' not in errors:
                errors['api'] = []
            errors['api'].append("DeepSeek API key is required")
        
        # 验证数据库配置
        if self.database.max_connections <= 0:
            if 'database' not in errors:
                errors['database'] = []
            errors['database'].append("max_connections must be positive")
        
        # 验证缓存配置
        if self.cache.max_memory_size <= 0:
            if 'cache' not in errors:
                errors['cache'] = []
            errors['cache'].append("max_memory_size must be positive")
        
        return errors


# 全局配置实例
config_manager = ConfigManager()


def get_config(section: str) -> Dict[str, Any]:
    """获取配置的便捷函数"""
    return config_manager.get_config(section)


def update_config(section: str, key: str, value: Any) -> bool:
    """更新配置的便捷函数"""
    return config_manager.update_config(section, key, value)


def validate_config() -> Dict[str, list]:
    """验证配置的便捷函数"""
    return config_manager.validate_config() 