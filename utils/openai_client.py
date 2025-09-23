"""
OpenAI SDK封装层

提供统一的OpenAI SDK异步接口，集成配置管理、错误处理、重试机制和Function Calling功能。
"""

import asyncio
import os
import time
from typing import Dict, List, Any, Optional, AsyncIterator, Callable, TypedDict
import copy
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from utils.logger_config import get_openai_logger

try:
    from dynaconf import Dynaconf
    DYNACONF_AVAILABLE = True
except ImportError:
    DYNACONF_AVAILABLE = False


class Message(TypedDict):
    """消息类型定义"""
    role: str
    content: str


class ToolCallTagFilter:
    """
    工具调用标签过滤器和转换器（状态机模式）

    使用状态机模式处理跨chunk的工具调用标签分割情况，
    支持标签被任意分割的边界情况（如 chunk1="<tool_", chunk2="call>{"name""）
    """

    def __init__(self):
        # 状态机状态
        self.state = "NORMAL"  # NORMAL, COLLECTING_START_TAG, IN_TOOL_CALL, COLLECTING_END_TAG

        # 标签定义
        self.start_tag = "<tool_call>"
        self.end_tag = "</tool_call>"

        # 标签收集缓冲区
        self.tag_buffer = ""
        self.tag_target = ""

        # 内容缓冲区
        self.content_buffer = ""
        self.tool_call_content = ""

        # 输出缓冲区
        self.output_buffer = ""

        # 提取的工具调用
        self.extracted_tool_calls = []

    def process_chunk(self, content: str) -> str:
        """
        处理流式内容块，使用状态机模式过滤工具调用标签

        Args:
            content: 原始内容块

        Returns:
            过滤后的可显示内容
        """
        if not content:
            return ""

        output = ""

        for char in content:
            if self.state == "NORMAL":
                output += self._process_normal_char(char)
            elif self.state == "COLLECTING_START_TAG":
                output += self._process_start_tag_char(char)
            elif self.state == "IN_TOOL_CALL":
                self._process_tool_call_char(char)
            elif self.state == "COLLECTING_END_TAG":
                self._process_end_tag_char(char)

        return output

    def _process_normal_char(self, char: str) -> str:
        """处理正常状态下的字符"""
        if char == '<':
            # 开始收集开始标签
            self.state = "COLLECTING_START_TAG"
            self.tag_buffer = '<'
            self.tag_target = self.start_tag
            return ""  # 不输出，等待确认是否为工具调用标签
        else:
            return char

    def _process_start_tag_char(self, char: str) -> str:
        """处理开始标签收集状态下的字符"""
        self.tag_buffer += char

        if len(self.tag_buffer) <= len(self.tag_target):
            # 检查是否匹配目标标签
            if self.tag_buffer == self.tag_target[:len(self.tag_buffer)]:
                if self.tag_buffer == self.tag_target:
                    # 完整匹配开始标签
                    self.state = "IN_TOOL_CALL"
                    self.tool_call_content = ""
                    self.tag_buffer = ""
                    return ""  # 不输出标签
                else:
                    # 部分匹配，继续收集
                    return ""
            else:
                # 不匹配，输出缓冲的内容并回到正常状态
                output = self.tag_buffer
                self.state = "NORMAL"
                self.tag_buffer = ""
                return output
        else:
            # 超出标签长度，不匹配，输出缓冲的内容并回到正常状态
            output = self.tag_buffer
            self.state = "NORMAL"
            self.tag_buffer = ""
            return output

    def _process_tool_call_char(self, char: str):
        """处理工具调用内容状态下的字符"""
        if char == '<':
            # 可能是结束标签的开始
            self.state = "COLLECTING_END_TAG"
            self.tag_buffer = '<'
            self.tag_target = self.end_tag
        else:
            self.tool_call_content += char

    def _process_end_tag_char(self, char: str):
        """处理结束标签收集状态下的字符"""
        self.tag_buffer += char

        if len(self.tag_buffer) <= len(self.tag_target):
            # 检查是否匹配目标标签
            if self.tag_buffer == self.tag_target[:len(self.tag_buffer)]:
                if self.tag_buffer == self.tag_target:
                    # 完整匹配结束标签，完成工具调用提取
                    self._parse_and_store_tool_call(self.tool_call_content)
                    self.state = "NORMAL"
                    self.tag_buffer = ""
                    self.tool_call_content = ""
                # 部分匹配，继续收集
            else:
                # 不匹配，将缓冲的内容加入工具调用内容，继续收集工具调用
                self.tool_call_content += self.tag_buffer
                self.state = "IN_TOOL_CALL"
                self.tag_buffer = ""
        else:
            # 超出标签长度，不匹配，将缓冲的内容加入工具调用内容
            self.tool_call_content += self.tag_buffer
            self.state = "IN_TOOL_CALL"
            self.tag_buffer = ""

    def finalize(self) -> str:
        """
        完成处理，返回剩余的可显示内容

        Returns:
            剩余的可显示内容
        """
        output = ""

        # 处理未完成的状态
        if self.state == "COLLECTING_START_TAG":
            # 未完成的开始标签收集，输出缓冲的内容
            output += self.tag_buffer
        elif self.state == "IN_TOOL_CALL":
            # 未完成的工具调用，不输出（工具调用不完整）
            pass
        elif self.state == "COLLECTING_END_TAG":
            # 未完成的结束标签收集，将缓冲内容作为工具调用内容的一部分
            # 但由于工具调用未完成，不输出
            pass

        # 重置状态
        self.state = "NORMAL"
        self.tag_buffer = ""
        self.tool_call_content = ""

        return output

    def _parse_and_store_tool_call(self, tool_call_content: str) -> None:
        """
        解析工具调用内容并存储为标准格式

        Args:
            tool_call_content: 工具调用的JSON内容
        """
        import json
        import uuid

        try:
            # 解析JSON内容
            tool_call_data = json.loads(tool_call_content)

            # 验证必需字段
            if "name" not in tool_call_data:
                return

            # 生成唯一的call_id
            call_id = f"call_{uuid.uuid4().hex[:8]}"

            # 确保arguments是字符串格式
            arguments = tool_call_data.get("arguments", {})
            if isinstance(arguments, dict):
                arguments_str = json.dumps(arguments, ensure_ascii=False)
            else:
                arguments_str = str(arguments)

            # 创建标准格式的工具调用
            standard_tool_call = {
                "id": call_id,
                "type": "function",
                "function": {
                    "name": tool_call_data["name"],
                    "arguments": arguments_str
                }
            }

            self.extracted_tool_calls.append(standard_tool_call)

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # 解析失败，忽略这个工具调用
            pass

    def get_extracted_tool_calls(self) -> list:
        """
        获取提取的工具调用列表

        Returns:
            标准格式的工具调用列表
        """
        return self.extracted_tool_calls.copy()




