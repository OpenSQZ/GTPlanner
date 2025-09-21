"""
统一配置管理器测试
"""
import pytest
import os
import time
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到 Python 路径
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.unified_config import (
    UnifiedConfigManager,
    ConfigCache,
    get_config_manager,
    get_config,
    reload_config,
    clear_config_cache
)


class TestConfigCache:
    """ConfigCache 测试类"""

    def test_config_cache_creation(self):
        """测试配置缓存创建"""
        cache = ConfigCache(
            data="test_data",
            timestamp=time.time(),
            ttl=300.0
        )
        
        assert cache.data == "test_data"
        assert cache.ttl == 300.0
        assert not cache.is_expired()

    def test_config_cache_expiration(self):
        """测试配置缓存过期"""
        # 创建已过期的缓存
        cache = ConfigCache(
            data="test_data",
            timestamp=time.time() - 400,  # 400秒前
            ttl=300.0  # 5分钟TTL
        )
        
        assert cache.is_expired()


class TestUnifiedConfigManager:
    """UnifiedConfigManager 测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.config_manager = UnifiedConfigManager()

    def test_init_without_dynaconf(self):
        """测试在没有Dynaconf的情况下初始化"""
        with patch('utils.unified_config.DYNACONF_AVAILABLE', False):
            manager = UnifiedConfigManager()
            assert manager._settings is None

    def test_get_setting_from_env(self):
        """测试从环境变量获取配置"""
        with patch.dict(os.environ, {'GTPLANNER_TEST_KEY': 'test_value'}):
            value = self.config_manager.get_setting('test_key', 'default')
            assert value == 'test_value'

    def test_get_setting_default_value(self):
        """测试获取默认配置值"""
        # 确保环境变量不存在
        env_key = 'GTPLANNER_NONEXISTENT_KEY'
        if env_key in os.environ:
            del os.environ[env_key]
        
        value = self.config_manager.get_setting('nonexistent_key', 'default_value')
        assert value == 'default_value'

    def test_convert_env_value_boolean(self):
        """测试环境变量值转换 - 布尔值"""
        assert self.config_manager._convert_env_value('true') is True
        assert self.config_manager._convert_env_value('false') is False
        assert self.config_manager._convert_env_value('True') is True
        assert self.config_manager._convert_env_value('FALSE') is False

    def test_convert_env_value_integer(self):
        """测试环境变量值转换 - 整数"""
        assert self.config_manager._convert_env_value('123') == 123
        assert self.config_manager._convert_env_value('-456') == -456

    def test_convert_env_value_float(self):
        """测试环境变量值转换 - 浮点数"""
        assert self.config_manager._convert_env_value('123.45') == 123.45
        assert self.config_manager._convert_env_value('-67.89') == -67.89

    def test_convert_env_value_string(self):
        """测试环境变量值转换 - 字符串"""
        assert self.config_manager._convert_env_value('hello') == 'hello'
        assert self.config_manager._convert_env_value('123abc') == '123abc'

    def test_config_caching(self):
        """测试配置缓存功能"""
        # 第一次获取配置
        with patch.dict(os.environ, {'GTPLANNER_CACHE_TEST': 'cached_value'}):
            value1 = self.config_manager.get_setting('cache_test', use_cache=True)
            assert value1 == 'cached_value'
        
        # 修改环境变量，但应该返回缓存值
        with patch.dict(os.environ, {'GTPLANNER_CACHE_TEST': 'new_value'}):
            value2 = self.config_manager.get_setting('cache_test', use_cache=True)
            assert value2 == 'cached_value'  # 应该返回缓存值
        
        # 清空缓存后应该返回新值
        self.config_manager.clear_cache()
        with patch.dict(os.environ, {'GTPLANNER_CACHE_TEST': 'new_value'}):
            value3 = self.config_manager.get_setting('cache_test', use_cache=True)
            assert value3 == 'new_value'

    def test_get_openai_config(self):
        """测试获取OpenAI配置"""
        config = self.config_manager.get_openai_config()
        
        # 验证配置结构
        expected_keys = [
            'api_key', 'base_url', 'model', 'temperature', 'max_tokens',
            'timeout', 'max_retries', 'retry_delay', 'log_requests',
            'log_responses', 'function_calling_enabled', 'tool_choice'
        ]
        
        for key in expected_keys:
            assert key in config
        
        # 验证默认值
        assert config['model'] == 'gpt-4'
        assert config['temperature'] == 0.0
        assert config['timeout'] == 120.0

    def test_get_multilingual_config(self):
        """测试获取多语言配置"""
        config = self.config_manager.get_multilingual_config()
        
        expected_keys = [
            'default_language', 'supported_languages', 'auto_detect', 'fallback_language'
        ]
        
        for key in expected_keys:
            assert key in config
        
        assert config['default_language'] == 'zh'
        assert 'zh' in config['supported_languages']
        assert 'en' in config['supported_languages']

    def test_get_jina_config(self):
        """测试获取Jina配置"""
        config = self.config_manager.get_jina_config()
        
        expected_keys = ['api_key', 'base_url', 'timeout', 'max_retries']
        
        for key in expected_keys:
            assert key in config
        
        assert config['base_url'] == 'https://r.jina.ai/'
        assert config['timeout'] == 30.0

    def test_get_logging_config(self):
        """测试获取日志配置"""
        config = self.config_manager.get_logging_config()
        
        expected_keys = [
            'level', 'format', 'file_path', 'max_file_size',
            'backup_count', 'enable_console', 'enable_file'
        ]
        
        for key in expected_keys:
            assert key in config
        
        assert config['level'] == 'INFO'
        assert config['enable_console'] is True

    def test_get_performance_config(self):
        """测试获取性能配置"""
        config = self.config_manager.get_performance_config()
        
        expected_keys = [
            'max_concurrent_requests', 'request_timeout', 'connection_pool_size',
            'enable_caching', 'cache_ttl', 'enable_compression', 'compression_threshold'
        ]
        
        for key in expected_keys:
            assert key in config
        
        assert config['max_concurrent_requests'] == 10
        assert config['enable_caching'] is True

    def test_get_streaming_config(self):
        """测试获取流式响应配置"""
        config = self.config_manager.get_streaming_config()
        
        expected_keys = [
            'enable_streaming', 'chunk_size', 'heartbeat_interval',
            'max_connection_time', 'buffer_size'
        ]
        
        for key in expected_keys:
            assert key in config
        
        assert config['enable_streaming'] is True
        assert config['chunk_size'] == 1024

    def test_reload_config(self):
        """测试重新加载配置"""
        # 添加一些缓存
        self.config_manager.get_setting('test_key', 'test_value', use_cache=True)
        assert len(self.config_manager._cache) > 0
        
        # 重新加载配置
        self.config_manager.reload_config()
        
        # 缓存应该被清空
        assert len(self.config_manager._cache) == 0

    def test_clear_cache(self):
        """测试清空缓存"""
        # 添加一些缓存
        self.config_manager.get_setting('test_key1', 'value1', use_cache=True)
        self.config_manager.get_setting('test_key2', 'value2', use_cache=True)
        assert len(self.config_manager._cache) == 2
        
        # 清空缓存
        self.config_manager.clear_cache()
        assert len(self.config_manager._cache) == 0

    def test_get_cache_stats(self):
        """测试获取缓存统计信息"""
        # 添加一些缓存
        self.config_manager.get_setting('key1', 'value1', use_cache=True)
        self.config_manager.get_setting('key2', 'value2', use_cache=True)
        
        # 添加一个过期的缓存
        expired_cache = ConfigCache(
            data="expired_data",
            timestamp=time.time() - 400,
            ttl=300.0
        )
        self.config_manager._cache['expired_key'] = expired_cache
        
        stats = self.config_manager.get_cache_stats()
        
        assert stats['total_entries'] == 3
        assert stats['expired_entries'] == 1
        assert stats['active_entries'] == 2
        assert 'key1' in stats['cache_keys']
        assert 'key2' in stats['cache_keys']
        assert 'expired_key' in stats['cache_keys']


class TestGlobalConfigFunctions:
    """全局配置函数测试类"""

    def test_get_config_manager_singleton(self):
        """测试全局配置管理器单例模式"""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        assert manager1 is manager2

    def test_get_config_function(self):
        """测试便捷配置获取函数"""
        with patch.dict(os.environ, {'GTPLANNER_GLOBAL_TEST': 'global_value'}):
            value = get_config('global_test', 'default')
            assert value == 'global_value'

    def test_reload_config_function(self):
        """测试重新加载全局配置函数"""
        manager = get_config_manager()
        
        # 添加缓存
        manager.get_setting('test_reload', 'value', use_cache=True)
        assert len(manager._cache) > 0
        
        # 重新加载
        reload_config()
        assert len(manager._cache) == 0

    def test_clear_config_cache_function(self):
        """测试清空全局配置缓存函数"""
        manager = get_config_manager()
        
        # 添加缓存
        manager.get_setting('test_clear', 'value', use_cache=True)
        assert len(manager._cache) > 0
        
        # 清空缓存
        clear_config_cache()
        assert len(manager._cache) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
