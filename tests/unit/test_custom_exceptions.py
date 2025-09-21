"""
自定义异常类型测试

测试自定义异常类型体系的功能，包括：
1. 异常类型创建和属性
2. 异常映射功能
3. 用户友好消息生成
4. 异常处理装饰器
"""

import pytest
from utils.custom_exceptions import (
    GTPlannerException, APIError, ConfigError, ValidationError,
    ProcessingError, NetworkError, StorageError, ErrorCode,
    map_standard_exception, handle_exceptions,
    raise_api_error, raise_config_error, raise_validation_error
)


class TestGTPlannerException:
    """测试基础异常类"""
    
    def test_basic_exception_creation(self):
        """测试基础异常创建"""
        exc = GTPlannerException(
            message="测试错误",
            error_code=ErrorCode.INVALID_INPUT,
            details={"field": "test"},
            suggestions=["检查输入格式"]
        )
        
        assert exc.message == "测试错误"
        assert exc.error_code == ErrorCode.INVALID_INPUT
        assert exc.details == {"field": "test"}
        assert exc.suggestions == ["检查输入格式"]
        assert "输入数据格式不正确" in exc.user_message
    
    def test_exception_to_dict(self):
        """测试异常转换为字典"""
        exc = GTPlannerException(
            message="测试错误",
            error_code=ErrorCode.API_TIMEOUT_ERROR
        )
        
        result = exc.to_dict()
        
        assert result["error_code"] == ErrorCode.API_TIMEOUT_ERROR.value
        assert result["error_name"] == "API_TIMEOUT_ERROR"
        assert result["message"] == "测试错误"
        assert "user_message" in result
        assert "details" in result
        assert "suggestions" in result
    
    def test_exception_str_representation(self):
        """测试异常字符串表示"""
        exc = GTPlannerException(
            message="测试错误",
            error_code=ErrorCode.PROCESSING_FAILED
        )
        
        str_repr = str(exc)
        assert "PROCESSING_FAILED" in str_repr
        assert "测试错误" in str_repr


class TestSpecificExceptions:
    """测试特定异常类型"""
    
    def test_api_error(self):
        """测试API错误"""
        exc = APIError(
            message="API调用失败",
            error_code=ErrorCode.API_RATE_LIMIT_ERROR,
            status_code=429,
            response_data={"error": "rate limit exceeded"}
        )
        
        assert exc.status_code == 429
        assert exc.response_data == {"error": "rate limit exceeded"}
        assert exc.details["status_code"] == 429
        assert exc.details["response_data"] == {"error": "rate limit exceeded"}
    
    def test_config_error(self):
        """测试配置错误"""
        exc = ConfigError(
            message="配置文件错误",
            config_file="settings.toml",
            config_key="llm.api_key"
        )
        
        assert exc.config_file == "settings.toml"
        assert exc.config_key == "llm.api_key"
        assert exc.details["config_file"] == "settings.toml"
        assert exc.details["config_key"] == "llm.api_key"
    
    def test_validation_error(self):
        """测试验证错误"""
        exc = ValidationError(
            message="字段验证失败",
            field_name="user_input",
            field_value="invalid_value",
            expected_type="string"
        )
        
        assert exc.field_name == "user_input"
        assert exc.field_value == "invalid_value"
        assert exc.expected_type == "string"
    
    def test_processing_error(self):
        """测试处理错误"""
        exc = ProcessingError(
            message="节点执行失败",
            node_name="TestNode",
            flow_name="TestFlow",
            stage="execution"
        )
        
        assert exc.node_name == "TestNode"
        assert exc.flow_name == "TestFlow"
        assert exc.stage == "execution"
    
    def test_network_error(self):
        """测试网络错误"""
        exc = NetworkError(
            message="连接超时",
            url="https://api.example.com",
            timeout=30.0
        )
        
        assert exc.url == "https://api.example.com"
        assert exc.timeout == 30.0
    
    def test_storage_error(self):
        """测试存储错误"""
        exc = StorageError(
            message="文件不存在",
            file_path="/path/to/file.txt",
            operation="read"
        )
        
        assert exc.file_path == "/path/to/file.txt"
        assert exc.operation == "read"