class SimpleOpenAIConfig:
    """简化的OpenAI配置类"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        timeout: float = 120.0,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        log_requests: bool = True,
        log_responses: bool = True,
        function_calling_enabled: bool = True,
        tool_choice: str = "auto",
        # 新增：细粒度重试配置
        retry_config: Optional[Dict[str, Any]] = None,
    ):
        # 尝试从 settings.toml 加载配置
        settings = self._load_settings()

        self.api_key = api_key or self._get_setting(settings, "llm.api_key") or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or self._get_setting(settings, "llm.base_url") or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = self._get_setting(settings, "llm.model") or os.getenv("OPENAI_MODEL", model)
        self.temperature = self._get_setting(settings, "llm.temperature", temperature)
        self.max_tokens = self._get_setting(settings, "llm.max_tokens", max_tokens)
        self.timeout = self._get_setting(settings, "llm.timeout", timeout)
        self.max_retries = self._get_setting(settings, "llm.max_retries", max_retries)
        self.retry_delay = self._get_setting(settings, "llm.retry_delay", retry_delay)
        self.log_requests = self._get_setting(settings, "llm.log_requests", log_requests)
        self.log_responses = self._get_setting(settings, "llm.log_responses", log_responses)
        self.function_calling_enabled = self._get_setting(settings, "llm.function_calling_enabled", function_calling_enabled)
        self.tool_choice = self._get_setting(settings, "llm.tool_choice", tool_choice)
        
        # 新增：细粒度重试配置
        self.retry_config = retry_config or self._get_setting(settings, "llm.retry_config", self._get_default_retry_config())

        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or configure llm.api_key in settings.toml.")

    def _load_settings(self):
        """加载 Dynaconf 设置"""
        if not DYNACONF_AVAILABLE:
            return None

        try:
            return Dynaconf(
                settings_files=["settings.toml", "settings.local.toml", ".secrets.toml"],
                environments=True,
                env_switcher="ENV_FOR_DYNACONF",
                load_dotenv=True,
            )
        except Exception:
            return None

    def _get_setting(self, settings, key: str, default: Any = None) -> Any:
        """从设置中获取值"""
        if settings is None:
            return default

        try:
            return settings.get(key, default)
        except Exception:
            return default

    def to_openai_client_kwargs(self) -> Dict[str, Any]:
        """转换为OpenAI客户端初始化参数"""
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }

    def to_chat_completion_kwargs(self) -> Dict[str, Any]:
        """转换为chat completion调用参数"""
        kwargs = {
            "model": self.model,
            "temperature": self.temperature,
        }

        if self.max_tokens:
            kwargs["max_tokens"] = self.max_tokens

        return kwargs

    def _get_default_retry_config(self) -> Dict[str, Any]:
        """获取默认的重试配置"""
        return {
            # 不同错误类型的最大重试次数
            "max_retries_by_error_type": {
                "rate_limit": 5,      # 速率限制错误：最多重试5次
                "timeout": 3,         # 超时错误：最多重试3次  
                "network": 3,         # 网络错误：最多重试3次
                "server_error": 2,     # 服务器错误：最多重试2次
                "default": 3          # 默认重试次数
            },
            # 不同错误类型的初始延迟（秒）
            "base_delay_by_error_type": {
                "rate_limit": 5.0,    # 速率限制错误：初始延迟5秒
                "timeout": 2.0,       # 超时错误：初始延迟2秒
                "network": 1.0,       # 网络错误：初始延迟1秒
                "server_error": 3.0,  # 服务器错误：初始延迟3秒
                "default": 2.0        # 默认初始延迟
            },
            # 最大延迟时间（秒）
            "max_delay": 60.0,
            # 是否启用jitter（随机抖动）
            "enable_jitter": True,
            # jitter范围（0.0-1.0，表示±百分比）
            "jitter_range": 0.25,
            # 可重试的错误类型模式
            "retryable_error_patterns": {
                "rate_limit": ["rate_limit", "429", "quota", "limit"],
                "timeout": ["timeout", "timed out", "time out"],
                "network": ["connection", "network", "dns", "ssl", "socket"],
                "server_error": ["server_error", "500", "502", "503", "504", "internal"]
            }
        }


class OpenAIClientError(Exception):
    """OpenAI客户端错误基类"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None, 
                 error_type: str = "unknown", request_info: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.original_error = original_error
        self.error_type = error_type
        self.request_info = request_info or {}
        self.timestamp = time.time()
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于序列化和日志记录"""
        return {
            "message": str(self),
            "error_type": self.error_type,
            "original_error": str(self.original_error) if self.original_error else None,
            "request_info": self.request_info,
            "timestamp": self.timestamp
        }


class OpenAIRateLimitError(OpenAIClientError):
    """API速率限制错误"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None, 
                 request_info: Optional[Dict[str, Any]] = None, 
                 retry_after: Optional[float] = None):
        super().__init__(message, original_error, "rate_limit", request_info)
        self.retry_after = retry_after
        
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["retry_after"] = self.retry_after
        return result


