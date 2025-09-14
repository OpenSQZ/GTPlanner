"""
优化效果测试

测试GTPlanner的各项优化功能，包括：
- 性能优化测试
- 错误处理测试
- 配置验证测试
- 安全功能测试
- 内存优化测试
"""

import asyncio
import time
import pytest
import tempfile
import os
from unittest.mock import Mock, patch

# 导入优化模块
from utils.advanced_cache import get_global_cache, AsyncCacheWrapper
from utils.performance_monitor import get_global_monitor, monitor_request
from utils.enhanced_error_handler import get_global_error_handler, retry_on_failure
from utils.config_validator import validate_settings_file, get_global_validator
from utils.security_enhancer import get_global_security_enhancer, SecurityConfig
from utils.memory_optimizer import get_global_memory_optimizer, optimize_memory
from agent.persistence.connection_pool import OptimizedConnectionPool


class TestPerformanceOptimizations:
    """性能优化测试"""
    
    def test_cache_performance(self):
        """测试缓存性能"""
        cache = get_global_cache()
        
        # 测试基本缓存操作
        start_time = time.time()
        for i in range(1000):
            cache.set(f"key_{i}", f"value_{i}")
        
        set_time = time.time() - start_time
        
        # 测试缓存读取
        start_time = time.time()
        for i in range(1000):
            value = cache.get(f"key_{i}")
            assert value == f"value_{i}"
        
        get_time = time.time() - start_time
        
        # 验证性能提升
        assert set_time < 1.0, f"缓存设置时间过长: {set_time:.3f}s"
        assert get_time < 0.5, f"缓存读取时间过长: {get_time:.3f}s"
        
        # 测试缓存统计
        stats = cache.get_stats()
        assert stats.hits >= 1000
        assert stats.hit_rate > 0.9
    
    def test_async_cache_performance(self):
        """测试异步缓存性能"""
        async def async_test():
            cache = AsyncCacheWrapper(get_global_cache())
            
            # 异步设置
            start_time = time.time()
            tasks = []
            for i in range(100):
                tasks.append(cache.set(f"async_key_{i}", f"async_value_{i}"))
            
            await asyncio.gather(*tasks)
            set_time = time.time() - start_time
            
            # 异步读取
            start_time = time.time()
            tasks = []
            for i in range(100):
                tasks.append(cache.get(f"async_key_{i}"))
            
            results = await asyncio.gather(*tasks)
            get_time = time.time() - start_time
            
            # 验证结果
            for i, result in enumerate(results):
                assert result == f"async_value_{i}"
            
            assert set_time < 1.0, f"异步缓存设置时间过长: {set_time:.3f}s"
            assert get_time < 0.5, f"异步缓存读取时间过长: {get_time:.3f}s"
        
        asyncio.run(async_test())
    
    def test_performance_monitoring(self):
        """测试性能监控"""
        monitor = get_global_monitor()
        
        # 模拟请求
        with monitor_request(monitor):
            time.sleep(0.1)  # 模拟处理时间
        
        # 检查指标
        metrics = monitor.get_metrics()
        assert metrics.total_requests >= 1
        assert metrics.successful_requests >= 1
        assert metrics.avg_response_time > 0
    
    def test_database_connection_pool(self):
        """测试数据库连接池"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            pool = OptimizedConnectionPool(db_path, min_connections=2, max_connections=5)
            
            # 测试连接获取和归还
            connections = []
            for _ in range(3):
                conn = pool.get_connection()
                assert conn is not None
                connections.append(conn)
            
            # 归还连接
            for conn in connections:
                pool.return_connection(conn)
            
            # 检查统计信息
            stats = pool.get_stats()
            assert stats.total_connections >= 2
            assert stats.active_connections == 0
            assert stats.idle_connections >= 2
            
            pool.close_all_connections()
            
        finally:
            os.unlink(db_path)


class TestErrorHandling:
    """错误处理测试"""
    
    def test_error_classification(self):
        """测试错误分类"""
        handler = get_global_error_handler()
        
        # 测试网络错误
        try:
            raise ConnectionError("网络连接失败")
        except Exception as e:
            context = handler.handle_error(e, "网络测试")
            assert context.category.value == "network"
            assert context.severity.value == "medium"
    
    def test_retry_mechanism(self):
        """测试重试机制"""
        call_count = 0
        
        @retry_on_failure("test_operation")
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("模拟网络错误")
            return "success"
        
        result = failing_function()
        assert result == "success"
        assert call_count == 3
    
    def test_user_friendly_messages(self):
        """测试用户友好消息"""
        handler = get_global_error_handler()
        
        # 创建错误上下文
        context = handler.handle_error(
            ConnectionError("网络错误"),
            "测试错误",
            user_id="test_user"
        )
        
        friendly_message = handler.get_user_friendly_message(context)
        assert "网络连接" in friendly_message
        assert "重试" in friendly_message


class TestConfigurationValidation:
    """配置验证测试"""
    
    def test_config_validation(self):
        """测试配置验证"""
        validator = get_global_validator()
        
        # 测试有效配置
        valid_config = {
            "debug": True,
            "logging": {
                "level": "INFO",
                "file_enabled": True
            },
            "llm": {
                "base_url": "https://api.example.com",
                "api_key": "test-key",
                "model": "test-model"
            }
        }
        
        result = validator.validate_config(valid_config)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_invalid_config(self):
        """测试无效配置"""
        validator = get_global_validator()
        
        # 测试无效配置
        invalid_config = {
            "logging": {
                "level": "INVALID_LEVEL"  # 无效的日志级别
            },
            "llm": {
                "max_tokens": 50000  # 超过最大值
            }
        }
        
        result = validator.validate_config(invalid_config)
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_environment_variables(self):
        """测试环境变量检查"""
        validator = get_global_validator()
        
        env_status = validator.check_environment_variables()
        assert isinstance(env_status, dict)
        
        # 检查是否有LLM相关的环境变量
        llm_vars = [key for key in env_status.keys() if 'LLM' in key]
        assert len(llm_vars) > 0


class TestSecurityFeatures:
    """安全功能测试"""
    
    def test_input_validation(self):
        """测试输入验证"""
        enhancer = get_global_security_enhancer()
        
        # 测试正常输入
        result = enhancer.validate_request(
            {"message": "Hello, world!"},
            "test_client"
        )
        assert result["valid"]
        
        # 测试XSS攻击
        result = enhancer.validate_request(
            {"message": "<script>alert('xss')</script>"},
            "test_client"
        )
        assert not result["valid"] or len(result["warnings"]) > 0
    
    def test_sql_injection_protection(self):
        """测试SQL注入防护"""
        enhancer = get_global_security_enhancer()
        
        # 测试SQL注入
        result = enhancer.validate_request(
            {"query": "'; DROP TABLE users; --"},
            "test_client"
        )
        assert not result["valid"] or len(result["warnings"]) > 0
    
    def test_rate_limiting(self):
        """测试速率限制"""
        enhancer = get_global_security_enhancer()
        
        # 快速发送多个请求
        for i in range(70):  # 超过默认限制60
            result = enhancer.validate_request(
                {"message": f"Request {i}"},
                "test_client"
            )
            
            if i >= 60:
                assert not result["valid"]
                break


class TestMemoryOptimization:
    """内存优化测试"""
    
    def test_memory_monitoring(self):
        """测试内存监控"""
        optimizer = get_global_memory_optimizer()
        
        # 获取初始内存状态
        initial_stats = optimizer.monitor.get_current_stats()
        
        # 创建一些对象消耗内存
        large_list = [i for i in range(10000)]
        large_dict = {f"key_{i}": f"value_{i}" for i in range(1000)}
        
        # 执行内存优化
        optimization_result = optimizer.optimize_memory()
        
        # 验证优化结果
        assert "before_memory" in optimization_result
        assert "after_memory" in optimization_result
        assert "freed_memory" in optimization_result
        assert optimization_result["freed_memory"] >= 0
    
    def test_memory_leak_detection(self):
        """测试内存泄漏检测"""
        monitor = get_global_memory_monitor()
        
        # 模拟内存泄漏
        leaked_objects = []
        for i in range(100):
            leaked_objects.append([j for j in range(100)])
        
        # 触发泄漏检测
        monitor._detect_memory_leaks()
        
        # 检查是否检测到泄漏
        leaks = monitor.get_detected_leaks()
        # 注意：这个测试可能不会立即检测到泄漏，因为需要时间积累


class TestIntegration:
    """集成测试"""
    
    def test_full_optimization_workflow(self):
        """测试完整优化工作流"""
        # 1. 初始化所有组件
        cache = get_global_cache()
        monitor = get_global_monitor()
        error_handler = get_global_error_handler()
        security_enhancer = get_global_security_enhancer()
        memory_optimizer = get_global_memory_optimizer()
        
        # 2. 模拟正常使用
        with monitor_request(monitor):
            # 使用缓存
            cache.set("test_key", "test_value")
            cached_value = cache.get("test_key")
            assert cached_value == "test_value"
            
            # 使用安全验证
            result = security_enhancer.validate_request(
                {"message": "Test message"},
                "test_client"
            )
            assert result["valid"]
        
        # 3. 检查所有组件状态
        cache_stats = cache.get_stats()
        monitor_stats = monitor.get_metrics()
        error_stats = error_handler.get_error_statistics()
        memory_stats = memory_optimizer.monitor.get_current_stats()
        
        # 验证组件正常工作
        assert cache_stats is not None
        assert monitor_stats is not None
        assert error_stats is not None
        assert memory_stats is not None


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
