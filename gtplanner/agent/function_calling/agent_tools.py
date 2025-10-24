"""
Agent Function Calling工具包装器

将现有的子Agent节点直接包装为OpenAI Function Calling工具，
保持现有流程逻辑不变，只是提供Function Calling接口。
"""


from typing import Dict, List, Any, Optional

# 导入现有的子Agent流程
from gtplanner.agent.subflows.short_planning.flows.short_planning_flow import ShortPlanningFlow
from gtplanner.agent.subflows.research.flows.research_flow import ResearchFlow
# DesignFlow 在 _execute_design 中动态导入


def get_agent_function_definitions() -> List[Dict[str, Any]]:
    """
    获取所有Agent工具的Function Calling定义

    Returns:
        OpenAI Function Calling格式的工具定义列表
    """
    # 检查JINA_API_KEY是否可用
    from gtplanner.utils.config_manager import get_jina_api_key
    import os

    jina_api_key = get_jina_api_key() or os.getenv("JINA_API_KEY")
    # 确保API密钥不为空且不是占位符
    has_jina_api_key = bool(jina_api_key and jina_api_key.strip() and not jina_api_key.startswith("@format"))

    # 基础工具定义
    tools = [
        {
            "type": "function",
            "function": {
                "name": "short_planning",
                "description": "生成项目的步骤化实施计划。这是一个原子化的工具，所有需要的信息都通过参数显式传入。如果之前调用了 prefab_recommend 或 research，可以将它们的结果作为可选参数传入，以生成更完善的规划。此工具可以根据用户反馈被**重复调用**，直到与用户就项目规划达成最终共识。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_requirements": {
                            "type": "string",
                            "description": "用户的项目需求描述（必需）"
                        },
                        "previous_planning": {
                            "type": "string",
                            "description": "之前的规划内容（可选）。如果用户对之前的规划提出了修改意见，可以传入"
                        },
                        "improvement_points": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "用户提出的改进点或补充需求（可选）"
                        },
                        "recommended_prefabs": {
                            "type": "string",
                            "description": "推荐预制件信息（可选）。如果之前调用了 prefab_recommend 或 search_prefabs，可以将其结果的 JSON 字符串传入"
                        },
                        "research_findings": {
                            "type": "string",
                            "description": "技术调研结果（可选）。如果之前调用了 research，可以将其结果的 JSON 字符串传入"
                        }
                    },
                    "required": ["user_requirements"]
                }
            }
        },
    ]

    # 如果有JINA_API_KEY，添加research工具
    if has_jina_api_key:
        research_tool = {
            "type": "function",
            "function": {
                "name": "research",
                "description": "(可选工具) 用于对`prefab_recommend`推荐的技术栈进行深入的可行性或实现方案调研。**建议**在`prefab_recommend`成功调用之后使用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "需要调研的关键词列表，例如：['rag', '数据库设计']"
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "调研关注点，例如：['技术选型', '性能优化', '最佳实践', '架构设计']"
                        },
                        "project_context": {
                            "type": "string",
                            "description": "项目背景信息，帮助调研更有针对性"
                        }
                    },
                    "required": ["keywords", "focus_areas"]
                }
            }
        }
        tools.append(research_tool)

    # 添加design工具
    design_tool = {
        "type": "function",
        "function": {
            "name": "design",
            "description": "生成系统设计文档（design.md）。这是一个原子化的工具，所有需要的信息都通过参数显式传入。如果之前调用了 short_planning、prefab_recommend 或 research，可以将它们的结果作为可选参数传入，以生成更完善的设计文档。",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_requirements": {
                        "type": "string",
                        "description": "用户的项目需求描述（必需）"
                    },
                    "project_planning": {
                        "type": "string",
                        "description": "项目规划内容（可选）。如果之前调用了 short_planning，可以将其结果传入"
                    },
                    "recommended_prefabs": {
                        "type": "string",
                        "description": "推荐预制件信息（可选）。如果之前调用了 prefab_recommend 或 search_prefabs，可以将其结果的 JSON 字符串传入"
                    },
                    "research_findings": {
                        "type": "string",
                        "description": "技术调研结果（可选）。如果之前调用了 research，可以将其结果的 JSON 字符串传入"
                    }
                },
                "required": ["user_requirements"]
            }
        }
    }
    tools.append(design_tool)
    
    # 添加 search_prefabs 工具（降级方案，无需向量服务）
    search_prefabs_tool = {
        "type": "function",
        "function": {
            "name": "search_prefabs",
            "description": "在本地预制件库中搜索。这是一个降级工具，当向量服务不可用时使用。提供基于关键词、标签、作者的模糊搜索功能。**建议优先使用 prefab_recommend（如果向量服务可用），该工具提供更精准的语义匹配。**",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词，会在预制件的名称、描述、ID、标签中查找"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "标签过滤，至少匹配一个标签即可"
                    },
                    "author": {
                        "type": "string",
                        "description": "作者过滤，精确匹配作者名"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制，默认20",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 50
                    }
                },
                "required": []
            }
        }
    }
    tools.append(search_prefabs_tool)
    
    # 添加 prefab_recommend 工具（需要向量服务）
    prefab_recommend_tool = {
        "type": "function",
        "function": {
            "name": "prefab_recommend",
            "description": "基于向量语义检索推荐预制件。**这是推荐预制件的首选方法**，提供高精度的语义匹配。如果向量服务不可用，系统会提示使用 search_prefabs 作为降级方案。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "查询文本，描述需要的预制件功能或技术需求"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回的推荐预制件数量，默认5个",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    },
                    "use_llm_filter": {
                        "type": "boolean",
                        "description": "是否使用大模型进行二次筛选，默认true",
                        "default": True
                    }
                },
                "required": ["query"]
            }
        }
    }
    tools.append(prefab_recommend_tool)

    return tools