class OpenAITimeoutError(OpenAIClientError):
    """API超时错误"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None, 
                 request_info: Optional[Dict[str, Any]] = None):
        super().__init__(message, original_error, "timeout", request_info)


class OpenAIRetryableError(OpenAIClientError):
    """可重试的API错误"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None, 
                 request_info: Optional[Dict[str, Any]] = None, 
                 error_type: str = "retryable"):
        super().__init__(message, original_error, error_type, request_info)


class RetryManager:
    """重试管理器"""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, 
                 retry_config: Optional[Dict[str, Any]] = None, client: Optional[Any] = None):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.retry_config = retry_config or {}
        self.client = client  # OpenAIClient实例引用
        
        # 合并默认配置
        self._merge_default_config()

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        执行函数并在失败时重试

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except Exception as e:
                last_error = e

                # 检查是否应该重试
                if not self._should_retry(e, attempt):
                    break

                # 分类错误类型
                error_type = self._classify_error_type(e)
                
                # 计算延迟时间（基于错误类型）
                delay = self._calculate_delay(attempt, error_type)

                # 使用日志记录重试信息
                from utils.logger_config import get_logger
                logger = get_logger("retry_manager")
                logger.warning(f"⚠️ API调用失败 (尝试 {attempt + 1}/{self._get_max_retries_for_error_type(error_type)}): {e}")
                logger.info(f"🔄 错误类型: {error_type}, 等待 {delay:.1f}秒后重试...")

                # 更新重试统计（如果可用）
                self._update_retry_stats(error_type, False)

                await asyncio.sleep(delay)

        # 所有重试都失败了
        raise last_error

    def _merge_default_config(self) -> None:
        """合并默认配置"""
        default_config = {
            "max_retries_by_error_type": {
                "rate_limit": 5,
                "timeout": 3,
                "network": 3,
                "server_error": 2,
                "default": 3
            },
            "base_delay_by_error_type": {
                "rate_limit": 5.0,
                "timeout": 2.0,
                "network": 1.0,
                "server_error": 3.0,
                "default": 2.0
            },
            "max_delay": 60.0,
            "enable_jitter": True,
            "jitter_range": 0.25,
            "retryable_error_patterns": {
                "rate_limit": ["rate_limit", "429", "quota", "limit"],
                "timeout": ["timeout", "timed out", "time out"],
                "network": ["connection", "network", "dns", "ssl", "socket"],
                "server_error": ["server_error", "500", "502", "503", "504", "internal"]
            }
        }
        
        # 深度合并配置
        for key, default_value in default_config.items():
            if key not in self.retry_config:
                self.retry_config[key] = default_value
            elif isinstance(default_value, dict) and isinstance(self.retry_config[key], dict):
                # 字典类型的深度合并
                for sub_key, sub_default in default_value.items():
                    if sub_key not in self.retry_config[key]:
                        self.retry_config[key][sub_key] = sub_default

    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """
        判断是否应该重试

        Args:
            error: 错误对象
            attempt: 当前尝试次数

        Returns:
            是否应该重试
        """
        # 获取错误类型
        error_type = self._classify_error_type(error)
        
        # 根据错误类型获取最大重试次数
        max_retries_for_error = self._get_max_retries_for_error_type(error_type)
        
        if attempt >= max_retries_for_error:
            return False

        # 检查错误是否可重试
        return self._is_retryable_error_type(error_type)

    def _classify_error_type(self, error: Exception) -> str:
        """
        分类错误类型

        Args:
            error: 错误对象

        Returns:
            错误类型字符串
        """
        error_str = str(error).lower()
        
        # 检查配置中的错误类型模式
        patterns = self.retry_config.get("retryable_error_patterns", {})
        
        for error_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if pattern.lower() in error_str:
                    return error_type
        
        # 默认错误类型
        return "default"

    def _get_max_retries_for_error_type(self, error_type: str) -> int:
        """
        根据错误类型获取最大重试次数

        Args:
            error_type: 错误类型

        Returns:
            最大重试次数
        """
        max_retries_config = self.retry_config.get("max_retries_by_error_type", {})
        return max_retries_config.get(error_type, max_retries_config.get("default", self.max_retries))

    def _is_retryable_error_type(self, error_type: str) -> bool:
        """
        检查错误类型是否可重试

        Args:
            error_type: 错误类型

        Returns:
            是否可重试
        """
        # 所有在配置中的错误类型都是可重试的
        max_retries_config = self.retry_config.get("max_retries_by_error_type", {})
        return error_type in max_retries_config and max_retries_config[error_type] > 0

    def _calculate_delay(self, attempt: int, error_type: str = "default") -> float:
        """
        计算重试延迟时间（指数退避 + 随机抖动）

        Args:
            attempt: 当前尝试次数
            error_type: 错误类型

        Returns:
            延迟时间（秒）
        """
        import random

        # 根据错误类型获取基础延迟
        base_delay_config = self.retry_config.get("base_delay_by_error_type", {})
        base_delay = base_delay_config.get(error_type, base_delay_config.get("default", self.base_delay))

        # 指数退避
        delay = base_delay * (2 ** attempt)

        # 应用最大延迟限制
        max_delay = self.retry_config.get("max_delay", 60.0)
        delay = min(delay, max_delay)

        # 添加随机抖动（如果启用）
        if self.retry_config.get("enable_jitter", True):
            jitter_range = self.retry_config.get("jitter_range", 0.25)
            jitter = delay * jitter_range * (random.random() * 2 - 1)
            delay += jitter

        return max(0.1, delay)

    def _update_retry_stats(self, error_type: str, success: bool) -> None:
        """
        更新重试统计信息

        Args:
            error_type: 错误类型
            success: 重试是否成功
        """
        if self.client and hasattr(self.client, 'stats'):
            retry_stats = self.client.stats.get("retry_stats", {})
            
            # 更新总重试次数
            retry_stats["total_retries"] = retry_stats.get("total_retries", 0) + 1
            
            # 更新成功/失败重试次数
            if success:
                retry_stats["successful_retries"] = retry_stats.get("successful_retries", 0) + 1
            else:
                retry_stats["failed_retries"] = retry_stats.get("failed_retries", 0) + 1
            
            # 更新按错误类型的重试次数
            retries_by_type = retry_stats.get("retries_by_error_type", {})
            retries_by_type[error_type] = retries_by_type.get(error_type, 0) + 1

