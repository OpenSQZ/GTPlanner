"""
HTTP连接池性能测试

测试HTTP连接池的性能改进效果，包括：
1. 连接复用效果
2. 并发请求性能
3. 缓存命中率
4. 重试机制效果
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
import pytest

from utils.http_pool_manager import get_http_pool, HTTPPoolManager, ConnectionPoolConfig, CacheConfig
from utils.openai_client import get_openai_client


class HTTPPerformanceTester:
    """HTTP性能测试器"""
    
    def __init__(self):
        self.results: Dict[str, Any] = {}
    
    async def test_connection_reuse(self, num_requests: int = 10) -> Dict[str, Any]:
        """测试连接复用效果"""
        print(f"🔄 测试连接复用 ({num_requests} 个请求)...")
        
        pool = await get_http_pool()
        
        # 记录开始时间
        start_time = time.time()
        
        # 发送多个请求到同一个主机
        tasks = []
        for i in range(num_requests):
            task = pool.request(
                "GET",
                "https://httpbin.org/delay/0.1",
                cache_key=f"test_reuse_{i}"  # 不同的缓存键避免缓存影响
            )
            tasks.append(task)
        
        # 并发执行
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # 分析结果
        successful_requests = sum(1 for r in responses if isinstance(r, dict) and r.get("success"))
        avg_time_per_request = total_time / num_requests
        
        stats = pool.get_stats()
        
        result = {
            "test_name": "connection_reuse",
            "num_requests": num_requests,
            "successful_requests": successful_requests,
            "total_time": total_time,
            "avg_time_per_request": avg_time_per_request,
            "requests_per_second": num_requests / total_time,
            "pool_stats": stats
        }
        
        print(f"  ✅ 成功请求: {successful_requests}/{num_requests}")
        print(f"  ⏱️ 总时间: {total_time:.2f}s")
        print(f"  📊 平均每请求: {avg_time_per_request:.3f}s")
        print(f"  🚀 QPS: {result['requests_per_second']:.2f}")
        
        return result
    
    async def test_cache_performance(self, num_requests: int = 20) -> Dict[str, Any]:
        """测试缓存性能"""
        print(f"💾 测试缓存性能 ({num_requests} 个请求)...")
        
        # 创建启用缓存的连接池
        cache_config = CacheConfig(enabled=True, max_size=100, ttl_seconds=60)
        pool = HTTPPoolManager(cache_config=cache_config)
        await pool._initialize()
        
        # 第一轮：填充缓存
        cache_key = "test_cache_key"
        start_time = time.time()
        
        first_response = await pool.request(
            "GET",
            "https://httpbin.org/delay/0.5",
            cache_key=cache_key
        )
        first_request_time = time.time() - start_time
        
        # 第二轮：从缓存读取
        cache_start_time = time.time()
        tasks = []
        for i in range(num_requests - 1):
            task = pool.request(
                "GET",
                "https://httpbin.org/delay/0.5",
                cache_key=cache_key
            )
            tasks.append(task)
        
        cached_responses = await asyncio.gather(*tasks, return_exceptions=True)
        cache_total_time = time.time() - cache_start_time
        
        stats = pool.get_stats()
        
        result = {
            "test_name": "cache_performance",
            "first_request_time": first_request_time,
            "cached_requests_time": cache_total_time,
            "cache_hit_rate": stats.get("cache_hit_rate", 0),
            "cache_hits": stats.get("cache_hits", 0),
            "cache_misses": stats.get("cache_misses", 0),
            "speedup_factor": first_request_time / (cache_total_time / (num_requests - 1)) if cache_total_time > 0 else 0
        }
        
        print(f"  🎯 首次请求时间: {first_request_time:.3f}s")
        print(f"  ⚡ 缓存请求平均时间: {cache_total_time / (num_requests - 1):.3f}s")
        print(f"  📈 缓存命中率: {result['cache_hit_rate']:.2%}")
        print(f"  🚀 加速倍数: {result['speedup_factor']:.1f}x")
        
        await pool.close()
        return result
    
    async def test_concurrent_performance(self, num_concurrent: int = 10) -> Dict[str, Any]:
        """测试并发性能"""
        print(f"⚡ 测试并发性能 ({num_concurrent} 个并发请求)...")
        
        pool = await get_http_pool()
        
        # 并发请求测试
        start_time = time.time()
        
        tasks = []
        for i in range(num_concurrent):
            task = pool.request(
                "GET",
                f"https://httpbin.org/delay/0.2",
                cache_key=f"concurrent_test_{i}"
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # 分析响应时间
        response_times = []
        successful_requests = 0
        
        for response in responses:
            if isinstance(response, dict) and response.get("success"):
                successful_requests += 1
                response_times.append(response.get("execution_time", 0))
        
        stats = pool.get_stats()
        
        result = {
            "test_name": "concurrent_performance",
            "num_concurrent": num_concurrent,
            "successful_requests": successful_requests,
            "total_time": total_time,
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "median_response_time": statistics.median(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "pool_stats": stats
        }
        
        print(f"  ✅ 成功请求: {successful_requests}/{num_concurrent}")
        print(f"  ⏱️ 总时间: {total_time:.2f}s")
        print(f"  📊 平均响应时间: {result['avg_response_time']:.3f}s")
        print(f"  📈 中位数响应时间: {result['median_response_time']:.3f}s")
        
        return result
    
    async def test_retry_mechanism(self) -> Dict[str, Any]:
        """测试重试机制"""
        print("🔄 测试重试机制...")
        
        pool = await get_http_pool()
        
        # 测试对失败请求的重试
        start_time = time.time()
        
        # 使用一个会间歇性失败的端点
        response = await pool.request(
            "GET",
            "https://httpbin.org/status/500",  # 总是返回500错误
            cache_key="retry_test"
        )
        
        total_time = time.time() - start_time
        
        stats = pool.get_stats()
        
        result = {
            "test_name": "retry_mechanism",
            "response_success": response.get("success", False),
            "attempts": response.get("attempts", 1),
            "total_time": total_time,
            "retry_attempts": stats.get("retry_attempts", 0),
            "failed_requests": stats.get("failed_requests", 0)
        }
        
        print(f"  🎯 响应成功: {result['response_success']}")
        print(f"  🔄 尝试次数: {result['attempts']}")
        print(f"  ⏱️ 总时间: {total_time:.2f}s")
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有性能测试"""
        print("🚀 开始HTTP连接池性能测试...")
        print("=" * 50)
        
        all_results = {}
        
        try:
            # 1. 连接复用测试
            all_results["connection_reuse"] = await self.test_connection_reuse(10)
            print()
            
            # 2. 缓存性能测试
            all_results["cache_performance"] = await self.test_cache_performance(10)
            print()
            
            # 3. 并发性能测试
            all_results["concurrent_performance"] = await self.test_concurrent_performance(5)
            print()
            
            # 4. 重试机制测试
            all_results["retry_mechanism"] = await self.test_retry_mechanism()
            print()
            
        except Exception as e:
            print(f"❌ 测试过程中出现错误: {e}")
            all_results["error"] = str(e)
        
        print("=" * 50)
        print("📊 性能测试总结:")
        
        for test_name, result in all_results.items():
            if isinstance(result, dict) and "test_name" in result:
                print(f"  {test_name}: ✅")
            else:
                print(f"  {test_name}: ❌")
        
        return all_results


@pytest.mark.asyncio
async def test_http_pool_performance():
    """pytest测试函数"""
    tester = HTTPPerformanceTester()
    results = await tester.run_all_tests()
    
    # 验证基本性能指标
    assert "connection_reuse" in results
    assert "cache_performance" in results
    assert "concurrent_performance" in results
    
    # 验证连接复用效果
    reuse_result = results["connection_reuse"]
    assert reuse_result["successful_requests"] > 0
    assert reuse_result["requests_per_second"] > 1  # 至少1 QPS
    
    # 验证缓存效果
    cache_result = results["cache_performance"]
    assert cache_result["cache_hit_rate"] > 0.5  # 至少50%命中率
    assert cache_result["speedup_factor"] > 1  # 有加速效果


if __name__ == "__main__":
    async def main():
        tester = HTTPPerformanceTester()
        await tester.run_all_tests()
    
    asyncio.run(main())