async def execute_agent_tool(tool_name: str, arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    执行Agent工具
    
    Args:
        tool_name: 工具名称
        arguments: 工具参数
        
    Returns:
        工具执行结果
    """
    try:
        # 确保 shared 字典存在
        if shared is None:
            shared = {}

        if tool_name == "short_planning":
            return await _execute_short_planning(arguments, shared)
        elif tool_name == "search_prefabs":
            return await _execute_search_prefabs(arguments, shared)
        elif tool_name == "prefab_recommend":
            return await _execute_prefab_recommend(arguments, shared)
        elif tool_name == "research":
            return await _execute_research(arguments, shared)
        elif tool_name == "design":
            return await _execute_design(arguments, shared)
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Tool execution failed: {str(e)}"
        }



async def _execute_short_planning(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """执行短期规划 - 原子化工具，所有参数显式传入"""
    user_requirements = arguments.get("user_requirements", "")
    previous_planning = arguments.get("previous_planning", "")
    improvement_points = arguments.get("improvement_points", [])
    recommended_prefabs = arguments.get("recommended_prefabs", "")
    research_findings = arguments.get("research_findings", "")

    # 验证必需参数
    if not user_requirements:
        return {
            "success": False,
            "error": "user_requirements is required"
        }

    try:
        # 创建独立的 flow_shared，实现原子化
        flow_shared = {
            "user_requirements": user_requirements,
            "previous_planning": previous_planning,
            "improvement_points": improvement_points,
            "recommended_prefabs": recommended_prefabs,
            "research_findings": research_findings,
            "language": shared.get("language") if shared else None,
            "streaming_session": shared.get("streaming_session") if shared else None  # 确保 SSE 支持
        }

        # 执行规划流程
        flow = ShortPlanningFlow()
        result = await flow.run_async(flow_shared)

        # 检查流程是否成功完成（返回"planning_complete"表示成功）
        if result == "planning_complete":
            # 从 flow_shared 中获取结果
            short_planning = flow_shared.get("short_planning", "")

            return {
                "success": True,
                "result": short_planning,
                "tool_name": "short_planning"
            }
        else:
            # 流程失败或返回错误
            error_msg = flow_shared.get('planning_error', flow_shared.get('short_planning_flow_error', f"短期规划执行失败，返回值: {result}"))
            return {
                "success": False,
                "error": error_msg,
                "tool_name": "short_planning"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"短期规划执行异常: {str(e)}",
            "tool_name": "short_planning"
        }


async def _execute_research(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """执行技术调研 - 使用ResearchFlow"""
    # 检查JINA_API_KEY环境变量
    from gtplanner.utils.config_manager import get_jina_api_key
    import os

    jina_api_key = get_jina_api_key() or os.getenv("JINA_API_KEY")
    # 确保API密钥不为空且不是占位符
    if not jina_api_key or not jina_api_key.strip() or jina_api_key.startswith("@format"):
        return {
            "success": False,
            "error": "❌ Research工具未启用：缺少JINA_API_KEY环境变量。请设置JINA_API_KEY后重试。",
            "tool_name": "research",
            "disabled_reason": "missing_jina_api_key"
        }

    keywords = arguments.get("keywords", [])
    focus_areas = arguments.get("focus_areas", [])
    project_context = arguments.get("project_context", "")

    # 参数验证
    if not keywords:
        return {
            "success": False,
            "error": "keywords is required and cannot be empty"
        }

    if not focus_areas:
        return {
            "success": False,
            "error": "focus_areas is required and cannot be empty"
        }

    try:
        # 使用完整的ResearchFlow
     

        # 直接在shared字典中添加工具参数，避免数据隔离
        if shared is None:
            shared = {}

        # 添加工具参数到shared字典
        shared["research_keywords"] = keywords
        shared["focus_areas"] = focus_areas
        shared["project_context"] = project_context

        # 直接使用shared字典执行流程，确保状态传递
        flow = ResearchFlow()
        success = await flow.run_async(shared)

        if success:
            # 从shared字典中获取结果（PocketFlow已经直接修改了shared）
            research_findings = shared.get("research_findings", {})

            return {
                "success": True,
                "result": research_findings,
                "tool_name": "research",
                "keywords_processed": len(keywords),
                "focus_areas": focus_areas
            }
        else:
            error_msg = shared.get('research_error', "研究流程执行失败")
            return {
                "success": False,
                "error": error_msg,
                "tool_name": "research"
            }

    except Exception as e:
        print(f"❌ 技术调研执行失败: {e}")
        return {
            "success": False,
            "error": f"Research execution failed: {str(e)}"
        }





async def _execute_design(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    执行设计 - 原子化工具，所有参数显式传入
    
    参数：
    - user_requirements: 必需，用户需求描述
    - project_planning: 可选，项目规划内容（如果之前调用了 short_planning）
    - recommended_prefabs: 可选，推荐预制件信息（JSON 字符串）
    - research_findings: 可选，技术调研结果（JSON 字符串）
    """
    import json
    
    # 验证必需参数
    user_requirements = arguments.get("user_requirements")
    if not user_requirements:
        return {
            "success": False,
            "error": "user_requirements is required"
        }
    
    # 获取可选参数（显式传入，不从 shared 读取）
    project_planning = arguments.get("project_planning", "")
    recommended_prefabs_str = arguments.get("recommended_prefabs", "")
    research_findings_str = arguments.get("research_findings", "")
    
    # 解析 JSON 字符串
    recommended_prefabs = []
    if recommended_prefabs_str:
        try:
            recommended_prefabs = json.loads(recommended_prefabs_str)
        except:
            pass
    
    research_findings = {}
    if research_findings_str:
        try:
            research_findings = json.loads(research_findings_str)
        except:
            pass
    
    try:
        # 创建独立的流程 shared 字典（不污染全局 shared）
        flow_shared = {
            "user_requirements": user_requirements,
            "short_planning": project_planning,
            "recommended_prefabs": recommended_prefabs,
            "research_findings": research_findings,
            "language": shared.get("language") if shared else None,  # 保留全局配置
            "streaming_session": shared.get("streaming_session") if shared else None  # 🔑 关键：传递 streaming_session
        }
        
        # 使用新的统一 DesignFlow
        from gtplanner.agent.subflows.design.flows.design_flow import DesignFlow
        flow = DesignFlow()
        
        print("🎨 生成设计文档...")
        
        # 执行流程
        result = await flow.run_async(flow_shared)
        
        # 从流程 shared 中获取结果
        agent_design_document = flow_shared.get("agent_design_document", "")
        
        # 如果全局 shared 存在，将结果同步回去（供后续使用）
        if shared:
            shared["agent_design_document"] = agent_design_document
            shared["documentation"] = agent_design_document
        
        # 判断成功
        if result and agent_design_document:
            return {
                "success": True,
                "message": "✅ 设计文档生成成功",
                "document": agent_design_document,
                "tool_name": "design"
            }
        else:
            error_msg = flow_shared.get('design_flow_error') or "设计文档生成失败：未生成文档"
            return {
                "success": False,
                "error": error_msg
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"设计执行异常: {str(e)}"
        }


async def _execute_search_prefabs(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    执行预制件搜索（本地模糊搜索，降级方案）
    
    这是一个简单的搜索工具，不依赖向量服务。
    适用于向量服务不可用时的降级场景。
    """
    query = arguments.get("query")
    tags = arguments.get("tags")
    author = arguments.get("author")
    limit = arguments.get("limit", 20)
    
    # 至少需要一个搜索条件
    if not query and not tags and not author:
        return {
            "success": False,
            "error": "At least one search parameter (query, tags, or author) is required"
        }
    
    try:
        from gtplanner.agent.utils.local_prefab_searcher import get_local_prefab_searcher
        
        # 获取搜索器实例
        searcher = get_local_prefab_searcher()
        
        # 执行搜索
        results = searcher.search(
            query=query,
            tags=tags,
            author=author,
            limit=limit
        )
        
        return {
            "success": True,
            "result": {
                "prefabs": results,
                "total_found": len(results),
                "search_mode": "local_fuzzy_search",
                "query": query,
                "tags": tags,
                "author": author
            },
            "tool_name": "search_prefabs"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"预制件搜索执行异常: {str(e)}"
        }


async def _execute_prefab_recommend(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    执行预制件推荐（基于向量服务，需要先构建索引）
    
    这是推荐预制件的首选方法，提供高精度的语义匹配。
    如果向量服务不可用，会返回错误提示使用 search_prefabs。
    """
    query = arguments.get("query", "")
    top_k = arguments.get("top_k", 5)
    use_llm_filter = arguments.get("use_llm_filter", True)
    
    # 参数验证
    if not query:
        return {
            "success": False,
            "error": "query is required and cannot be empty"
        }
    
    try:
        # 1. 检查向量服务是否可用
        from gtplanner.utils.config_manager import get_vector_service_config
        import requests
        
        vector_config = get_vector_service_config()
        vector_service_url = vector_config.get("base_url")
        
        # 检查向量服务健康状态
        vector_service_available = False
        if vector_service_url:
            try:
                response = requests.get(f"{vector_service_url}/health", timeout=5)
                vector_service_available = response.status_code == 200
            except:
                pass
        
        if not vector_service_available:
            return {
                "success": False,
                "error": "Vector service is not available. Please use 'search_prefabs' tool as a fallback.",
                "suggestion": f"Try calling search_prefabs with the same query: search_prefabs(query=\"{query}\")"
            }
        
        # 2. 使用索引管理器确保索引存在（启动时已预加载，这里只是确认）
        from gtplanner.agent.utils.prefab_index_manager import ensure_prefab_index
        
        # 智能检测：只在必要时重建（如文件更新）
        index_name = await ensure_prefab_index(
            force_reindex=False,
            shared=shared
        )
        
        if not index_name:
            return {
                "success": False,
                "error": "Failed to initialize prefab index"
            }
        
        # 3. 执行预制件推荐
        from gtplanner.agent.nodes.node_prefab_recommend import NodePrefabRecommend
        recommend_node = NodePrefabRecommend()
        
        # 准备参数
        if shared is None:
            shared = {}
        
        shared["query"] = query
        shared["top_k"] = top_k
        shared["index_name"] = index_name
        shared["min_score"] = 0.1
        shared["use_llm_filter"] = use_llm_filter
        
        # 执行推荐节点流程
        prep_result = await recommend_node.prep_async(shared)
        if "error" in prep_result:
            return {
                "success": False,
                "error": prep_result["error"]
            }
        
        exec_result = await recommend_node.exec_async(prep_result)
        
        # 后处理
        await recommend_node.post_async(shared, prep_result, exec_result)
        
        return {
            "success": True,
            "result": {
                "recommended_prefabs": exec_result["recommended_prefabs"],
                "total_found": exec_result["total_found"],
                "search_time_ms": exec_result["search_time"],
                "query_used": exec_result["query_used"],
                "search_mode": exec_result["search_mode"],
                "index_name": index_name
            },
            "tool_name": "prefab_recommend"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"预制件推荐执行异常: {str(e)}"
        }


def get_tool_by_name(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    根据名称获取工具定义
    
    Args:
        tool_name: 工具名称
        
    Returns:
        工具定义或None
    """
    tools = get_agent_function_definitions()
    for tool in tools:
        if tool["function"]["name"] == tool_name:
            return tool
    return None


def validate_tool_arguments(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证工具参数
    
    Args:
        tool_name: 工具名称
        arguments: 参数字典
        
    Returns:
        验证结果 {"valid": bool, "errors": List[str]}
    """
    tool_def = get_tool_by_name(tool_name)
    if not tool_def:
        return {"valid": False, "errors": [f"Unknown tool: {tool_name}"]}
    
    errors = []
    required_params = tool_def["function"]["parameters"].get("required", [])
    
    # 检查必需参数
    for param in required_params:
        if param not in arguments:
            errors.append(f"Missing required parameter: {param}")
    
    return {"valid": len(errors) == 0, "errors": errors}


# 便捷函数
async def call_short_planning(
    user_requirements: str = "",
    improvement_points: List[str] = None,
    planning_stage: str = "initial"
) -> Dict[str, Any]:
    """便捷的短期规划调用 - 自动使用项目状态中的数据

    Args:
        user_requirements: 用户需求描述
        improvement_points: 改进点列表
        planning_stage: 规划阶段，'initial'或'technical'
    """
    arguments = {}
    if user_requirements:
        arguments["user_requirements"] = user_requirements
    if improvement_points:
        arguments["improvement_points"] = improvement_points
    if planning_stage:
        arguments["planning_stage"] = planning_stage

    return await execute_agent_tool("short_planning", arguments)


async def call_research(keywords: List[str], focus_areas: List[str], project_context: str = "") -> Dict[str, Any]:
    """便捷的技术调研调用 - 基于关键词和关注点"""
    return await execute_agent_tool("research", {
        "keywords": keywords,
        "focus_areas": focus_areas,
        "project_context": project_context
    })


async def call_prefab_recommend(
    query: str,
    top_k: int = 5,
    use_llm_filter: bool = True
) -> Dict[str, Any]:
    """便捷的预制件推荐调用（向量检索）
    
    Args:
        query: 查询文本，描述需要的预制件功能
        top_k: 返回的推荐预制件数量，默认5
        use_llm_filter: 是否使用LLM进行二次筛选，默认True
    """
    arguments = {
        "query": query,
        "top_k": top_k,
        "use_llm_filter": use_llm_filter
    }
    return await execute_agent_tool("prefab_recommend", arguments)


async def call_search_prefabs(
    query: str = None,
    tags: List[str] = None,
    author: str = None,
    limit: int = 20
) -> Dict[str, Any]:
    """便捷的预制件搜索调用（本地模糊搜索）
    
    Args:
        query: 搜索关键词（可选）
        tags: 标签过滤列表（可选）
        author: 作者过滤（可选）
        limit: 返回结果数量限制，默认20
    """
    arguments = {"limit": limit}
    if query:
        arguments["query"] = query
    if tags:
        arguments["tags"] = tags
    if author:
        arguments["author"] = author
    
    return await execute_agent_tool("search_prefabs", arguments)


async def call_design(
    user_requirements: str,
    project_planning: str = None,
    recommended_prefabs: str = None,
    research_findings: str = None
) -> Dict[str, Any]:
    """便捷的设计文档生成调用 - 原子化工具

    Args:
        user_requirements: 用户需求描述（必需）
        project_planning: 项目规划内容（可选）
        recommended_prefabs: 推荐预制件信息 JSON 字符串（可选）
        research_findings: 技术调研结果 JSON 字符串（可选）
    """
    arguments = {"user_requirements": user_requirements}
    if project_planning:
        arguments["project_planning"] = project_planning
    if recommended_prefabs:
        arguments["recommended_prefabs"] = recommended_prefabs
    if research_findings:
        arguments["research_findings"] = research_findings
    return await execute_agent_tool("design", arguments)
