"""
本地预制件搜索工具（降级模式）

当向量服务不可用时，提供基础的模糊搜索功能。
作为 agent tool 使用，让 LLM 自己调用和判断搜索结果。
"""

import json
from typing import List, Dict, Any
from pathlib import Path


class LocalPrefabSearcher:
    """
    本地预制件搜索器
    
    提供简单的模糊搜索功能，返回匹配的预制件列表。
    让 LLM 自己判断和选择合适的预制件。
    """
    
    def __init__(self, prefabs_json_path: str = None):
        """
        初始化搜索器
        
        Args:
            prefabs_json_path: community-prefabs.json 文件路径，
                             如果为 None 则自动查找
        """
        if prefabs_json_path is None:
            # 自动定位 community-prefabs.json
            current_dir = Path(__file__).parent
            prefabs_json_path = current_dir.parent.parent.parent / "prefabs" / "releases" / "community-prefabs.json"
        
        self.prefabs_path = Path(prefabs_json_path)
        self.prefabs_cache: List[Dict] = None
        self.last_modified: float = None
    
    def load_prefabs(self) -> List[Dict]:
        """
        加载预制件列表，支持缓存和热更新
        
        Returns:
            预制件列表
        """
        if not self.prefabs_path.exists():
            raise FileNotFoundError(f"Prefabs JSON not found: {self.prefabs_path}")
        
        # 检查文件是否被修改
        current_mtime = self.prefabs_path.stat().st_mtime
        
        if self.prefabs_cache is None or current_mtime != self.last_modified:
            # 重新加载
            with open(self.prefabs_path, 'r', encoding='utf-8') as f:
                self.prefabs_cache = json.load(f)
            self.last_modified = current_mtime
        
        return self.prefabs_cache
    
    def search(
        self, 
        query: str = None, 
        tags: List[str] = None, 
        author: str = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        执行模糊搜索
        
        Args:
            query: 搜索关键词（会在 name 和 description 中搜索）
            tags: 标签过滤（可选）
            author: 作者过滤（可选）
            limit: 返回结果数量限制
            
        Returns:
            匹配的预制件列表
        """
        prefabs = self.load_prefabs()
        
        # 如果没有任何过滤条件，返回所有预制件（限制数量）
        if not query and not tags and not author:
            return prefabs[:limit]
        
        matched_prefabs = []
        
        for prefab in prefabs:
            # 检查是否匹配
            if self._is_match(prefab, query, tags, author):
                matched_prefabs.append(prefab)
        
        # 限制返回数量
        return matched_prefabs[:limit]
    
    def _is_match(
        self, 
        prefab: Dict, 
        query: str = None, 
        tags: List[str] = None,
        author: str = None
    ) -> bool:
        """
        检查预制件是否匹配搜索条件
        
        Args:
            prefab: 预制件对象
            query: 搜索关键词
            tags: 标签过滤
            author: 作者过滤
            
        Returns:
            是否匹配
        """
        # 作者过滤
        if author and prefab.get("author", "").lower() != author.lower():
            return False
        
        # 标签过滤
        if tags:
            prefab_tags = [t.lower() for t in prefab.get("tags", [])]
            # 至少匹配一个标签
            if not any(tag.lower() in prefab_tags for tag in tags):
                return False
        
        # 关键词搜索（支持拆分关键词）
        if query:
            query_lower = query.lower()
            name = prefab.get("name", "").lower()
            description = prefab.get("description", "").lower()
            prefab_id = prefab.get("id", "").lower()
            prefab_tags = " ".join(prefab.get("tags", [])).lower()

            # 方法1: 整个查询作为子串匹配
            if (query_lower in name or
                query_lower in description or
                query_lower in prefab_id or
                query_lower in prefab_tags):
                return True

            # 方法2: 拆分查询为多个关键词，至少匹配一个
            # 支持中文（按空格、标点拆分）和英文（按空格拆分）
            import re
            # 移除标点符号，保留中文、英文、数字、空格
            cleaned_query = re.sub(r'[^\w\s\u4e00-\u9fff]+', ' ', query_lower)
            # 拆分为关键词（去除空白词）
            keywords = [kw.strip() for kw in cleaned_query.split() if kw.strip() and len(kw.strip()) > 1]

            # 方法3: 对于没有空格的连续中文文本，提取有意义的子串（2-4个字符）
            # 检测条件：没有关键词，或者唯一的关键词过长（>10字符，说明没被正确拆分）
            has_long_unsplit_keyword = len(keywords) == 1 and len(keywords[0]) > 10
            if (not keywords or has_long_unsplit_keyword) and any('\u4e00' <= c <= '\u9fff' for c in query_lower):
                # 提取所有可能的2-4字符的中文子串
                for start in range(len(query_lower) - 1):
                    for length in [2, 3, 4]:
                        if start + length <= len(query_lower):
                            substring = query_lower[start:start + length]
                            # 只包含有意义的中文字符（跳过纯数字、字母）
                            if any('\u4e00' <= c <= '\u9fff' for c in substring):
                                keywords.append(substring)
                # 去重
                keywords = list(set(keywords))

            if keywords:
                # 至少匹配一个关键词
                for keyword in keywords:
                    if (keyword in name or
                        keyword in description or
                        keyword in prefab_id or
                        keyword in prefab_tags):
                        return True
                # 所有关键词都不匹配
                return False

            return False
        
        return True


# 全局单例
_local_searcher_instance = None


def get_local_prefab_searcher() -> LocalPrefabSearcher:
    """获取全局单例的本地搜索器"""
    global _local_searcher_instance
    if _local_searcher_instance is None:
        _local_searcher_instance = LocalPrefabSearcher()
    return _local_searcher_instance


if __name__ == "__main__":
    # 测试代码
    searcher = LocalPrefabSearcher()
    
    # 测试不同搜索场景
    print("=== 测试1: 关键词搜索 ===")
    results = searcher.search(query="hello", limit=5)
    print(f"找到 {len(results)} 个结果")
    for r in results:
        print(f"  - {r['name']} (ID: {r['id']})")
    
    print("\n=== 测试2: 标签搜索 ===")
    results = searcher.search(tags=["example"], limit=5)
    print(f"找到 {len(results)} 个结果")
    for r in results:
        print(f"  - {r['name']} (Tags: {r.get('tags', [])})")
    
    print("\n=== 测试3: 组合搜索 ===")
    results = searcher.search(query="demo", tags=["example"], limit=5)
    print(f"找到 {len(results)} 个结果")
    for r in results:
        print(f"  - {r['name']}")

