"""
预制件索引构建模块

负责将 community-prefabs.json 中的预制件转换为向量索引，使用智谱AI的嵌入API和本地向量存储。
这不是一个 pocketflow node，而是独立的工具函数。
"""

import os
import json
import time
import requests
import pickle
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class LocalVectorStore:
    """本地向量存储"""

    def __init__(self, storage_dir: str = None):
        """
        初始化本地向量存储

        Args:
            storage_dir: 存储目录路径
        """
        if storage_dir is None:
            current_dir = Path(__file__).parent.parent.parent
            storage_dir = current_dir / "data" / "vector_store"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 存储文件路径
        self.vectors_file = self.storage_dir / "prefab_vectors.pkl"
        self.metadata_file = self.storage_dir / "prefab_metadata.json"
        self.index_file = self.storage_dir / "index_info.json"

        # 内存中的向量数据
        self.vectors = []
        self.documents = []
        self.index_info = {"total_count": 0, "last_updated": None}

        # 加载已有数据
        self._load_data()

    def _load_data(self):
        """从文件加载数据"""
        try:
            # 加载向量
            if self.vectors_file.exists():
                with open(self.vectors_file, 'rb') as f:
                    self.vectors = pickle.load(f)

            # 加载元数据
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)

            # 加载索引信息
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index_info = json.load(f)

        except Exception as e:
            print(f"⚠️ 加载向量数据失败: {e}")
            self.vectors = []
            self.documents = []
            self.index_info = {"total_count": 0, "last_updated": None}

    def _save_data(self):
        """保存数据到文件"""
        try:
            # 保存向量
            with open(self.vectors_file, 'wb') as f:
                pickle.dump(self.vectors, f)

            # 保存元数据
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)

            # 保存索引信息
            self.index_info["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index_info, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"❌ 保存向量数据失败: {e}")

    def clear(self):
        """清空所有数据"""
        self.vectors = []
        self.documents = []
        self.index_info = {"total_count": 0, "last_updated": None}
        self._save_data()

    def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        添加文档和对应的向量

        Args:
            documents: 文档列表
            embeddings: 向量列表
        """
        for doc, embedding in zip(documents, embeddings):
            self.documents.append(doc)
            self.vectors.append(np.array(embedding, dtype=np.float32))

        self.index_info["total_count"] = len(self.documents)
        self._save_data()

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        向量相似度搜索

        Args:
            query_vector: 查询向量
            top_k: 返回结果数量

        Returns:
            (文档, 相似度分数) 的列表
        """
        if not self.vectors:
            return []

        query_vec = np.array(query_vector, dtype=np.float32)

        # 计算相似度（余弦相似度）
        similarities = []
        for i, vec in enumerate(self.vectors):
            # 余弦相似度
            similarity = np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec))
            similarities.append((self.documents[i], float(similarity)))

        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """根据ID获取文档"""
        for doc in self.documents:
            if doc.get("id") == doc_id:
                return doc
        return None