class TestExceptionMapping:
    """测试异常映射功能"""
    
    def test_map_connection_error(self):
        """测试连接错误映射"""
        original_exc = ConnectionError("连接失败")
        mapped_exc = map_standard_exception(original_exc)
        
        assert isinstance(mapped_exc, NetworkError)
        assert mapped_exc.error_code == ErrorCode.NETWORK_ERROR
        assert "连接失败" in mapped_exc.message
    
    def test_map_timeout_error(self):
        """测试超时错误映射"""
        original_exc = TimeoutError("请求超时")
        mapped_exc = map_standard_exception(original_exc)
        
        assert isinstance(mapped_exc, NetworkError)
        assert mapped_exc.error_code == ErrorCode.CONNECTION_TIMEOUT
    
    def test_map_file_not_found_error(self):
        """测试文件未找到错误映射"""
        original_exc = FileNotFoundError("文件不存在")
        mapped_exc = map_standard_exception(original_exc)
        
        assert isinstance(mapped_exc, StorageError)
        assert mapped_exc.error_code == ErrorCode.FILE_NOT_FOUND
    
    def test_map_permission_error(self):
        """测试权限错误映射"""
        original_exc = PermissionError("权限不足")
        mapped_exc = map_standard_exception(original_exc)
        
        assert isinstance(mapped_exc, StorageError)
        assert mapped_exc.error_code == ErrorCode.FILE_PERMISSION_ERROR
    
    def test_map_value_error(self):
        """测试值错误映射"""
        original_exc = ValueError("无效的值")
        mapped_exc = map_standard_exception(original_exc)
        
        assert isinstance(mapped_exc, ValidationError)
        assert mapped_exc.error_code == ErrorCode.DATA_TYPE_ERROR
    
    def test_map_key_error(self):
        """测试键错误映射"""
        original_exc = KeyError("missing_key")
        mapped_exc = map_standard_exception(original_exc)
        
        assert isinstance(mapped_exc, ValidationError)
        assert mapped_exc.error_code == ErrorCode.MISSING_REQUIRED_FIELD
        assert mapped_exc.field_name == "missing_key"
    
    def test_map_unknown_error(self):
        """测试未知错误映射"""
        original_exc = RuntimeError("运行时错误")
        mapped_exc = map_standard_exception(original_exc)
        
        assert isinstance(mapped_exc, GTPlannerException)
        assert mapped_exc.error_code == ErrorCode.UNKNOWN_ERROR
        assert "RuntimeError" in mapped_exc.details["original_exception"]


class TestExceptionHandlers:
    """测试异常处理装饰器和便捷函数"""
    
    def test_handle_exceptions_decorator_sync(self):
        """测试同步函数异常处理装饰器"""
        @handle_exceptions(reraise=False)
        def test_function():
            raise ValueError("测试错误")
        
        result = test_function()
        assert isinstance(result, ValidationError)
        assert result.error_code == ErrorCode.DATA_TYPE_ERROR
    
    @pytest.mark.asyncio
    async def test_handle_exceptions_decorator_async(self):
        """测试异步函数异常处理装饰器"""
        @handle_exceptions(reraise=False)
        async def test_async_function():
            raise ConnectionError("连接失败")
        
        result = await test_async_function()
        assert isinstance(result, NetworkError)
        assert result.error_code == ErrorCode.NETWORK_ERROR
    
    def test_raise_api_error(self):
        """测试API错误抛出函数"""
        with pytest.raises(APIError) as exc_info:
            raise_api_error("API错误", status_code=401)
        
        exc = exc_info.value
        assert exc.error_code == ErrorCode.API_AUTHENTICATION_ERROR
        assert exc.status_code == 401
    
    def test_raise_config_error(self):
        """测试配置错误抛出函数"""
        with pytest.raises(ConfigError) as exc_info:
            raise_config_error("配置错误", config_file="test.toml")
        
        exc = exc_info.value
        assert exc.config_file == "test.toml"
    
    def test_raise_validation_error(self):
        """测试验证错误抛出函数"""
        with pytest.raises(ValidationError) as exc_info:
            raise_validation_error("验证失败", field_name="test_field")
        
        exc = exc_info.value
        assert exc.field_name == "test_field"


class TestErrorCodes:
    """测试错误代码"""
    
    def test_error_code_values(self):
        """测试错误代码值"""
        assert ErrorCode.UNKNOWN_ERROR.value == 1000
        assert ErrorCode.API_CONNECTION_ERROR.value == 1100
        assert ErrorCode.CONFIG_FILE_NOT_FOUND.value == 1200
        assert ErrorCode.VALIDATION_FAILED.value == 1300
        assert ErrorCode.PROCESSING_FAILED.value == 1400
        assert ErrorCode.STORAGE_ERROR.value == 1500
        assert ErrorCode.NETWORK_ERROR.value == 1600
    
    def test_error_code_names(self):
        """测试错误代码名称"""
        assert ErrorCode.UNKNOWN_ERROR.name == "UNKNOWN_ERROR"
        assert ErrorCode.API_TIMEOUT_ERROR.name == "API_TIMEOUT_ERROR"
        assert ErrorCode.CONFIG_VALIDATION_ERROR.name == "CONFIG_VALIDATION_ERROR"


class TestUserFriendlyMessages:
    """测试用户友好消息"""
    
    def test_user_message_generation(self):
        """测试用户消息生成"""
        test_cases = [
            (ErrorCode.API_CONNECTION_ERROR, "无法连接到API服务"),
            (ErrorCode.API_TIMEOUT_ERROR, "API请求超时"),
            (ErrorCode.API_RATE_LIMIT_ERROR, "API请求频率过高"),
            (ErrorCode.CONFIG_FILE_NOT_FOUND, "配置文件未找到"),
            (ErrorCode.INVALID_INPUT, "输入数据格式不正确"),
        ]
        
        for error_code, expected_message in test_cases:
            exc = GTPlannerException("技术错误", error_code=error_code)
            assert expected_message in exc.user_message
    
    def test_custom_user_message(self):
        """测试自定义用户消息"""
        custom_message = "这是自定义的用户消息"
        exc = GTPlannerException(
            "技术错误",
            error_code=ErrorCode.UNKNOWN_ERROR,
            user_message=custom_message
        )
        
        assert exc.user_message == custom_message
