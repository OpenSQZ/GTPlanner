"""
Jina URL转Markdown工具
"""

import os
import aiohttp
import asyncio
from typing import Dict, Optional, Any
from utils.config_manager import get_jina_api_key

class JinaWebClient:
    """Jina URL转Markdown客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://r.jina.ai/",
        timeout: int = 30
    ):
        """
        初始化 Jina Web 客户端
        
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
            "Authorization": f"Bearer {self.api_key}"
        }
    
    async def url_to_markdown(
        self,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        将URL转换为Markdown格式 - 异步版本

        Args:
            url: 要转换的URL
            **kwargs: 其他请求参数

        Returns:
            包含转换结果的字典
        """
        try:
            # 构建完整的API URL
            api_url = f"{self.base_url}/{url}"

            # 使用异步HTTP客户端发送请求
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    api_url,
                    headers=self.headers,
                    params=kwargs
                ) as response:
                    response.raise_for_status()
                    return await response.json()

        except aiohttp.ClientError as e:
            raise Exception(f"Jina Web API调用失败: {str(e)}")
        except asyncio.TimeoutError as e:
            raise Exception(f"Jina Web API超时: {str(e)}")
        except Exception as e:
            raise Exception(f"URL转换过程中发生错误: {str(e)}")
    
    def get_content(
        self,
        url: str,
        **kwargs
    ) -> str:
        """
        获取URL的Markdown内容
        
        Args:
            url: 要获取内容的URL
            **kwargs: 其他请求参数
            
        Returns:
            Markdown格式的内容字符串
        """
        result = self.url_to_markdown(url, **kwargs)
        
        if result.get("code") != 200:
            raise Exception(f"获取内容失败: {result.get('status', 'Unknown error')}")
        
        data = result.get("data", {})
        return data.get("content", "")
    
    async def get_page_info(
        self,
        url: str,
        **kwargs
    ) -> Dict[str, str]:
        """
        获取页面基本信息 - 异步版本

        Args:
            url: 要获取信息的URL
            **kwargs: 其他请求参数

        Returns:
            包含title、description、url、content的字典
        """
        result = await self.url_to_markdown(url, **kwargs)

        if result.get("code") != 200:
            raise Exception(f"获取页面信息失败: {result.get('status', 'Unknown error')}")

        data = result.get("data", {})
        return {
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "url": data.get("url", url),
            "content": data.get("content", "")
        }
    
    def get_usage_info(self, result: Dict[str, Any]) -> Dict[str, int]:
        """
        从转换结果中提取使用信息
        
        Args:
            result: API返回的完整结果
            
        Returns:
            包含token使用信息的字典
        """
        # 从data中获取usage信息
        data = result.get("data", {})
        usage = data.get("usage", {})
        
        # 也检查meta中的usage信息
        meta = result.get("meta", {})
        meta_usage = meta.get("usage", {})
        
        return {
            "tokens": usage.get("tokens", 0) or meta_usage.get("tokens", 0)
        }
    
    def batch_convert(
        self,
        urls: list,
        **kwargs
    ) -> Dict[str, Dict[str, str]]:
        """
        批量转换多个URL
        
        Args:
            urls: URL列表
            **kwargs: 其他请求参数
            
        Returns:
            以URL为键的结果字典
        """
        results = {}
        
        for url in urls:
            try:
                results[url] = self.get_page_info(url, **kwargs)
            except Exception as e:
                results[url] = {
                    "title": "",
                    "description": "",
                    "url": url,
                    "content": "",
                    "error": str(e)
                }
        
        return results
