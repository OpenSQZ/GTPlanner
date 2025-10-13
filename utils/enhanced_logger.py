"""
增强的日志配置系统

提供结构化日志、多种日志格式、日志轮转等功能。
支持控制台输出、文件输出、JSON格式等。
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

try:
    from pythonjsonlogger import jsonlogger
    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False


class CustomJsonFormatter(logging.Formatter):
    """自定义JSON日志格式化器（不依赖pythonjsonlogger）"""
    
    def format(self, record: logging.LogRecord) -> str:
        import json
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加额外字段
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
            
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        # 添加自定义字段
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data
            
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        # 格式化消息
        formatted = super().format(record)
        
        # 重置 levelname
        record.levelname = levelname
        
        return formatted


class LoggerConfig:
    """日志配置管理器"""
    
    def __init__(
        self,
        app_name: str = "gtplanner",
        log_dir: Optional[str] = None,
        log_level: str = "INFO",
        enable_console: bool = True,
        enable_file: bool = True,
        enable_json: bool = False,
        enable_structured: bool = False,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        enable_rotation: str = "size",  # "size" or "time"
    ):
        """
        初始化日志配置
        
        Args:
            app_name: 应用名称
            log_dir: 日志目录（None则使用默认）
            log_level: 日志级别
            enable_console: 是否启用控制台输出
            enable_file: 是否启用文件输出
            enable_json: 是否使用JSON格式
            enable_structured: 是否使用structlog（需要安装structlog）
            max_file_size: 日志文件最大大小（字节）
            backup_count: 保留的备份文件数量
            enable_rotation: 日志轮转方式 ("size" 或 "time")
        """
        self.app_name = app_name
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_json = enable_json
        self.enable_structured = enable_structured
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.enable_rotation = enable_rotation
        
        # 设置日志目录
        if log_dir is None:
            self.log_dir = Path("logs")
        else:
            self.log_dir = Path(log_dir)
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志文件路径
        self.log_file = self.log_dir / f"{app_name}.log"
        self.error_log_file = self.log_dir / f"{app_name}_error.log"
        self.json_log_file = self.log_dir / f"{app_name}_json.log"
        
    def configure(self) -> logging.Logger:
        """配置并返回根日志记录器"""
        
        # 如果启用结构化日志
        if self.enable_structured and STRUCTLOG_AVAILABLE:
            return self._configure_structlog()
        
        # 标准日志配置
        return self._configure_standard_logging()
    
    def _configure_standard_logging(self) -> logging.Logger:
        """配置标准Python日志"""
        
        # 获取根日志记录器
        logger = logging.getLogger()
        logger.setLevel(self.log_level)
        
        # 清除现有处理器
        logger.handlers.clear()
        
        # 日志格式
        detailed_format = (
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "%(funcName)s:%(lineno)d | %(message)s"
        )
        simple_format = "%(asctime)s | %(levelname)-8s | %(message)s"
        
        # 1. 控制台处理器
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            
            # 使用彩色格式化器
            console_formatter = ColoredFormatter(
                detailed_format,
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # 2. 文件处理器（常规日志）
        if self.enable_file:
            if self.enable_rotation == "time":
                # 按时间轮转（每天）
                file_handler = TimedRotatingFileHandler(
                    self.log_file,
                    when="midnight",
                    interval=1,
                    backupCount=self.backup_count,
                    encoding="utf-8"
                )
            else:
                # 按大小轮转
                file_handler = RotatingFileHandler(
                    self.log_file,
                    maxBytes=self.max_file_size,
                    backupCount=self.backup_count,
                    encoding="utf-8"
                )
            
            file_handler.setLevel(self.log_level)
            file_formatter = logging.Formatter(
                detailed_format,
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        # 3. 错误日志文件处理器（仅ERROR及以上）
        if self.enable_file:
            error_handler = RotatingFileHandler(
                self.error_log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding="utf-8"
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            logger.addHandler(error_handler)
        
        # 4. JSON日志处理器
        if self.enable_json:
            json_handler = RotatingFileHandler(
                self.json_log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding="utf-8"
            )
            json_handler.setLevel(self.log_level)
            
            # 使用JSON格式化器
            if JSON_LOGGER_AVAILABLE:
                json_formatter = jsonlogger.JsonFormatter(
                    "%(timestamp)s %(level)s %(name)s %(message)s",
                    rename_fields={
                        "levelname": "level",
                        "asctime": "timestamp"
                    }
                )
            else:
                json_formatter = CustomJsonFormatter()
            
            json_handler.setFormatter(json_formatter)
            logger.addHandler(json_handler)
        
        return logger
    
    def _configure_structlog(self) -> logging.Logger:
        """配置structlog结构化日志"""
        
        # 配置标准logging作为后端
        logging.basicConfig(
            format="%(message)s",
            level=self.log_level,
            handlers=[]
        )
        
        # 添加处理器
        logger = logging.getLogger()
        logger.handlers.clear()
        
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            logger.addHandler(console_handler)
        
        if self.enable_file:
            file_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding="utf-8"
            )
            file_handler.setLevel(self.log_level)
            logger.addHandler(file_handler)
        
        # 配置structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer() if self.enable_json 
                    else structlog.dev.ConsoleRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        return structlog.get_logger(self.app_name)


class LoggerAdapter(logging.LoggerAdapter):
    """自定义日志适配器，用于添加上下文信息"""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """处理日志消息，添加额外的上下文"""
        
        # 从extra中提取信息
        extra = kwargs.get("extra", {})
        
        # 添加到日志记录中
        if self.extra:
            extra.update(self.extra)
        
        kwargs["extra"] = extra
        
        return msg, kwargs


def get_logger(
    name: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> logging.Logger:
    """
    获取日志记录器实例
    
    Args:
        name: 日志记录器名称
        session_id: 会话ID（可选）
        user_id: 用户ID（可选）
        request_id: 请求ID（可选）
    
    Returns:
        日志记录器实例
    """
    logger = logging.getLogger(name)
    
    # 添加上下文信息
    extra = {}
    if session_id:
        extra["session_id"] = session_id
    if user_id:
        extra["user_id"] = user_id
    if request_id:
        extra["request_id"] = request_id
    
    if extra:
        return LoggerAdapter(logger, extra)
    
    return logger


def configure_logging_from_env() -> logging.Logger:
    """从环境变量配置日志"""
    
    config = LoggerConfig(
        app_name=os.getenv("APP_NAME", "gtplanner"),
        log_dir=os.getenv("LOG_DIR", "logs"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        enable_console=os.getenv("LOG_CONSOLE", "true").lower() == "true",
        enable_file=os.getenv("LOG_FILE", "true").lower() == "true",
        enable_json=os.getenv("LOG_JSON", "false").lower() == "true",
        enable_structured=os.getenv("LOG_STRUCTURED", "false").lower() == "true",
        max_file_size=int(os.getenv("LOG_MAX_SIZE", str(10 * 1024 * 1024))),
        backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
        enable_rotation=os.getenv("LOG_ROTATION", "size"),
    )
    
    return config.configure()


# 全局日志记录器实例
_global_logger: Optional[logging.Logger] = None


def setup_global_logger(**kwargs) -> logging.Logger:
    """设置全局日志记录器"""
    global _global_logger
    
    config = LoggerConfig(**kwargs)
    _global_logger = config.configure()
    
    return _global_logger


def get_global_logger() -> logging.Logger:
    """获取全局日志记录器"""
    global _global_logger
    
    if _global_logger is None:
        _global_logger = configure_logging_from_env()
    
    return _global_logger


# 便捷函数
def debug(msg: str, **kwargs):
    """记录DEBUG级别日志"""
    get_global_logger().debug(msg, **kwargs)


def info(msg: str, **kwargs):
    """记录INFO级别日志"""
    get_global_logger().info(msg, **kwargs)


def warning(msg: str, **kwargs):
    """记录WARNING级别日志"""
    get_global_logger().warning(msg, **kwargs)


def error(msg: str, **kwargs):
    """记录ERROR级别日志"""
    get_global_logger().error(msg, **kwargs)


def critical(msg: str, **kwargs):
    """记录CRITICAL级别日志"""
    get_global_logger().critical(msg, **kwargs)


def exception(msg: str, **kwargs):
    """记录异常信息"""
    get_global_logger().exception(msg, **kwargs)