class PrefabIndexer:
    """预制件索引构建器（适配智谱AI）"""

    def __init__(self, timeout: int = 30):
        """
        初始化索引构建器

        Args:
            timeout: 请求超时时间
        """
        from gtplanner.utils.config_manager import get_vector_service_config
        from gtplanner.utils.config_manager import get_llm_config

        # 获取LLM配置来获取API密钥
        llm_config = get_llm_config()
        self.api_key = llm_config.get("api_key")

        self.timeout = timeout

        # 从配置获取索引参数
        vector_config = get_vector_service_config()
        self.index_name = vector_config.get("prefabs_index_name", "document_gtplanner_prefabs")
        self.vector_field = vector_config.get("vector_field", "combined_text")

        # 初始化本地向量存储
        self.vector_store = LocalVectorStore()
    
    def check_vector_service_available(self) -> bool:
        """检查智谱AI嵌入服务是否可用"""
        if not self.api_key:
            print("❌ 智谱AI API密钥未配置")
            return False

        try:
            # 智谱AI嵌入API的标准地址
            embedding_url = "https://open.bigmodel.cn/api/paas/v4/embeddings"

            response = requests.post(
                embedding_url,
                json={
                    "model": "embedding-2",
                    "input": "test"
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                timeout=5
            )
            if response.status_code == 200:
                print("✅ 智谱AI嵌入服务连接正常")
                return True
            else:
                print(f"❌ 智谱AI API响应异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 智谱AI嵌入服务连接失败: {str(e)}")
            return False

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        调用智谱AI获取文本嵌入

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        if not texts:
            return []

        try:
            # 智谱AI嵌入API的标准地址
            embedding_url = "https://open.bigmodel.cn/api/paas/v4/embeddings"

            response = requests.post(
                embedding_url,
                json={
                    "model": "embedding-2",
                    "input": texts
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                timeout=self.timeout
            )

            if response.status_code != 200:
                error_msg = f"智谱AI API调用失败: {response.status_code}, {response.text}"
                print(f"❌ {error_msg}")
                raise RuntimeError(error_msg)

            result = response.json()
            embeddings = [item["embedding"] for item in result["data"]]
            return embeddings

        except Exception as e:
            print(f"❌ 获取嵌入失败: {str(e)}")
            raise
    
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

        # 检查智谱AI服务
        if not self.check_vector_service_available():
            return {
                "success": False,
                "error": "智谱AI嵌入服务不可用，请检查API密钥和网络连接",
                "index_name": None,
                "indexed_count": 0
            }

        try:
            # 1. 加载预制件
            prefabs = self.load_prefabs_from_json(json_path)
            print(f"📦 加载了 {len(prefabs)} 个预制件")

            # 2. 如果强制重建，先清空现有索引
            if force_reindex:
                self.vector_store.clear()
                print("🔄 已清空现有索引")

            # 3. 转换为文档格式
            documents = []
            for prefab in prefabs:
                doc = self.convert_prefab_to_document(prefab)
                documents.append(doc)

            print(f"📝 转换了 {len(documents)} 个文档")

            # 4. 批量获取嵌入向量
            texts = [doc[self.vector_field] for doc in documents]
            print("🔄 正在获取嵌入向量...")

            # 分批处理（智谱AI API可能有长度限制）
            batch_size = 10
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = self._get_embeddings(batch_texts)
                all_embeddings.extend(batch_embeddings)
                print(f"📊 已处理 {min(i + batch_size, len(texts))}/{len(texts)} 个向量")

            # 5. 存储到本地向量数据库
            self.vector_store.add_documents(documents, all_embeddings)

            elapsed_time = time.time() - start_time

            return {
                "success": True,
                "index_name": self.index_name,
                "indexed_count": len(documents),
                "elapsed_time": round(elapsed_time, 2),
                "vector_service": "智谱AI嵌入API",
                "local_storage_path": str(self.vector_store.storage_dir)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "index_name": None,
                "indexed_count": 0
            }
    
    def search_prefabs(self, query: str, top_k: int = 5) -> List[Tuple[Dict, float]]:
        """
        搜索预制件

        Args:
            query: 搜索查询
            top_k: 返回结果数量

        Returns:
            (文档, 相似度分数) 的列表
        """
        try:
            # 获取查询向量
            query_embeddings = self._get_embeddings([query])
            if not query_embeddings:
                return []

            query_vector = query_embeddings[0]

            # 在本地向量存储中搜索
            results = self.vector_store.search(query_vector, top_k)

            return results

        except Exception as e:
            print(f"❌ 搜索预制件失败: {str(e)}")
            return []

    def get_prefab_by_id(self, prefab_id: str) -> Optional[Dict]:
        """
        根据ID获取预制件

        Args:
            prefab_id: 预制件ID

        Returns:
            预制件文档
        """
        return self.vector_store.get_document_by_id(prefab_id)

    def get_index_info(self) -> Dict[str, Any]:
        """
        获取索引信息

        Returns:
            索引信息
        """
        return {
            "index_name": self.index_name,
            "total_count": self.vector_store.index_info["total_count"],
            "last_updated": self.vector_store.index_info["last_updated"],
            "storage_path": str(self.vector_store.storage_dir),
            "vector_service": "智谱AI嵌入API"
        }


# 便捷函数
def build_prefab_index(
    json_path: str = None,
    force_reindex: bool = False
) -> Dict[str, Any]:
    """
    构建预制件索引的便捷函数

    Args:
        json_path: community-prefabs.json 路径
        force_reindex: 是否强制重建

    Returns:
        索引构建结果
    """
    indexer = PrefabIndexer()
    return indexer.build_index(json_path, force_reindex)


if __name__ == "__main__":
    # 测试代码
    result = build_prefab_index(force_reindex=True)
    print(f"\n索引构建结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

