"""
预制件推荐节点 (Node_Prefab_Recommend)

基于向量服务进行预制件推荐。
如果向量服务不可用，节点会返回错误，agent 可以选择使用 search_prefabs 工具作为降级方案。
"""

import time
import requests
import asyncio
import json
from typing import Dict, List, Any, Optional
from pocketflow import AsyncNode
from gtplanner.utils.openai_client import OpenAIClient
from gtplanner.utils.config_manager import get_vector_service_config
from gtplanner.agent.streaming import (
    emit_processing_status,
    emit_error
)

# 导入多语言提示词系统
from gtplanner.agent.prompts import get_prompt, PromptTypes


class NodePrefabRecommend(AsyncNode):
    """预制件推荐节点（基于向量服务）"""
    
    def __init__(self, max_retries: int = 3, wait: float = 2.0):
        """
        初始化预制件推荐节点
        
        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)
        
        # 从配置文件加载向量服务配置
        vector_config = get_vector_service_config()
        self.vector_service_url = vector_config.get("base_url")
        self.timeout = vector_config.get("timeout", 30)
        
        # 从配置文件读取索引相关参数
        self.index_name = vector_config.get("prefabs_index_name", "document_gtplanner_prefabs")
        self.vector_field = vector_config.get("vector_field", "combined_text")
        
        # 推荐配置
        self.default_top_k = 5
        self.min_score_threshold = 0.4  # 最小相似度阈值（提高到0.4以过滤不相关结果）
        self.use_llm_filter = True  # 是否使用大模型筛选
        self.llm_candidate_count = 10  # 传给大模型的候选数量
        
        # 初始化OpenAI客户端
        self.openai_client = OpenAIClient()
        
        # 检查向量服务可用性
        self.vector_service_available = self._check_vector_service()
        
        if not self.vector_service_available:
            print("⚠️ 向量服务不可用，prefab_recommend 节点将无法工作")
            print("💡 提示：可以使用 search_prefabs 工具作为降级方案")
    
    def _check_vector_service(self) -> bool:
        """检查向量服务是否可用"""
        if not self.vector_service_url:
            return False
        try:
            response = requests.get(f"{self.vector_service_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    async def prep_async(self, shared) -> Dict[str, Any]:
        """
        准备阶段：从共享变量获取查询参数
        
        Args:
            shared: pocketflow字典共享变量
            
        Returns:
            准备结果字典
        """
        try:
            # 从共享变量获取查询参数
            query = shared.get("query", "")
            top_k = shared.get("top_k", self.default_top_k)
            index_name = shared.get("index_name", self.index_name)
            min_score = shared.get("min_score", self.min_score_threshold)
            use_llm_filter = shared.get("use_llm_filter", self.use_llm_filter)
            language = shared.get("language")
            
            # 如果没有提供查询，尝试从其他字段提取
            if not query:
                query = self._extract_query_from_shared_state(shared)
            
            # 验证输入
            if not query or not query.strip():
                return {
                    "error": "No query provided for prefab recommendation",
                    "query": "",
                    "top_k": top_k,
                    "index_name": index_name
                }
            
            # 预处理查询文本
            processed_query = query.strip()
            
            return {
                "query": processed_query,
                "original_query": query,
                "top_k": top_k,
                "index_name": index_name,
                "min_score": min_score,
                "use_llm_filter": use_llm_filter,
                "language": language,
                "streaming_session": shared.get("streaming_session")
            }
            
        except Exception as e:
            return {
                "error": f"Prefab recommendation preparation failed: {str(e)}",
                "query": "",
                "top_k": self.default_top_k,
                "index_name": self.index_name
            }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：调用向量服务进行预制件检索
        
        Args:
            prep_res: 准备阶段的结果
            
        Returns:
            执行结果字典
        """
        if "error" in prep_res:
            raise ValueError(prep_res["error"])
        
        query = prep_res["query"]
        top_k = prep_res["top_k"]
        index_name = prep_res["index_name"]
        min_score = prep_res["min_score"]
        use_llm_filter = prep_res["use_llm_filter"]
        language = prep_res["language"]
        
        if not query:
            raise ValueError("Empty query for prefab recommendation")
        
        if not self.vector_service_available:
            raise RuntimeError(
                "Vector service is not available. "
                "Please use 'search_prefabs' tool as a fallback."
            )
        
        try:
            start_time = time.time()
            
            # 调用向量服务进行检索（获取更多候选）
            search_top_k = max(top_k, self.llm_candidate_count) if use_llm_filter else top_k
            shared_for_events = {"streaming_session": prep_res.get("streaming_session")}
            search_results = await self._search_prefabs_vector(query, index_name, search_top_k, shared_for_events)
            
            # 过滤和处理结果
            filtered_results = self._filter_results(search_results, min_score=min_score)
            processed_results = self._process_results(filtered_results)
            
            # 使用大模型筛选（如果启用）
            if use_llm_filter and len(processed_results) > 1:
                try:
                    llm_selected_results = await self._llm_filter_prefabs(
                        query, processed_results, top_k, language, shared_for_events
                    )
                    processed_results = llm_selected_results
                    await emit_processing_status(
                        shared_for_events, 
                        f"✅ 大模型筛选完成，返回 {len(processed_results)} 个预制件"
                    )
                except Exception as e:
                    await emit_error(
                        shared_for_events, 
                        f"⚠️ 大模型筛选失败，使用原始排序: {str(e)}"
                    )
                    processed_results = processed_results[:top_k]
            else:
                processed_results = processed_results[:top_k]
            
            search_time = time.time() - start_time
            
            return {
                "recommended_prefabs": processed_results,
                "total_found": len(processed_results),
                "search_time": round(search_time * 1000),  # 转换为毫秒
                "query_used": query,
                "original_query": prep_res["original_query"],
                "search_mode": "vector_rag",
                "search_metadata": {
                    "index_name": index_name,
                    "top_k": top_k,
                    "min_score": min_score
                }
            }
            
        except Exception as e:
            raise RuntimeError(f"Prefab recommendation execution failed: {str(e)}")
    
    async def post_async(self, shared, prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理阶段：将推荐结果存储到共享状态
        
        Args:
            shared: 共享状态对象
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果
            
        Returns:
            下一步动作
        """
        try:
            if "error" in exec_res:
                if hasattr(shared, 'record_error'):
                    shared.record_error(Exception(exec_res["error"]), "NodePrefabRecommend.exec")
                return "error"
            
            recommended_prefabs = exec_res["recommended_prefabs"]
            total_found = exec_res["total_found"]
            
            # 检查是否是子流程的共享变量（字典类型）
            if isinstance(shared, dict):
                # 子流程模式：保存推荐结果到共享变量
                shared["recommended_prefabs"] = recommended_prefabs
                shared["prefab_recommendation_result"] = {
                    "prefabs": recommended_prefabs,
                    "total_found": total_found,
                    "query": exec_res["query_used"],
                    "search_time": exec_res["search_time"],
                    "search_mode": exec_res["search_mode"]
                }
                return "success"
            
            # 主流程模式：保存到研究发现或相应的状态
            if not hasattr(shared, 'prefab_recommendations'):
                shared.prefab_recommendations = []
            
            # 转换推荐结果为标准格式
            for prefab in recommended_prefabs:
                recommendation = {
                    "prefab_id": prefab["id"],
                    "prefab_name": prefab.get("summary", ""),
                    "description": prefab.get("description", ""),
                    "relevance_score": prefab.get("score", 0.0),
                    "tags": prefab.get("tags", ""),
                    "metadata": {
                        "version": prefab.get("version", ""),
                        "author": prefab.get("author", ""),
                        "repo_url": prefab.get("repo_url", ""),
                        "artifact_url": prefab.get("artifact_url", "")
                    },
                    "search_metadata": {
                        "query": exec_res["query_used"],
                        "search_time": exec_res["search_time"],
                        "search_mode": exec_res["search_mode"]
                    }
                }
                shared.prefab_recommendations.append(recommendation)
            
            # 添加系统消息记录推荐结果
            if hasattr(shared, 'add_system_message'):
                shared.add_system_message(
                    f"预制件推荐完成，找到 {total_found} 个相关预制件",
                    agent_source="NodePrefabRecommend",
                    query=exec_res["query_used"],
                    prefabs_count=total_found,
                    search_time_ms=exec_res["search_time"]
                )
            
            return "success"
            
        except Exception as e:
            if hasattr(shared, 'record_error'):
                shared.record_error(e, "NodePrefabRecommend.post")
            return "error"
    
    def exec_fallback(self, prep_res: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
        """
        执行失败时的降级处理
        
        Args:
            prep_res: 准备阶段结果
            exc: 异常对象
            
        Returns:
            错误信息
        """
        return {
            "error": f"Prefab recommendation execution failed: {str(exc)}",
            "recommended_prefabs": [],
            "total_found": 0,
            "query_used": prep_res.get("query", ""),
            "original_query": prep_res.get("original_query", ""),
            "search_mode": "failed"
        }
    
    def _extract_query_from_shared_state(self, shared) -> str:
        """从共享状态中提取查询文本"""
        query_candidates = []
        
        # 检查是否是子流程的共享变量（字典类型）
        if isinstance(shared, dict):
            if "user_query" in shared:
                query_candidates.append(shared["user_query"])
            if "search_query" in shared:
                query_candidates.append(shared["search_query"])
            if "task_description" in shared:
                query_candidates.append(shared["task_description"])
        else:
            # 主流程模式
            if hasattr(shared, 'user_intent') and hasattr(shared.user_intent, 'original_query'):
                query_candidates.append(shared.user_intent.original_query)
            if hasattr(shared, 'user_requirements') and shared.user_requirements:
                query_candidates.append(shared.user_requirements)
            if hasattr(shared, 'short_planning') and shared.short_planning:
                query_candidates.append(shared.short_planning)
        
        # 返回第一个非空的查询
        for candidate in query_candidates:
            if candidate and candidate.strip():
                return candidate.strip()
        
        return ""
    
    async def _search_prefabs_vector(
        self, 
        query: str, 
        index_name: str, 
        top_k: int,
        shared: Dict[str, Any]
    ) -> Dict[str, Any]:
        """调用向量服务进行预制件检索"""
        try:
            # 构建搜索请求
            search_request = {
                "query": query,
                "vector_field": self.vector_field,
                "index": index_name,
                "top_k": top_k
            }
            
            # 调用向量服务
            response = requests.post(
                f"{self.vector_service_url}/search",
                json=search_request,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                total_results = result.get('total', 0)
                
                # 打印每个预制件的相似度分数（调试用）
                if result.get('results'):
                    print(f"\n🔍 向量检索结果 (查询: '{query}'):")
                    for idx, item in enumerate(result['results'][:10], 1):
                        doc = item.get('document', {})
                        score = item.get('score', 0)
                        name = doc.get('name', 'Unknown')
                        print(f"  {idx}. [{score:.3f}] {name}")
                
                await emit_processing_status(
                    shared, 
                    f"✅ 检索到 {total_results} 个相关预制件"
                )
                return result
            else:
                error_msg = f"向量服务返回错误: {response.status_code}, {response.text}"
                await emit_error(shared, f"❌ {error_msg}")
                raise RuntimeError(error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"调用向量服务失败: {str(e)}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    def _filter_results(
        self, 
        search_results: Dict[str, Any],
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """过滤搜索结果"""
        if "results" not in search_results:
            return []
        
        filtered = []
        filtered_out_count = 0
        for result in search_results["results"]:
            # 检查相似度阈值
            score = result.get("score", 0.0)
            if score < min_score:
                filtered_out_count += 1
                continue
            
            # 添加分数到文档中
            document = result.get("document", {})
            document["score"] = score
            filtered.append(document)
        
        if filtered_out_count > 0:
            print(f"📊 相似度过滤: 保留 {len(filtered)} 个 (过滤掉 {filtered_out_count} 个，阈值: {min_score:.2f})")
        
        return filtered
    
    def _process_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """后处理搜索结果"""
        processed = []
        
        for result in results:
            # 确保必要字段存在
            processed_result = {
                "id": result.get("id", ""),
                "type": result.get("type", "PREFAB"),
                "summary": result.get("summary", ""),
                "description": result.get("description", ""),
                "tags": result.get("tags", ""),
                "score": result.get("score", 0.0),
                # 预制件特有字段
                "version": result.get("version", ""),
                "author": result.get("author", ""),
                "repo_url": result.get("repo_url", ""),
                "artifact_url": result.get("artifact_url", ""),
                "created_at": result.get("created_at", ""),
                "updated_at": result.get("updated_at", "")
            }
            
            processed.append(processed_result)
        
        # 按相似度分数排序
        processed.sort(key=lambda x: x["score"], reverse=True)
        
        return processed
    
    async def _llm_filter_prefabs(
        self, 
        query: str, 
        prefabs: List[Dict[str, Any]], 
        top_k: int,
        language: str,
        shared: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """使用大模型筛选最合适的预制件"""
        if not prefabs:
            return []
        
        # 构建提示词
        prompt = self._build_filter_prompt(query, prefabs, top_k, language)
        
        try:
            # 调用大模型
            messages = [{"role": "user", "content": prompt}]
            response = await self.openai_client.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )
            
            # 解析JSON响应
            response_content = response.choices[0].message.content
            try:
                # 清理响应内容
                cleaned_content = response_content.strip()
                if cleaned_content.startswith("```json"):
                    cleaned_content = cleaned_content[7:]
                if cleaned_content.startswith("```"):
                    cleaned_content = cleaned_content[3:]
                if cleaned_content.endswith("```"):
                    cleaned_content = cleaned_content[:-3]
                cleaned_content = cleaned_content.strip()
                
                response_json = json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                await emit_error(
                    shared, 
                    f"❌ 大模型返回的不是有效JSON: {response_content[:500]}... 错误: {str(e)}"
                )
                return []
            
            # 解析大模型响应
            selected_prefabs = await self._parse_llm_filter_response(response_json, prefabs, shared)
            
            return selected_prefabs
            
        except Exception as e:
            await emit_error(shared, f"❌ 大模型调用失败: {str(e)}")
            return []
    
    def _build_filter_prompt(
        self, 
        query: str, 
        prefabs: List[Dict[str, Any]], 
        top_k: int,
        language: str
    ) -> str:
        """构建大模型筛选的提示词"""
        # 构建预制件信息列表
        prefabs_info = []
        for i, prefab in enumerate(prefabs):
            prefab_info = {
                "index": i,
                "id": prefab["id"],
                "type": prefab["type"],
                "name": prefab["summary"],
                "description": prefab["description"][:500] + "..." if len(prefab["description"]) > 500 else prefab["description"],
                "tags": prefab.get("tags", "")
            }
            prefabs_info.append(prefab_info)
        
        # 使用多语言模板系统获取提示词
        prompt = get_prompt(
            PromptTypes.Agent.PREFAB_RECOMMENDATION,
            language=language,
            query=query,
            prefabs_info=json.dumps(prefabs_info, ensure_ascii=False, indent=2),
            top_k=top_k,
            prefabs_count=len(prefabs)-1
        )
        
        return prompt
    
    async def _parse_llm_filter_response(
        self, 
        response: Dict[str, Any], 
        original_prefabs: List[Dict[str, Any]],
        shared: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """解析大模型筛选响应"""
        try:
            if "selected_prefabs" not in response:
                await emit_error(shared, "⚠️ 大模型响应格式错误：缺少selected_prefabs字段")
                return []
            
            selected_prefabs = response["selected_prefabs"]
            if not isinstance(selected_prefabs, list):
                await emit_error(shared, "⚠️ 大模型响应格式错误：selected_prefabs不是列表")
                return []
            
            if not selected_prefabs:
                await emit_processing_status(shared, "✅ 大模型分析后认为没有合适的预制件")
                return []
            
            filtered_prefabs = []
            used_indices = set()
            
            for item in selected_prefabs:
                if not isinstance(item, dict) or "index" not in item:
                    continue
                
                index = item["index"]
                if not isinstance(index, int) or index < 0 or index >= len(original_prefabs):
                    continue
                
                if index in used_indices:
                    continue
                
                used_indices.add(index)
                prefab = original_prefabs[index].copy()
                prefab["llm_reason"] = item.get("reason", "")
                prefab["llm_selected"] = True
                filtered_prefabs.append(prefab)
            
            await emit_processing_status(
                shared, 
                f"✅ 大模型筛选解析成功，筛选出 {len(filtered_prefabs)} 个预制件"
            )
            if "analysis" in response:
                await emit_processing_status(shared, f"📝 大模型分析: {response['analysis']}")
            
            return filtered_prefabs
            
        except Exception as e:
            await emit_error(shared, f"❌ 解析大模型响应失败: {str(e)}")
            return []

