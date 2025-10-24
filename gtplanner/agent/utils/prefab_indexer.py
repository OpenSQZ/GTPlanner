"""
预制件索引构建模块

负责将 community-prefabs.json 中的预制件转换为向量服务可索引的文档格式。
这不是一个 pocketflow node，而是独立的工具函数。
"""

import os
import json
import time
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path


class PrefabIndexer:
    """预制件索引构建器"""
    
    def __init__(self, vector_service_url: str = None, timeout: int = 30):
        """
        初始化索引构建器
        
        Args:
            vector_service_url: 向量服务地址
            timeout: 请求超时时间
        """
        from gtplanner.utils.config_manager import get_vector_service_config
        
        if vector_service_url is None:
            vector_config = get_vector_service_config()
            vector_service_url = vector_config.get("base_url")
        
        self.vector_service_url = vector_service_url
        self.timeout = timeout
        
        # 从配置获取索引参数
        vector_config = get_vector_service_config()
        self.index_name = vector_config.get("tools_index_name", "document_gtplanner_prefabs")
        self.vector_field = vector_config.get("vector_field", "combined_text")
    
    def check_vector_service_available(self) -> bool:
        """检查向量服务是否可用"""
        if not self.vector_service_url:
            return False
        
        try:
            response = requests.get(
                f"{self.vector_service_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def load_prefabs_from_json(self, json_path: str = None) -> List[Dict]:
        """
        从 JSON 文件加载预制件
        
        Args:
            json_path: community-prefabs.json 路径
            
        Returns:
            预制件列表
        """
        if json_path is None:
            # 自动定位
            current_dir = Path(__file__).parent
            json_path = current_dir.parent.parent.parent / "prefabs" / "releases" / "community-prefabs.json"
        
        json_path = Path(json_path)
        if not json_path.exists():
            raise FileNotFoundError(f"Prefabs JSON not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            prefabs = json.load(f)
        
        return prefabs
    
    def convert_prefab_to_document(self, prefab: Dict) -> Dict[str, Any]:
        """
        将预制件转换为向量服务的文档格式
        
        Args:
            prefab: 预制件对象（从 community-prefabs.json）
            
        Returns:
            文档对象
        """
        # 构建标签字符串
        tags = prefab.get("tags", [])
        tags_str = ", ".join(tags) if tags else ""
        
        # 构建组合文本（用于 embedding）
        combined_text = f"{prefab['name']} {prefab['description']}"
        if tags_str:
            combined_text += f" {tags_str}"
        
        # 构建 artifact URL
        artifact_url = self._construct_artifact_url(prefab)
        
        # 返回文档对象
        document = {
            "id": prefab["id"],
            "type": "PREFAB",  # 统一类型
            "summary": prefab["name"],  # 名称映射到 summary
            "description": prefab["description"],
            "tags": tags_str,
            "combined_text": combined_text,  # 用于 embedding
            # 元数据
            "version": prefab["version"],
            "author": prefab["author"],
            "repo_url": prefab["repo_url"],
            "artifact_url": artifact_url,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return document
    
    def _construct_artifact_url(self, prefab: Dict) -> str:
        """
        构建预制件的下载链接
        
        根据 schema.json 规则：
        {repo_url}/releases/download/v{version}/{id}-{version}.whl
        
        Args:
            prefab: 预制件对象
            
        Returns:
            下载链接
        """
        repo_url = prefab["repo_url"].rstrip('/')
        version = prefab["version"]
        prefab_id = prefab["id"]
        
        return (
            f"{repo_url}/releases/download/v{version}/{prefab_id}-{version}.whl"
        )
    
    def build_index(
        self, 
        json_path: str = None, 
        force_reindex: bool = False
    ) -> Dict[str, Any]:
        """
        构建预制件索引
        
        Args:
            json_path: community-prefabs.json 路径
            force_reindex: 是否强制重建索引
            
        Returns:
            索引构建结果
        """
        start_time = time.time()
        
        # 检查向量服务
        if not self.check_vector_service_available():
            return {
                "success": False,
                "error": "Vector service is not available",
                "index_name": None,
                "indexed_count": 0
            }
        
        try:
            # 1. 加载预制件
            prefabs = self.load_prefabs_from_json(json_path)
            print(f"📦 加载了 {len(prefabs)} 个预制件")
            
            # 2. 转换为文档格式
            documents = []
            for prefab in prefabs:
                doc = self.convert_prefab_to_document(prefab)
                documents.append(doc)
            
            print(f"📝 转换了 {len(documents)} 个文档")
            
            # 3. 调用向量服务建立索引
            index_result = self._call_vector_service_index(
                documents, 
                force_reindex
            )
            
            elapsed_time = time.time() - start_time
            
            return {
                "success": True,
                "index_name": self.index_name,
                "indexed_count": len(documents),
                "elapsed_time": round(elapsed_time, 2),
                "vector_service_url": self.vector_service_url,
                **index_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "index_name": None,
                "indexed_count": 0
            }
    
    def _call_vector_service_index(
        self, 
        documents: List[Dict], 
        force_reindex: bool
    ) -> Dict[str, Any]:
        """
        调用向量服务建立索引
        
        Args:
            documents: 文档列表
            force_reindex: 是否强制重建
            
        Returns:
            索引结果
        """
        # 构建索引请求
        index_request = {
            "documents": documents,
            "index": self.index_name,
            "vector_field": self.vector_field,
            "force_reindex": force_reindex
        }
        
        # 调用向量服务
        response = requests.post(
            f"{self.vector_service_url}/index",
            json=index_request,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 索引构建成功: {self.index_name}")
            return result
        else:
            error_msg = f"向量服务返回错误: {response.status_code}, {response.text}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)


# 便捷函数
def build_prefab_index(
    json_path: str = None,
    force_reindex: bool = False,
    vector_service_url: str = None
) -> Dict[str, Any]:
    """
    构建预制件索引的便捷函数
    
    Args:
        json_path: community-prefabs.json 路径
        force_reindex: 是否强制重建
        vector_service_url: 向量服务地址
        
    Returns:
        索引构建结果
    """
    indexer = PrefabIndexer(vector_service_url)
    return indexer.build_index(json_path, force_reindex)


if __name__ == "__main__":
    # 测试代码
    result = build_prefab_index(force_reindex=True)
    print(f"\n索引构建结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

