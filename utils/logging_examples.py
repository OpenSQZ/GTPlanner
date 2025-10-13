"""
日志和错误处理使用示例

展示如何在代码中使用增强的日志系统和自定义异常。
"""

from utils.enhanced_logger import get_logger
from utils.custom_exceptions import (
    ValidationError,
    SessionNotFoundError,
    LLMAPIError,
    ToolExecutionError,
    RateLimitExceededError,
)
from utils.sentry_integration import (
    SentryContext,
    add_breadcrumb,
    set_user,
    capture_exception,
)

# 获取日志记录器
logger = get_logger(__name__)


# ===== 示例1: 基础日志记录 =====

def example_basic_logging():
    """基础日志记录示例"""
    
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.critical("这是严重错误信息")


# ===== 示例2: 带上下文的日志 =====

def example_contextual_logging(session_id: str, user_id: str):
    """带上下文信息的日志记录"""
    
    # 获取带上下文的日志记录器
    context_logger = get_logger(
        __name__,
        session_id=session_id,
        user_id=user_id
    )
    
    context_logger.info("用户开始会话")
    context_logger.debug("处理用户请求", extra={
        "request_type": "planning",
        "language": "zh"
    })


# ===== 示例3: 异常处理 =====

def example_exception_handling():
    """异常处理示例"""
    
    try:
        # 模拟验证错误
        raise ValidationError(
            message="Invalid input format",
            field="user_input",
            details={"expected": "string", "got": "None"}
        )
    except ValidationError as e:
        logger.error(
            "验证失败",
            extra={
                "error_code": e.error_code.value,
                "field": e.details.get("field"),
            },
            exc_info=True
        )
        # 重新抛出或处理
        raise


# ===== 示例4: 自定义异常使用 =====

async def example_custom_exceptions(session_id: str):
    """自定义异常使用示例"""
    
    # Session不存在
    if not await check_session_exists(session_id):
        raise SessionNotFoundError(session_id)
    
    # LLM API错误
    try:
        result = await call_llm_api()
    except Exception as e:
        raise LLMAPIError(
            message="Failed to call LLM API",
            provider="OpenAI",
            details={"model": "gpt-4"},
            original_exception=e
        )
    
    # 工具执行错误
    try:
        result = await execute_tool("search", {"query": "test"})
    except Exception as e:
        raise ToolExecutionError(
            tool_name="search",
            message="Search failed",
            details={"query": "test"},
            original_exception=e
        )
    
    # 速率限制
    if await is_rate_limited():
        raise RateLimitExceededError(
            retry_after=60,
            details={"limit": 10, "window": "1 minute"}
        )


# ===== 示例5: Sentry集成 =====

def example_sentry_integration():
    """Sentry集成示例"""
    
    # 设置用户信息
    set_user(
        user_id="user123",
        username="john_doe",
        email="john@example.com"
    )
    
    # 添加面包屑
    add_breadcrumb(
        message="User started planning session",
        category="user_action",
        level="info",
        data={"session_id": "sess123"}
    )
    
    # 使用上下文管理器
    with SentryContext(
        transaction_name="process_planning_request",
        operation="planning",
        tags={"language": "zh", "user_type": "premium"},
        context={"session": {"id": "sess123", "type": "planning"}}
    ):
        # 业务逻辑
        process_user_request()


# ===== 示例6: 完整的错误处理流程 =====

async def example_complete_error_handling(session_id: str, user_input: str):
    """完整的错误处理流程示例"""
    
    # 获取带上下文的日志记录器
    request_logger = get_logger(
        __name__,
        session_id=session_id,
        request_id="req123"
    )
    
    try:
        # 记录开始
        request_logger.info(
            "开始处理请求",
            extra={"user_input_length": len(user_input)}
        )
        
        # 添加Sentry面包屑
        add_breadcrumb(
            message="Started processing request",
            category="processing",
            data={"session_id": session_id}
        )
        
        # 验证输入
        if not user_input or len(user_input) < 10:
            raise ValidationError(
                message="User input too short",
                field="user_input",
                details={
                    "min_length": 10,
                    "actual_length": len(user_input)
                }
            )
        
        # 检查会话
        if not await check_session_exists(session_id):
            raise SessionNotFoundError(session_id)
        
        # 处理请求
        result = await process_request(user_input)
        
        # 记录成功
        request_logger.info(
            "请求处理成功",
            extra={
                "result_length": len(result),
                "processing_time": 1.5
            }
        )
        
        return result
        
    except ValidationError as e:
        # 验证错误（用户错误，不需要发送到Sentry）
        request_logger.warning(
            f"验证错误: {e.message}",
            extra={"error_code": e.error_code.value}
        )
        raise
        
    except SessionNotFoundError as e:
        # Session错误（记录但不发送到Sentry）
        request_logger.error(
            f"Session不存在: {session_id}",
            extra={"error_code": e.error_code.value}
        )
        raise
        
    except LLMAPIError as e:
        # LLM错误（系统错误，发送到Sentry）
        request_logger.error(
            f"LLM API错误: {e.message}",
            extra={
                "error_code": e.error_code.value,
                "provider": e.details.get("provider")
            },
            exc_info=True
        )
        # 捕获到Sentry
        capture_exception(
            e,
            context={"session": {"id": session_id}},
            tags={"component": "llm", "provider": "openai"}
        )
        raise
        
    except Exception as e:
        # 未知错误（严重错误，必须发送到Sentry）
        request_logger.critical(
            f"未知错误: {str(e)}",
            extra={"exception_type": type(e).__name__},
            exc_info=True
        )
        # 捕获到Sentry
        capture_exception(
            e,
            context={
                "session": {"id": session_id},
                "request": {"input": user_input[:100]}
            },
            level="fatal"
        )
        raise


# ===== 模拟函数（实际使用时替换为真实实现） =====

async def check_session_exists(session_id: str) -> bool:
    """检查会话是否存在"""
    return True

async def call_llm_api():
    """调用LLM API"""
    return {"response": "test"}

async def execute_tool(name: str, args: dict):
    """执行工具"""
    return {"result": "success"}

async def is_rate_limited() -> bool:
    """检查是否被限流"""
    return False

def process_user_request():
    """处理用户请求"""
    pass

async def process_request(user_input: str):
    """处理请求"""
    return "处理结果"


# ===== 主函数 =====

if __name__ == "__main__":
    import asyncio
    
    # 设置日志
    from utils.enhanced_logger import setup_global_logger
    setup_global_logger(
        app_name="examples",
        log_level="DEBUG",
        enable_console=True,
        enable_file=False
    )
    
    # 运行示例
    print("=== 示例1: 基础日志 ===")
    example_basic_logging()
    
    print("\n=== 示例2: 带上下文日志 ===")
    example_contextual_logging("sess123", "user456")
    
    print("\n=== 示例3: 异常处理 ===")
    try:
        example_exception_handling()
    except ValidationError:
        print("捕获到验证错误")
    
    print("\n=== 示例6: 完整错误处理 ===")
    asyncio.run(example_complete_error_handling("sess123", "这是一个测试输入"))

