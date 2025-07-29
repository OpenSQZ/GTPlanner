"""
日志配置系统
提供统一的日志管理功能
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class LogConfig:
    """日志配置类"""
    
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.log_level = getattr(logging, log_level.upper())
        self.setup_logging()
    
    def setup_logging(self) -> None:
        """设置日志配置"""
        # 创建根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # 清除现有的处理器
        root_logger.handlers.clear()
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # 文件处理器 - 普通日志
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "gtplanner.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # 错误日志处理器
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "error.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s\n'
            'Exception: %(exc_info)s\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_handler)
        
        # 查询日志处理器
        query_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "queries.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        query_handler.setLevel(logging.INFO)
        query_formatter = logging.Formatter(
            '%(asctime)s - QUERY - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        query_handler.setFormatter(query_formatter)
        
        # 创建查询日志记录器
        query_logger = logging.getLogger('query')
        query_logger.setLevel(logging.INFO)
        query_logger.addHandler(query_handler)
        query_logger.propagate = False
        
        logging.info("日志系统初始化完成")
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        return logging.getLogger(name)
    
    def log_query(self, user_id: str, question: str, answer: str, 
                  feedback: str, processing_time: float) -> None:
        """记录查询日志"""
        query_logger = logging.getLogger('query')
        query_logger.info(
            f"User: {user_id} | Question: {question[:100]}... | "
            f"Feedback: {feedback} | Time: {processing_time:.2f}s"
        )
    
    def log_error(self, error: Exception, context: str = "") -> None:
        """记录错误日志"""
        logging.error(f"Error in {context}: {error}", exc_info=True)
    
    def log_performance(self, operation: str, duration: float, 
                       details: Optional[dict] = None) -> None:
        """记录性能日志"""
        perf_logger = logging.getLogger('performance')
        message = f"Operation: {operation} | Duration: {duration:.3f}s"
        if details:
            message += f" | Details: {details}"
        perf_logger.info(message)


# 全局日志配置实例
log_config = LogConfig()


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器的便捷函数"""
    return log_config.get_logger(name)


def log_query(user_id: str, question: str, answer: str, 
              feedback: str, processing_time: float) -> None:
    """记录查询日志的便捷函数"""
    log_config.log_query(user_id, question, answer, feedback, processing_time)


def log_error(error: Exception, context: str = "") -> None:
    """记录错误日志的便捷函数"""
    log_config.log_error(error, context)


def log_performance(operation: str, duration: float, 
                   details: Optional[dict] = None) -> None:
    """记录性能日志的便捷函数"""
    log_config.log_performance(operation, duration, details) 