"""
日志配置模块

提供统一的日志配置和管理，支持文件输出、控制台输出、日志轮转等功能。
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from dynaconf import Dynaconf


class LoggerConfig:
    """日志配置类"""
    
    def __init__(
        self,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        log_dir: str = "logs",
        console_output: bool = True,
        file_output: bool = True,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        log_format: Optional[str] = None
    ):
        """
        初始化日志配置
        
        Args:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: 日志文件名，如果为None则自动生成
            log_dir: 日志目录
            console_output: 是否输出到控制台
            file_output: 是否输出到文件
            max_file_size: 单个日志文件最大大小（字节）
            backup_count: 保留的备份文件数量
            log_format: 日志格式，如果为None则使用默认格式
        """
        self.log_level = log_level.upper()
        self.log_dir = Path(log_dir)
        self.console_output = console_output
        self.file_output = file_output
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        
        # 确保日志目录存在
        self.log_dir.mkdir(exist_ok=True)
        
        # 设置日志文件名
        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d")
            self.log_file = self.log_dir / f"gtplanner_{timestamp}.log"
        else:
            self.log_file = self.log_dir / log_file
        
        # 设置日志格式
        if log_format is None:
            self.log_format = (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "%(filename)s:%(lineno)d - %(message)s"
            )
        else:
            self.log_format = log_format
    
    def get_level(self) -> int:
        """获取日志级别对应的数值"""
        return getattr(logging, self.log_level, logging.INFO)


class LoggerManager:
    """日志管理器"""
    
    def __init__(self):
        self._loggers: Dict[str, logging.Logger] = {}
        self._config: Optional[LoggerConfig] = None
        self._initialized = False
    
    def initialize(self, config: LoggerConfig) -> None:
        """
        初始化日志系统

        Args:
            config: 日志配置对象
        """
        self._config = config
        self._initialized = True

        # 设置根日志级别
        root_logger = logging.getLogger()
        root_logger.setLevel(config.get_level())

        # 如果禁用控制台输出，清除所有现有的控制台处理器
        if not config.console_output:
            # 清除根日志器的所有StreamHandler
            for handler in root_logger.handlers[:]:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    root_logger.removeHandler(handler)

            # 禁用根日志器的默认行为
            root_logger.handlers.clear()
            root_logger.addHandler(logging.NullHandler())
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志器

        Args:
            name: 日志器名称

        Returns:
            配置好的日志器
        """
        if not self._initialized:
            # 从配置文件加载配置并初始化
            config = load_logging_config_from_settings()
            self.initialize(config)

        # 总是重新创建日志器以确保使用最新配置
        self._loggers[name] = self._create_logger(name)

        return self._loggers[name]
    
    def _create_logger(self, name: str) -> logging.Logger:
        """
        创建并配置日志器

        Args:
            name: 日志器名称

        Returns:
            配置好的日志器
        """
        logger = logging.getLogger(name)
        logger.setLevel(self._config.get_level())

        # 清除现有的处理器
        logger.handlers.clear()

        # 创建格式化器
        formatter = logging.Formatter(self._config.log_format)

        # 添加控制台处理器（只有在明确启用时才添加）
        if self._config.console_output is True:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self._config.get_level())
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # 添加文件处理器（带轮转）
        if self._config.file_output:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=self._config.log_file,
                maxBytes=self._config.max_file_size,
                backupCount=self._config.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self._config.get_level())
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # 防止日志传播到父日志器（重要：防止输出到根日志器）
        logger.propagate = False

        # 确保根日志器也不会输出到控制台
        root_logger = logging.getLogger()
        if not self._config.console_output:
            # 移除根日志器的控制台处理器
            for handler in root_logger.handlers[:]:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    root_logger.removeHandler(handler)

        return logger


def load_logging_config_from_settings() -> LoggerConfig:
    """从settings.toml加载日志配置"""
    try:
        settings = Dynaconf(
            settings_files=["settings.toml", "settings.local.toml", ".secrets.toml"],
            environments=True,
            env_switcher="ENV_FOR_DYNACONF",
            load_dotenv=True,
        )

        # 从配置文件读取日志设置
        log_level = settings.get("logging.level", "INFO")
        console_enabled = settings.get("logging.console_enabled", True)
        file_enabled = settings.get("logging.file_enabled", True)
        max_file_size = settings.get("logging.max_file_size", 10 * 1024 * 1024)
        backup_count = settings.get("logging.backup_count", 5)

        return LoggerConfig(
            log_level=log_level,
            console_output=console_enabled,
            file_output=file_enabled,
            max_file_size=max_file_size,
            backup_count=backup_count
        )
    except Exception as e:
        # 如果加载配置失败，返回默认配置
        print(f"警告: 加载日志配置失败，使用默认配置: {e}")
        return LoggerConfig(console_output=False)  # 默认不输出到控制台


# 全局日志管理器实例
_logger_manager = LoggerManager()


def initialize_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs",
    console_output: bool = True,
    file_output: bool = True,
    max_file_size: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    log_format: Optional[str] = None
) -> None:
    """
    初始化全局日志系统

    Args:
        log_level: 日志级别
        log_file: 日志文件名
        log_dir: 日志目录
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
        max_file_size: 单个日志文件最大大小
        backup_count: 保留的备份文件数量
        log_format: 日志格式
    """
    # 如果禁用控制台输出，先彻底清理所有现有的控制台处理器
    if not console_output:
        # 获取所有现有的日志器并清理它们的控制台处理器
        for name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(name)
            for handler in logger.handlers[:]:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    logger.removeHandler(handler)

        # 清理根日志器
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                root_logger.removeHandler(handler)

    config = LoggerConfig(
        log_level=log_level,
        log_file=log_file,
        log_dir=log_dir,
        console_output=console_output,
        file_output=file_output,
        max_file_size=max_file_size,
        backup_count=backup_count,
        log_format=log_format
    )
    _logger_manager.initialize(config)


def get_logger(name: str) -> logging.Logger:
    """
    获取日志器的便捷函数
    
    Args:
        name: 日志器名称
        
    Returns:
        配置好的日志器
    """
    return _logger_manager.get_logger(name)


# 预定义的日志器
def get_openai_logger() -> logging.Logger:
    """获取OpenAI客户端专用日志器"""
    return get_logger("openai_client")


def get_api_logger() -> logging.Logger:
    """获取API调用专用日志器"""
    return get_logger("api_calls")


def get_system_logger() -> logging.Logger:
    """获取系统日志器"""
    return get_logger("system")
