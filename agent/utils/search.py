"""
Jina 搜索引擎客户端工具
"""

import os
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from utils.config_manager import get_jina_api_key


class JinaSearchClient:
    """Jina 搜索引擎客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://s.jina.ai/",
        timeout: int = 30
    ):
        """
        初始化 Jina 搜索客户端
        
        Args:
            api_key: API密钥，如果为None则从环境变量JINA_API_KEY读取
            base_url: API端点URL
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key or get_jina_api_key() or os.getenv("JINA_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        if not self.api_key:
            raise ValueError("API密钥未设置，请设置JINA_API_KEY环境变量或传入api_key参数")
        
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-Respond-With": "no-content"
        }
    
    async def search(
        self,
        query: str,
        count: int = 10,
        site: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行搜索查询 - 异步版本

        Args:
            query: 搜索查询字符串
            count: 返回结果数量，默认10
            site: 限制搜索的网站域名
            **kwargs: 其他查询参数

        Returns:
            搜索结果字典
        """

        try:
            # 构建查询参数
            params = {
                "q": query,
                "count": count,
                **kwargs
            }

            if site:
                params["site"] = site

            # 使用异步HTTP客户端
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    headers=self.headers
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result

        except aiohttp.ClientError as e:
            print(f"❌ Jina搜索API请求异常: {str(e)}")
            print(f"❌ 异常类型: {type(e).__name__}")
            raise Exception(f"Jina搜索API调用失败: {str(e)}")
        except asyncio.TimeoutError as e:
            print(f"❌ Jina搜索API超时: {str(e)}")
            raise Exception(f"Jina搜索API超时: {str(e)}")
        except Exception as e:
            print(f"❌ 搜索过程中发生未知错误: {str(e)}")
            print(f"❌ 异常类型: {type(e).__name__}")
            raise Exception(f"搜索过程中发生错误: {str(e)}")
    
    async def search_simple(
        self,
        query: str,
        count: int = 5
    ) -> List[Dict[str, str]]:
        """
        简化的搜索接口，只返回基本信息 - 异步版本

        Args:
            query: 搜索查询字符串
            count: 返回结果数量

        Returns:
            包含title、url、description的结果列表
        """
        result = await self.search(query, count=count)
        
        if result.get("code") != 200:
            raise Exception(f"搜索失败: {result.get('status', 'Unknown error')}")
        
        # 提取基本信息
        simplified_results = []
        for item in result.get("data", []):
            simplified_results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
                "content": item.get("content", "")
            })
        
        return simplified_results
    
    async def search_with_content(
        self,
        query: str,
        count: int = 5
    ) -> List[Dict[str, str]]:
        """
        搜索并返回包含内容的结果 - 异步版本

        Args:
            query: 搜索查询字符串
            count: 返回结果数量

        Returns:
            包含完整内容的结果列表
        """
        # 移除 X-Respond-With: no-content 头部以获取内容
        headers = self.headers.copy()
        headers.pop("X-Respond-With", None)

        try:
            params = {
                "q": query,
                "count": count
            }

            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    headers=headers
                ) as response:
                    response.raise_for_status()
                    result = await response.json()

                    if result.get("code") != 200:
                        raise Exception(f"搜索失败: {result.get('status', 'Unknown error')}")

                    return result.get("data", [])

        except aiohttp.ClientError as e:
            raise Exception(f"Jina搜索API调用失败: {str(e)}")
        except asyncio.TimeoutError as e:
            raise Exception(f"Jina搜索API超时: {str(e)}")
        except Exception as e:
            raise Exception(f"搜索过程中发生错误: {str(e)}")
    
    def get_usage_info(self, result: Dict[str, Any]) -> Dict[str, int]:
        """
        从搜索结果中提取使用信息
        
        Args:
            result: 搜索API返回的完整结果
            
        Returns:
            包含token使用信息的字典
        """
        meta = result.get("meta", {})
        usage = meta.get("usage", {})
        return {
            "tokens": usage.get("tokens", 0)
        }