class OpenAIClient:
    """OpenAI SDK封装客户端"""

    def __init__(self, config: Optional[SimpleOpenAIConfig] = None):
        """
        初始化OpenAI客户端

        Args:
            config: OpenAI配置对象，如果为None则使用默认配置
        """
        self.config = config or SimpleOpenAIConfig()

        # 获取日志器（会自动初始化日志系统）
        self.logger = get_openai_logger()

        # 创建异步客户端
        client_kwargs = self.config.to_openai_client_kwargs()
        self.async_client = AsyncOpenAI(**client_kwargs)

        # 创建重试管理器
        self.retry_manager = RetryManager(
            max_retries=self.config.max_retries,
            base_delay=self.config.retry_delay,
            retry_config=self.config.retry_config,
            client=self  # 传递自身引用用于统计
        )

        # 性能统计
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_time": 0.0,
            # 新增：详细的错误统计
            "error_stats": {
                "rate_limit": 0,
                "timeout": 0,
                "network": 0,
                "server_error": 0,
                "bad_request": 0,
                "authentication": 0,
                "permission": 0,
                "not_found": 0,
                "unknown": 0
            },
            # 新增：延迟统计
            "latency_stats": {
                "min": float('inf'),
                "max": 0.0,
                "avg": 0.0,
                "total_count": 0,
                "sum": 0.0
            },
            # 新增：重试统计
            "retry_stats": {
                "total_retries": 0,
                "successful_retries": 0,
                "failed_retries": 0,
                "retries_by_error_type": {
                    "rate_limit": 0,
                    "timeout": 0,
                    "network": 0,
                    "server_error": 0,
                    "default": 0
                }
            }
        }


        # 记录初始化日志
        self.logger.info(f"OpenAI客户端初始化完成 - 模型: {self.config.model}, 基础URL: {self.config.base_url}")

    def _prepare_messages(
        self,
        messages: Optional[List[Message]] = None,
        system_prompt: Optional[str] = None
    ) -> List[Message]:
        """
        准备消息列表，统一处理系统提示词和全局系统提示词

        Args:
            messages: 原始消息列表
            system_prompt: 系统提示词

        Returns:
            准备好的消息列表
        """
        prepared_messages = []

        # 添加自定义系统提示词
        if system_prompt:
            prepared_messages.append({"role": "system", "content": system_prompt})

        # 添加对话消息
        if messages:
            prepared_messages.extend(messages)

        return prepared_messages

    def _prepare_request_params(
        self,
        messages: Optional[List[Message]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        准备API请求参数

        Args:
            messages: 消息列表
            system_prompt: 系统提示词
            tools: 工具列表
            stream: 是否流式响应
            **kwargs: 其他参数

        Returns:
            准备好的请求参数
        """
        # 准备消息
        prepared_messages = self._prepare_messages(messages, system_prompt)

        # 合并配置参数
        params = self.config.to_chat_completion_kwargs()

        # 过滤掉内部参数，避免传递给OpenAI API
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['filter_tool_tags']}
        params.update(filtered_kwargs)
        params["messages"] = prepared_messages

        if stream:
            params["stream"] = True

        # 添加工具支持
        if tools and self.config.function_calling_enabled:
            params["tools"] = tools
            if "tool_choice" not in params:
                params["tool_choice"] = self.config.tool_choice

        return params

    def _update_success_stats(self, response: Any, latency: Optional[float] = None) -> None:
        """更新成功统计信息"""
        self.stats["successful_requests"] += 1
        if hasattr(response, 'usage') and response.usage:
            self.stats["total_tokens"] += response.usage.total_tokens
        
        # 更新延迟统计
        if latency is not None:
            self._update_latency_stats(latency)

    def _update_latency_stats(self, latency: float) -> None:
        """更新延迟统计信息"""
        stats = self.stats["latency_stats"]
        stats["min"] = min(stats["min"], latency)
        stats["max"] = max(stats["max"], latency)
        stats["total_count"] += 1
        stats["sum"] += latency
        stats["avg"] = stats["sum"] / stats["total_count"]

    def _update_failure_stats(self, error: Optional[OpenAIClientError] = None) -> None:
        """更新失败统计信息"""
        self.stats["failed_requests"] += 1
        
        # 记录详细的错误类型统计
        if error and hasattr(error, 'error_type'):
            error_type = error.error_type
            if error_type in self.stats["error_stats"]:
                self.stats["error_stats"][error_type] += 1
            else:
                self.stats["error_stats"]["unknown"] += 1



    async def chat_completion(
        self,
        messages: Optional[List[Message]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> ChatCompletion:
        """
        异步聊天完成调用

        Args:
            messages: 消息列表
            system_prompt: 系统提示词（可选）
            tools: Function Calling工具列表
            **kwargs: 其他参数

        Returns:
            聊天完成响应
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            # 准备请求参数
            params = self._prepare_request_params(
                messages=messages,
                system_prompt=system_prompt,
                tools=tools,
                **kwargs
            )

            # 记录请求日志
            self._log_request("chat_completion", params)

            # 使用重试机制执行API调用
            async def _api_call():
                return await self.async_client.chat.completions.create(**params)

            response = await self.retry_manager.execute_with_retry(_api_call)

            # 更新统计信息（包含延迟信息）
            request_latency = time.time() - start_time
            self._update_success_stats(response, request_latency)

            # 记录响应日志
            self._log_response("chat_completion", response)

            return response

        except Exception as e:
            self._update_failure_stats()
            raise self._handle_error(e)

        finally:
            self.stats["total_time"] += time.time() - start_time
    
    async def chat_completion_stream(
        self,
        messages: Optional[List[Message]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        filter_tool_tags: bool = False,
        **kwargs
    ) -> AsyncIterator[ChatCompletionChunk]:
        """
        异步流式聊天完成调用

        Args:
            messages: 消息列表
            system_prompt: 系统提示词（可选）
            tools: Function Calling工具列表
            filter_tool_tags: 是否过滤工具调用标签（默认False，保持向后兼容）
            **kwargs: 其他参数

        Yields:
            聊天完成流式响应块（如果启用filter_tool_tags，delta.content将被过滤）
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            # 提取filter_tool_tags参数，避免传递给OpenAI API
            filter_tool_tags_param = filter_tool_tags

        

            # 准备请求参数（不包含filter_tool_tags）
            params = self._prepare_request_params(
                messages=messages,
                system_prompt=system_prompt,
                tools=tools,
                stream=True,
                **kwargs
            )

            # 记录请求日志
            self._log_request("chat_completion_stream", params)

            # 执行流式API调用
            stream = await self.async_client.chat.completions.create(**params)

            chunk_count = 0
            full_content = ""
            total_tokens = 0

            # 初始化工具调用标签过滤器（如果启用）
            tag_filter = ToolCallTagFilter() if filter_tool_tags_param else None

            async for chunk in stream:
                chunk_count += 1

                # 收集响应内容用于日志记录
                if chunk.choices and chunk.choices[0].delta.content:
                    full_content += chunk.choices[0].delta.content

                # 收集token使用信息
                if hasattr(chunk, 'usage') and chunk.usage:
                    total_tokens = chunk.usage.total_tokens



                # 如果启用了工具调用标签过滤，处理delta.content
                if filter_tool_tags_param and tag_filter and chunk.choices and chunk.choices[0].delta.content:
                    # 创建chunk的副本以避免修改原始对象
                    filtered_chunk = copy.deepcopy(chunk)
                    original_content = chunk.choices[0].delta.content
                    filtered_content = tag_filter.process_chunk(original_content)

                    # 更新副本的content
                    filtered_chunk.choices[0].delta.content = filtered_content

                    # 如果提取到了工具调用，添加到delta.tool_calls
                    extracted_calls = tag_filter.get_extracted_tool_calls()
                    if extracted_calls and not filtered_chunk.choices[0].delta.tool_calls:
                        # 将提取的工具调用转换为delta格式
                        tool_call_deltas = []
                        for i, tool_call in enumerate(extracted_calls):
                            from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall, ChoiceDeltaToolCallFunction

                            tool_call_delta = ChoiceDeltaToolCall(
                                index=i,
                                id=tool_call["id"],
                                function=ChoiceDeltaToolCallFunction(
                                    name=tool_call["function"]["name"],
                                    arguments=tool_call["function"]["arguments"]
                                ),
                                type="function"
                            )
                            tool_call_deltas.append(tool_call_delta)

                        filtered_chunk.choices[0].delta.tool_calls = tool_call_deltas
                        # 清空已处理的工具调用，避免重复
                        tag_filter.extracted_tool_calls.clear()

                    yield filtered_chunk
                else:
                    yield chunk

            # 如果启用了过滤，处理剩余的内容
            if filter_tool_tags_param and tag_filter:
                remaining_content = tag_filter.finalize()
                if remaining_content:
                    # 创建一个包含剩余内容的chunk
                    from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, Choice, ChoiceDelta

                    # 创建最后一个chunk来输出剩余内容
                    final_choice = Choice(
                        delta=ChoiceDelta(content=remaining_content),
                        index=0,
                        finish_reason=None
                    )
                    final_chunk = ChatCompletionChunk(
                        id="filtered_final",
                        choices=[final_choice],
                        created=int(time.time()),
                        model="filtered",
                        object="chat.completion.chunk"
                    )
                    yield final_chunk

            # 更新统计信息（包含延迟信息）
            self.stats["successful_requests"] += 1
            if total_tokens > 0:
                self.stats["total_tokens"] += total_tokens
            
            # 更新延迟统计（流式请求的延迟计算）
            request_latency = time.time() - start_time
            self._update_latency_stats(request_latency)

            # 记录响应日志（流式响应）
            self._log_stream_response("chat_completion_stream", chunk_count, full_content)

        except Exception as e:
            self._update_failure_stats()
            raise self._handle_error(e)

        finally:
            self.stats["total_time"] += time.time() - start_time




    
    def _handle_error(self, error: Exception, request_params: Optional[Dict[str, Any]] = None) -> OpenAIClientError:
        """
        处理和转换错误，提供详细的诊断信息

        Args:
            error: 原始错误
            request_params: 请求参数（用于诊断）

        Returns:
            转换后的错误，包含详细的诊断信息
        """
        import openai

        # 准备请求信息（去除敏感信息）
        safe_request_info = self._prepare_safe_request_info(request_params)
        
        # OpenAI SDK特定错误
        if isinstance(error, openai.RateLimitError):
            retry_after = getattr(error, 'retry_after', None)
            return OpenAIRateLimitError(
                f"API rate limit exceeded: {error}",
                original_error=error,
                request_info=safe_request_info,
                retry_after=retry_after
            )

        if isinstance(error, openai.APITimeoutError):
            return OpenAITimeoutError(
                f"API request timeout: {error}",
                original_error=error,
                request_info=safe_request_info
            )

        if isinstance(error, openai.APIConnectionError):
            return OpenAIRetryableError(
                f"API connection error: {error}",
                original_error=error,
                request_info=safe_request_info,
                error_type="network"
            )

        if isinstance(error, openai.InternalServerError):
            return OpenAIRetryableError(
                f"Internal server error: {error}",
                original_error=error,
                request_info=safe_request_info,
                error_type="server_error"
            )

        if isinstance(error, openai.BadRequestError):
            return OpenAIClientError(
                f"Bad request: {error}",
                original_error=error,
                request_info=safe_request_info,
                error_type="bad_request"
            )

        if isinstance(error, openai.AuthenticationError):
            return OpenAIClientError(
                f"Authentication failed: {error}",
                original_error=error,
                request_info=safe_request_info,
                error_type="authentication"
            )

        if isinstance(error, openai.PermissionDeniedError):
            return OpenAIClientError(
                f"Permission denied: {error}",
                original_error=error,
                request_info=safe_request_info,
                error_type="permission"
            )

        if isinstance(error, openai.NotFoundError):
            return OpenAIClientError(
                f"Resource not found: {error}",
                original_error=error,
                request_info=safe_request_info,
                error_type="not_found"
            )

        # 通用错误处理
        error_message = str(error)

        # 速率限制错误（字符串匹配）
        if "rate_limit" in error_message.lower() or "429" in error_message:
            return OpenAIRateLimitError(
                f"API rate limit exceeded: {error_message}",
                original_error=error,
                request_info=safe_request_info
            )

        # 超时错误（字符串匹配）
        if "timeout" in error_message.lower() or "timed out" in error_message.lower():
            return OpenAITimeoutError(
                f"API request timeout: {error_message}",
                original_error=error,
                request_info=safe_request_info
            )

        # 网络错误（字符串匹配）
        if any(keyword in error_message.lower() for keyword in ["connection", "network", "dns", "ssl", "socket"]):
            return OpenAIRetryableError(
                f"Network error: {error_message}",
                original_error=error,
                request_info=safe_request_info,
                error_type="network"
            )

        # 服务器错误（字符串匹配）
        if any(code in error_message for code in ["500", "502", "503", "504"]):
            return OpenAIRetryableError(
                f"Server error: {error_message}",
                original_error=error,
                request_info=safe_request_info,
                error_type="server_error"
            )

        # 其他错误
        return OpenAIClientError(
            f"OpenAI API error: {error_message}",
            original_error=error,
            request_info=safe_request_info,
            error_type="unknown"
        )

    def _get_user_friendly_error_message(self, error: OpenAIClientError) -> str:
        """
        生成用户友好的错误消息

        Args:
            error: OpenAIClientError实例

        Returns:
            用户友好的错误消息
        """
        error_type = getattr(error, 'error_type', 'unknown')
        
        friendly_messages = {
            "rate_limit": "⚠️ API访问频率受限，请稍后再试。如果您频繁遇到此问题，可以考虑升级API套餐或联系支持。",
            "timeout": "⏱️ 请求超时，可能是网络连接较慢或服务器响应延迟。请检查网络连接后重试。",
            "network": "🌐 网络连接问题，请检查您的网络连接是否正常，然后重试。",
            "server_error": "🔧 服务器暂时不可用，可能是OpenAI服务维护中。请稍后重试。",
            "bad_request": "❌ 请求格式错误，请检查输入参数是否正确。",
            "authentication": "🔑 API密钥验证失败，请检查您的API密钥是否正确配置。",
            "permission": "🚫 权限不足，请检查您的API密钥是否有访问该资源的权限。",
            "not_found": "🔍 请求的资源不存在，请检查API端点是否正确。",
            "default": "❌ 发生未知错误，请稍后重试。如果问题持续，请联系技术支持。"
        }
        
        # 获取具体的错误消息
        base_message = friendly_messages.get(error_type, friendly_messages["default"])
        
        # 添加重试建议（如果是可重试错误）
        if error_type in ["rate_limit", "timeout", "network", "server_error"]:
            if hasattr(error, 'retry_after') and error.retry_after:
                base_message += f" 建议等待 {error.retry_after:.0f} 秒后重试。"
            else:
                base_message += " 系统将自动重试，请稍等片刻。"
        
        return base_message

    def _create_fallback_response(self, error: Exception) -> Dict[str, Any]:
        """
        创建优雅降级的响应

        Args:
            error: 发生的错误

        Returns:
            降级响应字典
        """
        error_type = "unknown"
        if isinstance(error, OpenAIClientError):
            error_type = getattr(error, 'error_type', 'unknown')
        
        # 根据错误类型提供不同的降级响应
        fallback_responses = {
            "rate_limit": {
                "error": "rate_limit_exceeded",
                "message": "API访问频率受限，请稍后再试",
                "suggestion": "等待一段时间后重试或升级API套餐",
                "retryable": True
            },
            "timeout": {
                "error": "request_timeout", 
                "message": "请求超时，请检查网络连接",
                "suggestion": "检查网络稳定性后重试",
                "retryable": True
            },
            "network": {
                "error": "network_error",
                "message": "网络连接问题",
                "suggestion": "检查网络连接后重试",
                "retryable": True
            },
            "default": {
                "error": "service_unavailable",
                "message": "服务暂时不可用",
                "suggestion": "请稍后重试或联系技术支持",
                "retryable": False
            }
        }
        
        return fallback_responses.get(error_type, fallback_responses["default"])

    def _prepare_safe_request_info(self, request_params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        准备安全的请求信息（去除敏感数据）

        Args:
            request_params: 原始请求参数

        Returns:
            安全的请求信息字典
        """
        if not request_params:
            return {}
        
        # 复制参数并移除敏感信息
        safe_params = request_params.copy()
        
        # 移除敏感字段
        sensitive_fields = ["api_key", "password", "token", "secret", "key"]
        for field in sensitive_fields:
            if field in safe_params:
                safe_params[field] = "[REDACTED]"
        
        # 处理消息中的敏感内容
        if "messages" in safe_params and isinstance(safe_params["messages"], list):
            for message in safe_params["messages"]:
                if isinstance(message, dict) and "content" in message:
                    # 简略显示消息内容
                    content = message["content"]
                    if isinstance(content, str) and len(content) > 100:
                        message["content"] = content[:100] + "..."
        
        return safe_params
    
    def _log_request(self, method: str, params: Dict[str, Any]) -> None:
        """记录请求日志"""
        if self.config.log_requests:
            self.logger.info(f"🔄 OpenAI {method} 请求:")
            self.logger.info(f"� 完整请求参数: {params}")

    def _log_response(self, method: str, response: Any) -> None:
        """记录响应日志"""
        if self.config.log_responses:
            self.logger.info(f"✅ OpenAI {method} 响应:")
            self.logger.info(f"📝 完整响应: {response}")

    def _log_stream_response(self, method: str, chunk_count: int, content: str = "") -> None:
        """记录流式响应日志"""
        if self.config.log_responses:
            self.logger.info(f"✅ OpenAI {method} 流式响应完成: 接收到 {chunk_count} 个数据块")
            if content:
                self.logger.info(f"📝 完整流式响应内容: {content}")

    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """重置性能统计信息"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_time": 0.0,
            "error_stats": {
                "rate_limit": 0,
                "timeout": 0,
                "network": 0,
                "server_error": 0,
                "bad_request": 0,
                "authentication": 0,
                "permission": 0,
                "not_found": 0,
                "unknown": 0
            },
            "latency_stats": {
                "min": float('inf'),
                "max": 0.0,
                "avg": 0.0,
                "total_count": 0,
                "sum": 0.0
            },
            "retry_stats": {
                "total_retries": 0,
                "successful_retries": 0,
                "failed_retries": 0,
                "retries_by_error_type": {
                    "rate_limit": 0,
                    "timeout": 0,
                    "network": 0,
                    "server_error": 0,
                    "default": 0
                }
            }
        }

    def get_user_friendly_error(self, error: Exception) -> str:
        """
        获取用户友好的错误消息（公共方法）

        Args:
            error: 异常对象

        Returns:
            用户友好的错误消息
        """
        if isinstance(error, OpenAIClientError):
            return self._get_user_friendly_error_message(error)
        else:
            # 处理非OpenAIClientError异常
            handled_error = self._handle_error(error)
            return self._get_user_friendly_error_message(handled_error)


# 全局客户端实例
_global_client: Optional[OpenAIClient] = None


def get_openai_client(config: Optional[SimpleOpenAIConfig] = None) -> OpenAIClient:
    """
    获取全局OpenAI客户端实例

    Args:
        config: OpenAI配置对象

    Returns:
        OpenAI客户端实例
    """
    global _global_client

    if _global_client is None or config is not None:
        _global_client = OpenAIClient(config)

    return _global_client

