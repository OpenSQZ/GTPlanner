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
                            "type": "array",
                            "description": "推荐预制件列表（可选）。如果之前调用了 prefab_recommend 或 search_prefabs，请从结果中提取每个预制件的关键信息（id, version, name, description）",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "description": "预制件唯一标识符"
                                    },
                                    "version": {
                                        "type": "string",
                                        "description": "预制件版本号"
                                    },
                                    "name": {
                                        "type": "string",
                                        "description": "预制件名称"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "预制件功能描述"
                                    }
                                },
                                "required": ["id", "version", "name", "description"]
                            }
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
            "description": "生成系统设计文档（design.md），包含节点设计、Shared Store 等。这是一个原子化的工具，所有需要的信息都通过参数显式传入。如果之前调用了 short_planning、prefab_recommend、research，可以将它们的结果作为可选参数传入。**如果需要数据库持久化，应该在调用 design 之后再调用 database_design**。",
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
                        "type": "array",
                        "description": "推荐预制件列表。如果之前调用了 prefab_recommend 或 search_prefabs，请从结果中提取你觉得需要的预制件的关键信息（id, version, name, description）。**重要**：如果调用了 list_prefab_functions，请从查询结果中筛选出你认为与用户需求相关的函数（不是全部函数），并包含到 functions 字段中。",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "string",
                                    "description": "预制件唯一标识符"
                                },
                                "version": {
                                    "type": "string",
                                    "description": "预制件版本号"
                                },
                                "name": {
                                    "type": "string",
                                    "description": "预制件名称"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "预制件功能描述"
                                },
                                "functions": {
                                    "type": "array",
                                    "description": "预制件提供的相关函数列表（必须），需要先查询预制件都有哪些方法。**仅包含**你认为与用户需求相关的函数，不是预制件的全部函数。",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {
                                                "type": "string",
                                                "description": "函数名称"
                                            },
                                            "description": {
                                                "type": "string",
                                                "description": "函数描述"
                                            }
                                        }
                                    }
                                }
                            },
                            "required": ["id", "version", "name", "description","functions"]
                        }
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
    
    # TODO: 数据库设计工具暂时禁用，后续再开放
    # 添加 database_design 工具
    # database_design_tool = {
    #     "type": "function",
    #     "function": {
    #         "name": "database_design",
    #         "description": "⭐ （design 的后置工具）生成 MySQL 数据库表结构设计文档。**重要**：必须在 design 之后调用，因为需要基于系统设计中的 Shared Store 和节点定义来设计表结构。建议流程：先调用 design 生成系统设计，再调用 database_design 基于系统设计生成数据库表结构。这是一个原子化的工具，所有需要的信息都通过参数显式传入。",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "user_requirements": {
    #                     "type": "string",
    #                     "description": "用户的项目需求描述（必需）"
    #                 },
    #                 "system_design": {
    #                     "type": "string",
    #                     "description": "⭐ 系统设计文档（必需）。**必须**从 design 工具的返回结果中获取完整的设计文档内容，包含 Shared Store 和节点定义"
    #                 },
    #                 "project_planning": {
    #                     "type": "string",
    #                     "description": "项目规划内容（可选）。如果之前调用了 short_planning，可以将其结果传入"
    #                 },
    #                 "recommended_prefabs": {
    #                     "type": "array",
    #                     "description": "推荐预制件列表（可选）。如果之前调用了 prefab_recommend 或 search_prefabs，可以传入相关的数据库预制件信息",
    #                     "items": {
    #                         "type": "object",
    #                         "properties": {
    #                             "id": {
    #                                 "type": "string",
    #                                 "description": "预制件唯一标识符"
    #                             },
    #                             "version": {
    #                                 "type": "string",
    #                                 "description": "预制件版本号"
    #                             },
    #                             "name": {
    #                                 "type": "string",
    #                                 "description": "预制件名称"
    #                             },
    #                             "description": {
    #                                 "type": "string",
    #                                 "description": "预制件功能描述"
    #                             }
    #                         },
    #                         "required": ["id", "version", "name", "description"]
    #                     }
    #                 }
    #             },
    #             "required": ["user_requirements", "system_design"]
    #         }
    #     }
    # }
    # tools.append(database_design_tool)
    
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

    # 添加 list_prefab_functions 工具
    list_prefab_functions_tool = {
        "type": "function",
        "function": {
            "name": "list_prefab_functions",
            "description": "根据预制件 ID 查询该预制件的所有函数列表（仅包含函数名和描述）。**建议使用场景**：当 prefab_recommend 或 search_prefabs 返回预制件后，使用此工具查看预制件内部有哪些函数，判断是否符合需求。",
            "parameters": {
                "type": "object",
                "properties": {
                    "prefab_id": {
                        "type": "string",
                        "description": "预制件 ID，例如：'file-processing-prefab'"
                    },
                    "version": {
                        "type": "string",
                        "description": "版本号（可选），不指定则返回最新版本"
                    }
                },
                "required": ["prefab_id"]
            }
        }
    }
    tools.append(list_prefab_functions_tool)

    # 添加 get_function_details 工具
    get_function_details_tool = {
        "type": "function",
        "function": {
            "name": "get_function_details",
            "description": "根据预制件 ID 和函数名称获取该函数的完整定义（包括参数、返回值、文件定义等）。**建议使用场景**：在调用 list_prefab_functions 后，针对感兴趣的函数查看其详细定义，了解如何调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "prefab_id": {
                        "type": "string",
                        "description": "预制件 ID"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "函数名称"
                    },
                    "version": {
                        "type": "string",
                        "description": "版本号（可选），不指定则返回最新版本"
                    }
                },
                "required": ["prefab_id", "function_name"]
            }
        }
    }
    tools.append(get_function_details_tool)

    # 添加 call_prefab_function 工具
    call_prefab_function_tool = {
        "type": "function",
        "function": {
            "name": "call_prefab_function",
            "description": "直接调用预制件函数并获取实际执行结果。**建议使用场景**：在推荐预制件后，调用此工具验证预制件的实际效果，确认其是否真正符合用户需求。通过实际调用，可以将不确定的推荐过程固定为经过验证的实现方案。",
            "parameters": {
                "type": "object",
                "properties": {
                    "prefab_id": {
                        "type": "string",
                        "description": "预制件 ID"
                    },
                    "version": {
                        "type": "string",
                        "description": "版本号"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "函数名称"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "函数参数（JSON 对象）"
                    },
                    "files": {
                        "type": "object",
                        "description": "文件参数（可选，但是如果是需要处理文件的预制件必须填入s3地址），格式：{\"input\": [\"s3://...\"]}"
                    }
                },
                "required": ["prefab_id", "version", "function_name", "parameters"]
            }
        }
    }
    tools.append(call_prefab_function_tool)

    # 添加 request_file_upload 工具
    request_file_upload_tool = {
        "type": "function",
        "function": {
            "name": "request_file_upload",
            "description": "请求用户上传测试文件。当预制件函数需要文件输入时使用此工具。用户上传文件后会获得 S3 URL，然后你可以使用这些 URL 调用预制件函数。",
            "parameters": {
                "type": "object",
                "properties": {
                    "prefab_id": {
                        "type": "string",
                        "description": "预制件 ID"
                    },
                    "version": {
                        "type": "string",
                        "description": "版本号"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "函数名称"
                    },
                    "file_description": {
                        "type": "string",
                        "description": "文件用途描述，例如：'需要处理的PDF文档'、'待转录的音频文件'"
                    },
                    "accept": {
                        "type": "string",
                        "description": "接受的文件类型，例如：'.pdf,.doc,.docx'、'.mp3,.wav,.m4a'",
                        "default": ".pdf,.png,.jpg,.jpeg,.doc,.docx,.txt,.csv,.xlsx"
                    }
                },
                "required": ["prefab_id", "version", "function_name", "file_description"]
            }
        }
    }
    tools.append(request_file_upload_tool)

    # 添加 edit_document 工具（subagent 模式）
    edit_document_tool = {
        "type": "function",
        "function": {
            "name": "edit_document",
            "description": "编辑当前会话中已生成的设计文档。**这是一个智能子Agent**：你只需要用自然语言描述修改需求，子Agent会自动分析文档、生成精确的修改方案，并通过 diff 视图发送给前端供用户确认。",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_type": {
                        "type": "string",
                        "enum": ["design", "database_design"],
                        "description": "要编辑的文档类型"
                    },
                    "edit_instructions": {
                        "type": "string",
                        "description": "用自然语言描述的修改需求。例如：'在数据存储章节增加Redis缓存层的说明'、'优化性能部分，补充索引设计'、'修正用户认证流程中的安全问题'"
                    }
                },
                "required": ["document_type", "edit_instructions"]
            }
        }
    }
    tools.append(edit_document_tool)
    
    # 添加 view_document 工具
    view_document_tool = {
        "type": "function",
        "function": {
            "name": "view_document",
            "description": "查看当前会话中已生成的文档内容。每次调用都会返回最新的文档内容（包括用户确认的编辑）。**建议使用场景**：需要查看或引用文档内容时调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "要查看的文档文件名（如：design.md, prefabs_info.md, database_design.md）"
                    }
                },
                "required": ["filename"]
            }
        }
    }
    tools.append(view_document_tool)

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
        # TODO: 数据库设计工具暂时禁用，后续再开放
        # elif tool_name == "database_design":
        #     return await _execute_database_design(arguments, shared)
        elif tool_name == "edit_document":
            return await _execute_edit_document(arguments, shared)
        elif tool_name == "view_document":
            return await _execute_view_document(arguments, shared)
        elif tool_name == "list_prefab_functions":
            return await _execute_list_prefab_functions(arguments, shared)
        elif tool_name == "get_function_details":
            return await _execute_get_function_details(arguments, shared)
        elif tool_name == "call_prefab_function":
            return await _execute_call_prefab_function(arguments, shared)
        elif tool_name == "request_file_upload":
            return await _execute_request_file_upload(arguments, shared)
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
    """
    执行短期规划 - 原子化工具，所有参数显式传入
    
    参数：
    - user_requirements: 必需，用户需求描述
    - previous_planning: 可选，之前的规划内容
    - improvement_points: 可选，用户提出的改进点列表
    - recommended_prefabs: 可选，推荐预制件列表（数组格式）
    - research_findings: 可选，技术调研结果（JSON 字符串）
    """
    user_requirements = arguments.get("user_requirements", "")
    previous_planning = arguments.get("previous_planning", "")
    improvement_points = arguments.get("improvement_points", [])
    recommended_prefabs = arguments.get("recommended_prefabs", [])
    research_findings = arguments.get("research_findings", "")
    
    # 确保 recommended_prefabs 是列表类型
    if not isinstance(recommended_prefabs, list):
        recommended_prefabs = []

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
    - recommended_prefabs: 可选，推荐预制件信息（数组）
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
    recommended_prefabs = arguments.get("recommended_prefabs", [])
    research_findings_str = arguments.get("research_findings", "")
    
    # 确保 recommended_prefabs 是列表类型
    if not isinstance(recommended_prefabs, list):
        recommended_prefabs = []
    
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
            
            # 🔥 关键修复：将子 agent 的 generated_documents 同步回主 agent
            if "generated_documents" in flow_shared:
                if "generated_documents" not in shared:
                    shared["generated_documents"] = []
                # 合并文档（避免重复）
                existing_filenames = {doc.get("filename") for doc in shared["generated_documents"]}
                for doc in flow_shared["generated_documents"]:
                    if doc.get("filename") not in existing_filenames:
                        shared["generated_documents"].append(doc)
        
        # 判断成功
        if result and agent_design_document:
            return {
                "success": True,
                "message": "✅ 设计文档已生成并保存",
                "document_reference": {
                    "type": "design",
                    "filename": "design.md",
                    "location": "使用 view_document 工具查看完整内容"
                },
                "content_length": len(agent_design_document),
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


# TODO: 数据库设计工具暂时禁用，后续再开放
# 保留函数实现，暂时不提供给 LLM 调用
async def _execute_database_design(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    执行数据库表结构设计 - 原子化工具，所有参数显式传入
    
    参数：
    - user_requirements: 必需，用户需求描述
    - system_design: 必需，系统设计文档（必须从 design 工具的返回结果中获取）
    - project_planning: 可选，项目规划内容（如果之前调用了 short_planning）
    - recommended_prefabs: 可选，推荐预制件列表
    """
    # 验证必需参数
    user_requirements = arguments.get("user_requirements")
    if not user_requirements:
        return {
            "success": False,
            "error": "user_requirements is required"
        }
    
    # ⭐ 验证 system_design 参数（必需）
    system_design = arguments.get("system_design", "")
    if not system_design:
        return {
            "success": False,
            "error": "system_design is required. Please call 'design' first and pass its result to this tool.",
            "tool_name": "database_design"
        }
    
    # 获取可选参数（显式传入，不从 shared 读取）
    project_planning = arguments.get("project_planning", "")
    recommended_prefabs = arguments.get("recommended_prefabs", [])
    
    # 确保 recommended_prefabs 是列表类型
    if not isinstance(recommended_prefabs, list):
        recommended_prefabs = []
    
    try:
        # 创建独立的流程 shared 字典（不污染全局 shared）
        flow_shared = {
            "user_requirements": user_requirements,
            "system_design": system_design,  # ⭐ 传入系统设计文档
            "short_planning": project_planning,
            "recommended_prefabs": recommended_prefabs,
            "language": shared.get("language") if shared else None,  # 保留全局配置
            "streaming_session": shared.get("streaming_session") if shared else None  # 支持 SSE 流式输出
        }
        
        # 使用数据库设计流程
        from gtplanner.agent.subflows.database_design.flows.database_design_flow import DatabaseDesignFlow
        flow = DatabaseDesignFlow()
        
        print("🗄️  生成数据库表结构设计...")
        
        # 执行流程
        result = await flow.run_async(flow_shared)
        
        # 从流程 shared 中获取结果
        database_design = flow_shared.get("database_design", "")
        
        # 如果全局 shared 存在，将结果同步回去（供后续使用）
        if shared:
            shared["database_design"] = database_design
            
            # 🔥 关键修复：将子 agent 的 generated_documents 同步回主 agent
            if "generated_documents" in flow_shared:
                if "generated_documents" not in shared:
                    shared["generated_documents"] = []
                # 合并文档（避免重复）
                existing_filenames = {doc.get("filename") for doc in shared["generated_documents"]}
                for doc in flow_shared["generated_documents"]:
                    if doc.get("filename") not in existing_filenames:
                        shared["generated_documents"].append(doc)
        
        # 判断成功
        if result and database_design:
            return {
                "success": True,
                "message": "✅ 数据库表结构设计生成成功",
                "result": database_design,
                "tool_name": "database_design"
            }
        else:
            error_msg = flow_shared.get('database_design_error') or "数据库设计生成失败：未生成设计文档"
            return {
                "success": False,
                "error": error_msg,
                "tool_name": "database_design"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"数据库设计执行异常: {str(e)}",
            "tool_name": "database_design"
        }


async def _execute_edit_document(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    执行文档编辑 - 使用 DocumentEditFlow subagent（智能模式）

    参数：
    - document_type: 必需，文档类型 ("design" 或 "database_design")
    - edit_instructions: 必需，自然语言描述的修改需求

    工作流程：
    1. DocumentEditFlow subagent 读取当前文档
    2. 使用 LLM 理解 edit_instructions
    3. LLM 自动生成精确的 search/replace 操作
    4. 验证并生成修改提案
    5. 🔑 返回完整提案数据（不使用 SSE），包含 user_decision 字段
    """
    # 验证必需参数
    document_type = arguments.get("document_type")
    if not document_type:
        return {
            "success": False,
            "error": "document_type is required"
        }

    edit_instructions = arguments.get("edit_instructions")
    if not edit_instructions:
        return {
            "success": False,
            "error": "edit_instructions is required"
        }

    try:
        # 创建独立的流程 shared 字典
        flow_shared = {
            "document_type": document_type,
            "edit_instructions": edit_instructions,  # 自然语言描述
            # 从 shared 中传递已生成的文档
            "generated_documents": shared.get("generated_documents", []),
            "language": shared.get("language") if shared else None,
            "streaming_session": shared.get("streaming_session") if shared else None
        }

        # 使用 DocumentEditFlow
        from gtplanner.agent.subflows.document_edit.flows.document_edit_flow import DocumentEditFlow
        flow = DocumentEditFlow()

        print(f"📝 开始编辑文档: {document_type}")
        print(f"📋 修改需求: {edit_instructions}")

        # 执行流程（subagent 内部会调用 LLM 生成具体的编辑操作）
        result = await flow.run_async(flow_shared)

        # 从流程 shared 中获取结果
        proposal_id = flow_shared.get("edit_proposal_id")
        pending_edits = flow_shared.get("pending_document_edits", {})

        # 判断成功
        if result == "edit_proposal_generated" and proposal_id:
            # 🔑 关键变更：返回完整提案数据
            proposal_details = pending_edits.get(proposal_id, {})

            # 返回完整的提案数据，供 LLM 查看和前端处理
            return {
                "success": True,
                "message": "✅ 文档编辑提案已生成，等待用户确认",
                "proposal_id": proposal_id,
                "document_type": proposal_details.get("document_type"),
                "document_filename": proposal_details.get("document_filename"),
                "summary": proposal_details.get("summary", ""),
                "edits": proposal_details.get("edits", []),  # 🔑 完整编辑列表
                "preview_content": proposal_details.get("preview_content"),
                "user_decision": None,  # 🔑 空字段，等待前端填写（accepted/rejected）
                "timestamp": proposal_details.get("timestamp"),
                "tool_name": "edit_document"
            }
        else:
            error_msg = flow_shared.get('document_edit_error') or "文档编辑提案生成失败"
            return {
                "success": False,
                "error": error_msg,
                "tool_name": "edit_document"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"文档编辑执行异常: {str(e)}",
            "tool_name": "edit_document"
        }


async def _execute_view_document(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    查看已生成的文档内容

    参数：
    - filename: 必需，文档文件名（如：design.md, prefabs_info.md, database_design.md）
    """
    filename = arguments.get("filename")

    if not filename:
        return {
            "success": False,
            "error": "filename is required"
        }

    try:
        # 确保 shared 字典存在
        if shared is None:
            shared = {}

        # 获取已生成的文档列表
        generated_documents = shared.get("generated_documents", [])

        # 调试日志：打印当前的文档列表
        print(f"📖 查看文档: {filename}")
        print(f"📋 当前 generated_documents: {len(generated_documents)} 个文档")
        if generated_documents:
            doc_filenames = [doc.get("filename") for doc in generated_documents]
            print(f"📄 可用文档文件名: {doc_filenames}")
        else:
            print("⚠️  没有找到任何已生成的文档")

        # 准备 Node 所需的 shared 数据
        node_shared = {
            "filename": filename,
            "generated_documents": generated_documents,
            "streaming_session": shared.get("streaming_session") if shared else None
        }

        # 使用 NodeViewDocument 执行
        from gtplanner.agent.nodes import NodeViewDocument
        node = NodeViewDocument()

        # 执行节点
        result = await node.run_async(node_shared)
        
        # 返回结果，添加 tool_name
        if result and result.get("success"):
            result["tool_name"] = "view_document"
            print(f"✅ 查看文档成功: {result.get('filename')}")
            return result
        else:
            error_msg = result.get("error") if result else "查看文档失败"
            print(f"❌ 查看文档失败: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "tool_name": "view_document"
            }
    except Exception as e:
        print(f"❌ 查看文档执行异常: {str(e)}")
        return {
            "success": False,
            "error": f"查看文档执行异常: {str(e)}",
            "tool_name": "view_document"
        }


def _extract_keywords_from_query(query: str) -> list:
    """
    从查询字符串中提取关键词

    Args:
        query: 查询字符串（可能包含多个关键词，用标点符号分隔）

    Returns:
        关键词列表
    """
    import re

    # 移除常见的中文和英文标点符号，替换为空格
    cleaned = re.sub(r'[、。，,.\s、，．·]+', ' ', query)

    # 按空格分割并去除空白项
    keywords = [k.strip() for k in cleaned.split(' ') if k.strip()]

    # 如果只有一个关键词且长度较长（可能是完整句子），尝试按长度分割
    if len(keywords) == 1 and len(keywords[0]) > 10:
        # 对于中文，每 2-4 个字符可能是一个词
        main_keyword = keywords[0]
        if len(main_keyword) <= 15:
            # 返回完整的查询和可能的子关键词
            return [main_keyword]
        else:
            # 对于很长的查询，返回前几个词
            return [main_keyword[:4], main_keyword[:6], main_keyword[:8]]

    return keywords


async def _execute_search_prefabs(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    执行预制件搜索（本地模糊搜索，降级方案）

    这是一个简单的搜索工具，不依赖向量服务。
    适用于向量服务不可用时的降级场景。

    增强功能：自动从完整句子中提取关键词并进行多关键词搜索。
    """
    # 🔍 调试日志：打印接收到的参数
    print(f"   📋 search_prefabs 接收到的参数: {arguments}")

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

        # 首先尝试原始查询
        results = searcher.search(
            query=query,
            tags=tags,
            author=author,
            limit=limit
        )

        # 如果没有结果且查询包含标点符号（可能是多关键词查询），尝试关键词提取
        if not results and query and any(punct in query for punct in ['、', '。', ',', '.', ' ', '，', '．', '·']):
            keywords = _extract_keywords_from_query(query)
            print(f"   🔎 原查询无结果，尝试提取关键词: {keywords}")

            # 尝试每个关键词（最多 3 个）
            seen_ids = set()  # 用于去重
            max_keywords = min(3, len(keywords))

            for i in range(max_keywords):
                keyword_results = searcher.search(
                    query=keywords[i],
                    tags=tags,
                    author=author,
                    limit=limit
                )

                # 去重并添加结果
                for prefab in keyword_results:
                    prefab_id = prefab.get("id")
                    if prefab_id and prefab_id not in seen_ids:
                        seen_ids.add(prefab_id)
                        results.append(prefab)

            if results:
                print(f"   ✅ 关键词搜索找到 {len(results)} 个预制件")

        return {
            "success": True,
            "result": {
                "prefabs": results,
                "total_found": len(results),
                "search_mode": "local_fuzzy_search_with_keyword_extraction" if query and any(punct in query for punct in ['、', '。', ',', '.', ' ']) else "local_fuzzy_search",
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

        # 2. 从配置获取索引名称
        from gtplanner.utils.config_manager import get_vector_service_config
        vector_config = get_vector_service_config()
        index_name = vector_config.get("prefabs_index_name", "document_gtplanner_prefabs")

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
    recommended_prefabs: List[Dict[str, Any]] = None,
    research_findings: str = None
) -> Dict[str, Any]:
    """便捷的设计文档生成调用 - 原子化工具

    Args:
        user_requirements: 用户需求描述（必需）
        project_planning: 项目规划内容（可选）
        recommended_prefabs: 推荐预制件列表（可选）
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


async def call_database_design(
    user_requirements: str,
    system_design: str,
    project_planning: str = None,
    recommended_prefabs: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """便捷的数据库表结构设计调用 - 原子化工具

    Args:
        user_requirements: 用户需求描述（必需）
        system_design: 系统设计文档（必需）- 必须从 call_design 的返回结果中获取
        project_planning: 项目规划内容（可选）
        recommended_prefabs: 推荐预制件列表（可选）
    """
    arguments = {
        "user_requirements": user_requirements,
        "system_design": system_design
    }
    if project_planning:
        arguments["project_planning"] = project_planning
    if recommended_prefabs:
        arguments["recommended_prefabs"] = recommended_prefabs
    return await execute_agent_tool("database_design", arguments)


async def _execute_list_prefab_functions(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    执行预制件函数列表查询

    参数：
    - prefab_id: 必需，预制件 ID
    - version: 可选，版本号（不指定则返回最新版本）

    注意：此函数不应该发送 emit_tool_start 和 emit_tool_end 事件，
    因为 ToolExecutor 已经统一处理了这些事件。
    """
    import httpx
    import time
    from gtplanner.agent.streaming import (
        emit_tool_progress,
        emit_processing_status
    )

    prefab_id = arguments.get("prefab_id")
    version = arguments.get("version")

    # 参数验证
    if not prefab_id:
        if shared:
            await emit_processing_status(shared, "❌ 参数错误：缺少 prefab_id")
        return {
            "success": False,
            "error": "prefab_id is required",
            "tool_name": "list_prefab_functions"
        }

    start_time = time.time()

    try:
        # 🆕 发送工具进度事件（不发送 start 事件，ToolExecutor 已经发送了）
        if shared:
            await emit_tool_progress(
                shared,
                tool_name="list_prefab_functions",
                message=f"正在查询: {prefab_id}" + (f"@{version}" if version else "")
            )

        # 从配置获取 prefab-gateway 地址
        from gtplanner.utils.config_manager import get_prefab_gateway_url
        gateway_url = get_prefab_gateway_url()

        if not gateway_url:
            if shared:
                await emit_processing_status(shared, "❌ Prefab gateway URL 未配置")
            return {
                "success": False,
                "error": "Prefab gateway URL not configured",
                "tool_name": "list_prefab_functions"
            }

        # 构建请求 URL
        url = f"{gateway_url}/v1/public/prefabs/{prefab_id}/functions"
        params = {}
        if version:
            params["version"] = version

        # 发起 HTTP 请求
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            functions = response.json()

        execution_time = time.time() - start_time

        # 发送处理状态信息（不发送 end 事件，ToolExecutor 会发送）
        if shared:
            await emit_processing_status(
                shared,
                f"✅ 查询成功！\n"
                f"📦 预制件: {prefab_id}" + (f"@{version}" if version else "") + "\n"
                f"🔧 函数数量: {len(functions)}\n"
                f"⏱️  执行时间: {execution_time:.2f}s"
            )

        # 格式化返回结果
        return {
            "success": True,
            "result": {
                "prefab_id": prefab_id,
                "version": version or "latest",
                "functions": functions,
                "total_functions": len(functions)
            },
            "tool_name": "list_prefab_functions"
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            error_msg = f"Prefab '{prefab_id}' not found" + (f" (version: {version})" if version else "")
        else:
            error_msg = f"HTTP error: {e.response.status_code} - {e.response.text}"

        if shared:
            await emit_processing_status(shared, f"❌ 查询失败: {error_msg}")

        return {
            "success": False,
            "error": error_msg,
            "tool_name": "list_prefab_functions"
        }
    except Exception as e:
        error_msg = f"Failed to fetch prefab functions: {str(e)}"

        if shared:
            await emit_processing_status(shared, f"❌ 查询异常: {error_msg}")

        return {
            "success": False,
            "error": error_msg,
            "tool_name": "list_prefab_functions"
        }


async def _execute_get_function_details(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    执行预制件函数详情查询

    参数：
    - prefab_id: 必需，预制件 ID
    - function_name: 必需，函数名称
    - version: 可选，版本号（不指定则返回最新版本）

    注意：此函数不应该发送 emit_tool_start 和 emit_tool_end 事件，
    因为 ToolExecutor 已经统一处理了这些事件。
    """
    import httpx
    import time
    from gtplanner.agent.streaming import (
        emit_tool_progress,
        emit_processing_status
    )

    prefab_id = arguments.get("prefab_id")
    function_name = arguments.get("function_name")
    version = arguments.get("version")

    # 参数验证
    if not prefab_id:
        if shared:
            await emit_processing_status(shared, "❌ 参数错误：缺少 prefab_id")
        return {
            "success": False,
            "error": "prefab_id is required",
            "tool_name": "get_function_details"
        }

    if not function_name:
        if shared:
            await emit_processing_status(shared, "❌ 参数错误：缺少 function_name")
        return {
            "success": False,
            "error": "function_name is required",
            "tool_name": "get_function_details"
        }

    start_time = time.time()

    try:
        # 发送工具进度事件（不发送 start 事件，ToolExecutor 已经发送了）
        if shared:
            await emit_tool_progress(
                shared,
                tool_name="get_function_details",
                message=f"正在查询: {prefab_id}.{function_name}" + (f"@{version}" if version else "")
            )

        # 从配置获取 prefab-gateway 地址
        from gtplanner.utils.config_manager import get_prefab_gateway_url
        gateway_url = get_prefab_gateway_url()

        if not gateway_url:
            if shared:
                await emit_processing_status(shared, "❌ Prefab gateway URL 未配置")
            return {
                "success": False,
                "error": "Prefab gateway URL not configured",
                "tool_name": "get_function_details"
            }

        # 构建请求 URL
        url = f"{gateway_url}/v1/public/prefabs/{prefab_id}/functions/{function_name}"
        params = {}
        if version:
            params["version"] = version

        # 发起 HTTP 请求
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            function_details = response.json()

        execution_time = time.time() - start_time

        # 发送处理状态信息（不发送 end 事件，ToolExecutor 会发送）
        if shared:
            await emit_processing_status(
                shared,
                f"✅ 查询成功！\n"
                f"📦 预制件: {prefab_id}" + (f"@{version}" if version else "") + "\n"
                f"🔧 函数: {function_name}\n"
                f"⏱️  执行时间: {execution_time:.2f}s"
            )

        # 格式化返回结果
        return {
            "success": True,
            "result": {
                "prefab_id": prefab_id,
                "version": version or "latest",
                "function": function_details
            },
            "tool_name": "get_function_details"
        }

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            error_detail = e.response.json().get("detail", "Not found")
        else:
            error_detail = f"HTTP error: {e.response.status_code} - {e.response.text}"

        if shared:
            await emit_processing_status(shared, f"❌ 查询失败: {error_detail}")

        return {
            "success": False,
            "error": error_detail,
            "tool_name": "get_function_details"
        }
    except Exception as e:
        error_msg = f"Failed to fetch function details: {str(e)}"

        if shared:
            await emit_processing_status(shared, f"❌ 查询异常: {error_msg}")

        return {
            "success": False,
            "error": error_msg,
            "tool_name": "get_function_details"
        }


async def _execute_call_prefab_function(arguments: Dict[str, Any], shared: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    执行预制件函数调用

    参数：
    - prefab_id: 必需，预制件 ID
    - version: 必需，版本号
    - function_name: 必需，函数名称
    - parameters: 必需，函数参数（JSON 对象）
    - files: 可选，文件参数
    """
    try:
        # 确保 shared 字典存在
        if shared is None:
            shared = {}

        # 提取参数
        prefab_id = arguments.get("prefab_id")
        version = arguments.get("version")
        function_name = arguments.get("function_name")
        parameters = arguments.get("parameters", {})
        files = arguments.get("files")

        # 准备节点 shared 数据
        node_shared = {
            "prefab_id": prefab_id,
            "version": version,
            "function_name": function_name,
            "parameters": parameters,
            "files": files
        }

        # 使用 NodeCallPrefabFunction 执行
        from gtplanner.agent.nodes import NodeCallPrefabFunction
        node = NodeCallPrefabFunction()

        # 执行节点
        prep_result = await node.prep_async(node_shared)
        if not prep_result.get("success"):
            return {
                "success": False,
                "error": prep_result.get("error"),
                "hint": prep_result.get("hint"),
                "tool_name": "call_prefab_function"
            }

        exec_result = await node.exec_async(prep_result)

        # 后处理
        await node.post_async(shared, prep_result, exec_result)

        # 返回结果
        if exec_result.get("success"):
            return {
                "success": True,
                "result": {
                    "prefab_id": exec_result["prefab_id"],
                    "version": exec_result["version"],
                    "function_name": exec_result["function_name"],
                    "function_result": exec_result["function_result"],
                    "output_files": exec_result.get("output_files"),
                    "job_id": exec_result.get("job_id")
                },
                "tool_name": "call_prefab_function"
            }
        else:
            return {
                "success": False,
                "error": exec_result.get("error"),
                "prefab_id": exec_result.get("prefab_id"),
                "version": exec_result.get("version"),
                "function_name": exec_result.get("function_name"),
                "tool_name": "call_prefab_function"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to call prefab function: {str(e)}",
            "tool_name": "call_prefab_function"
        }


async def _execute_request_file_upload(arguments: Dict[str, Any], shared: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    请求用户上传文件

    参数：
    - prefab_id: 必需，预制件 ID
    - version: 必需，版本号
    - function_name: 必需，函数名称
    - file_description: 必需，文件用途描述
    - accept: 可选，接受的文件类型
    """
    try:
        prefab_id = arguments.get("prefab_id")
        version = arguments.get("version")
        function_name = arguments.get("function_name")
        file_description = arguments.get("file_description")
        accept = arguments.get("accept", ".pdf,.png,.jpg,.jpeg,.doc,.docx,.txt,.csv,.xlsx")

        # 参数验证
        if not prefab_id:
            return {
                "success": False,
                "error": "prefab_id is required",
                "tool_name": "request_file_upload"
            }

        if not version:
            return {
                "success": False,
                "error": "version is required",
                "tool_name": "request_file_upload"
            }

        if not function_name:
            return {
                "success": False,
                "error": "function_name is required",
                "tool_name": "request_file_upload"
            }

        if not file_description:
            return {
                "success": False,
                "error": "file_description is required",
                "tool_name": "request_file_upload"
            }

        # 发送 SSE 事件
        if shared:
            from gtplanner.agent.streaming import emit_processing_status
            await emit_processing_status(
                shared,
                f"📁 请求用户上传文件\n"
                f"📦 预制件: {prefab_id}@{version}\n"
                f"🔧 函数: {function_name}\n"
                f"📝 用途: {file_description}"
            )

        # 返回文件上传请求
        return {
            "success": True,
            "result": {
                "prefab_id": prefab_id,
                "version": version,
                "function_name": function_name,
                "file_description": file_description,
                "accept": accept,
                "message": f"请上传{file_description}。上传成功后，请在消息中包含 S3 URL（格式：s3://bucket/path/file.ext），然后我会继续调用预制件函数。"
            },
            "tool_name": "request_file_upload"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to request file upload: {str(e)}",
            "tool_name": "request_file_upload"
        }

