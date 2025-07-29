from typing import Any, Optional, List, Dict

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from utils.multilingual_utils import determine_language
from utils.context_manager import optimize_conversation_context  # 启用上下文压缩功能

# 导入规划相关的功能
from api.v1.planning import (
    short_planning, long_planning,
    short_planning_stream, long_planning_stream,
    ShortPlanningRequest, LongPlanningRequest
)

chat_router = APIRouter(prefix="/chat", tags=["chat"])


def stream_data(content: str) -> bytes:
    """
    封装流式输出数据，确保UTF-8编码，每行以换行符结尾（SSE格式要求）
    使用占位符保护markdown换行符，避免与SSE协议冲突
    """
    # 将换行符替换为占位符，避免与SSE消息分隔符冲突
    protected_content = content.replace('\n', '<|newline|>')
    return f"data: {protected_content}\n".encode('utf-8')


def stream_data_block(content: str) -> bytes:
    """
    封装流式输出数据块，确保UTF-8编码，并添加结束标记
    """
    return f"data: {content}\n\n".encode('utf-8')


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    message_type: Optional[str] = "message"  # 'message', 'plan', 'document'
    timestamp: Optional[int] = None


class ConversationRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    session_id: Optional[str] = None
    language: Optional[str] = None
    action: Optional[str] = None  # 'generate_document'
    context: Optional[Dict[str, Any]] = None


class ConversationAction(BaseModel):
    type: str  # 'plan', 'document', 'suggestion'
    content: str
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    language: Optional[str] = None
    user_id: Optional[str] = None


class IntentAnalysisResult(BaseModel):
    intent: str  # 'requirement' or 'conversation'
    confidence: float
    reasoning: str

async def process_intent_actions(intent: str, message: str, current_plan: str, actions: List[Dict], language: str) -> List[ConversationAction]:
    """
    根据意图处理特殊操作，如生成规划或文档
    """
    processed_actions = []

    try:
        if intent == "requirement":
            # 生成短规划
            planning_request = ShortPlanningRequest(
                requirement=message,
                language=language
            )
            planning_result = await short_planning(planning_request)

            if "flow" in planning_result:
                processed_actions.append(ConversationAction(
                    type="plan",
                    content=planning_result["flow"],
                    title="项目规划" if language == "zh" else "Project Plan",
                    metadata={
                        "language": planning_result.get("language", language),
                        "version": 1
                    }
                ))

        elif intent == "optimization" and current_plan:
            # 优化现有规划
            planning_request = ShortPlanningRequest(
                requirement=message,
                previous_flow=current_plan,
                language=language
            )
            planning_result = await short_planning(planning_request)

            if "flow" in planning_result:
                processed_actions.append(ConversationAction(
                    type="plan",
                    content=planning_result["flow"],
                    title="优化规划" if language == "zh" else "Optimized Plan",
                    metadata={
                        "language": planning_result.get("language", language),
                        "based_on": current_plan[:100] + "..." if len(current_plan) > 100 else current_plan,
                        "version": 2
                    }
                ))

        elif intent == "document_generation" and current_plan:
            # 生成长文档
            doc_request = LongPlanningRequest(
                requirement=message,
                previous_flow=current_plan,
                language=language
            )
            doc_result = await long_planning(doc_request)

            if "flow" in doc_result:
                processed_actions.append(ConversationAction(
                    type="document",
                    content=doc_result["flow"],
                    title="设计文档" if language == "zh" else "Design Document",
                    metadata={
                        "language": doc_result.get("language", language),
                        "based_on": current_plan[:100] + "..." if len(current_plan) > 100 else current_plan
                    }
                ))

        # 处理LLM建议的其他actions
        for action in actions:
            if isinstance(action, dict) and "type" in action and "content" in action:
                processed_actions.append(ConversationAction(
                    type=action.get("type", "suggestion"),
                    content=action.get("content", ""),
                    title=action.get("title"),
                    metadata=action.get("metadata", {})
                ))

    except Exception as e:
        print(f"Error processing intent actions: {e}")
        # 如果处理失败，返回一个建议action
        processed_actions.append(ConversationAction(
            type="suggestion",
            content="处理您的请求时遇到问题，请尝试重新描述您的需求。" if language == "zh" else "There was an issue processing your request. Please try rephrasing your needs.",
            title="建议" if language == "zh" else "Suggestion"
        ))

    return processed_actions


async def handle_action(action_content: str, original_message: str, current_plan: str, language: str, conversation_history: Optional[List[ChatMessage]] = None):
    """
    处理ACTION标签，调用相应的流式planning接口并返回流式结果
    """
    try:
        # 解析action类型和内容
        if action_content.startswith("short_plan:"):
            requirement = action_content[11:].strip() or original_message

            # 调用流式短规划接口
            planning_request = ShortPlanningRequest(
                requirement=requirement,
                language=language
            )
            async for chunk in short_planning_stream(planning_request):
                if isinstance(chunk, str):
                    # short_planning_stream已经返回格式化的SSE数据，直接输出
                    yield chunk.encode('utf-8')
                else:
                    yield chunk



        elif action_content.startswith("long_doc:"):
            # LONG_DOC_ACTION不使用标签内容，使用固定的文档生成需求
            doc_requirement = "基于当前规划生成详细的设计文档" if language == "zh" else "Generate detailed design document based on current plan"

            # 调用流式长文档生成，使用context.current_plan
            doc_request = LongPlanningRequest(
                requirement=doc_requirement,
                previous_flow=current_plan,
                language=language
            )
            async for chunk in long_planning_stream(doc_request):
                if isinstance(chunk, str):
                    # long_planning_stream已经返回格式化的SSE数据，直接输出
                    yield chunk.encode('utf-8')
                else:
                    yield chunk

        elif action_content.startswith("full_flow:"):
            requirement = action_content[10:].strip() or original_message

            # 先执行短规划
            planning_request = ShortPlanningRequest(
                requirement=requirement,
                language=language
            )

            # 收集短规划的结果
            plan_result = ""
            async for chunk in short_planning_stream(planning_request):
                if isinstance(chunk, str):
                    yield chunk.encode('utf-8')
                    # 提取规划内容（去除SSE格式）
                    if chunk.startswith("data: ") and not chunk.startswith("data: ["):
                        plan_content = chunk[6:].replace('<|newline|>', '\n').strip()
                        if plan_content:
                            plan_result += plan_content + "\n"
                else:
                    yield chunk

            # 等待短规划完成后，自动触发长文档生成
            if plan_result.strip():
                # 调用流式长文档生成，使用刚生成的规划作为previous_flow
                doc_request = LongPlanningRequest(
                    requirement=requirement,
                    previous_flow=plan_result.strip(),
                    language=language
                )
                async for chunk in long_planning_stream(doc_request):
                    if isinstance(chunk, str):
                        yield chunk.encode('utf-8')
                    else:
                        yield chunk

    except Exception as e:
        # 记录详细错误信息用于调试
        import logging
        logging.error(f"Error in handle_action: {str(e)}", exc_info=True)

        # 向用户返回通用错误信息，不暴露内部细节
        yield stream_data("[ERROR_START]")
        yield stream_data("❌ An internal error occurred while processing the action. Please try again later.")
        yield stream_data_block("[ERROR_END]")


async def generate_stream_response(
    message: str,
    conversation_history: List[ChatMessage],
    session_id: Optional[str],
    language: str,
    context: Dict[str, Any]
):
    """
    生成基于标签的流式响应
    """
    try:
        # 发送状态信息
        yield stream_data("[STATUS_START]")
        yield stream_data("🔄 正在分析您的需求...")
        yield stream_data_block("[STATUS_END]")

        # 提取上下文信息
        current_plan = context.get("current_plan", "")

        # 禁用上下文压缩功能，直接使用原始对话历史
        # TODO: 后续研究更智能的压缩方案时可以重新启用以下代码
        # 转换消息格式
        history_dicts = []
        for msg in conversation_history:
            history_dicts.append({
                "role": msg.role,
                "content": msg.content,
                "message_type": msg.message_type,
                "timestamp": msg.timestamp
            })
    
        # 优化上下文
        context_str, context_stats = await optimize_conversation_context(
            history_dicts, message
        )

        # # 直接处理原始对话历史，分离系统提示词和用户聊天记录
        # user_conversation_history = []
        # for msg in conversation_history:
        #     # 包含用户和助手的对话消息和规划消息，排除系统消息、文档和分析消息
        #     # plan消息相对简洁且是对话的重要组成部分，应该保留在上下文中
        #     # document和analysis消息通常很长，会占用过多token，因此排除
        #     if msg.role in ["user", "assistant"] and msg.message_type in ["message", "plan"]:
        #         msg_content = f"{msg.role}: {msg.content}"
        #         user_conversation_history.append(msg_content)

        # # 构建纯净的用户对话历史字符串
        # context_str = "\n".join(user_conversation_history) if user_conversation_history else "这是对话的开始。"

        # 构建分离的系统提示词和用户对话上下文
        if language == "zh":
            # 系统提示词部分（包含所有系统指令，独立于用户对话历史）
            system_prompt = """你是GTPlanner的AI助手，核心任务是分析用户意图，并根据预设格式输出指令。

#### **1. 核心任务**
分析用户在对话上下文中的意图，从以下四种类型中选择一种并按要求回应：
*   **项目规划 (Project Planning)**: 用户提出新项目、新功能或优化建议。
*   **文档生成 (Document Generation)**: 用户明确要求生成设计或技术文档。
*   **完整流程 (Full Flow)**: 用户提出复杂项目需求，适合一次性生成规划和文档。
*   **普通对话 (Conversation)**: 日常问候、感谢、或一般性提问。

#### **2. 输出格式 (必须严格遵守)**
*   **普通对话**: `[TEXT_START]你的回复内容[TEXT_END]`
*   **项目规划**: `[SHORT_PLAN_ACTION_START]完整的最终需求列表[SHORT_PLAN_ACTION_END]`
*   **文档生成**: `[LONG_DOC_ACTION_START][LONG_DOC_ACTION_END]` (标签内无内容)
*   **完整流程**: `[FULL_FLOW_ACTION_START]完整的最终需求列表[FULL_FLOW_ACTION_END]`

**格式规则**:
1.  所有标签都使用 `[TAG_START]` 和 `[TAG_END]` 的配对格式。
2.  标签前后不要有任何多余字符或空格。
3.  确保开始和结束标签严格配对。

#### **3. 工作流程与决策**
1.  **识别意图**，并根据意图选择`ACTION`。
2.  **处理项目规划**: 如果意图是“项目规划”，则**必须**遵循第4节的规则。
3.  **禁止对话**: 当意图为“项目规划”或“文档生成”时，**禁止**使用 `[TEXT_START]` 进行回复。

#### **4. 需求处理规则 (核心中的核心)**

**你的唯一工作模式是维护一个项目的“最终状态”。每一次输出，都必须是基于历史所有对话的、一个全新的、完整的、最终的计划。**

1.  **强制性合并工作流**:
    *   **第一步：回顾历史** - 查看**上一轮**的完整规划是什么。
    *   **第二步：理解新增** - 分析用户**当前**的消息提出了什么新的需求点或修改。
    *   **第三步：生成全新** - 将新的需求点**无缝整合**进旧的规划中，生成一个**全新的、覆盖所有需求**的完整列表。你的输出必须像是第一次见到这个项目，然后一次性把所有事情都列出来。

2.  **输出内容准则**:
    *   **绝对完整性**: `ACTION` 标签内的内容，**永远是合并了所有历史需求后的最终完整清单**。它不是增量更新，不是补丁，而是完整的最终版本。
    *   **【严禁解释】**: 绝对禁止包含任何承上启下、解释性或对比性的文字。严禁出现“基于现有规划...”、“在...基础上新增...”或“最终形成一个...”等描述性语句。
    *   **【格式纯粹】**: 直接、清晰地将所有需求要点，一条一条列出来。

#### **5. 示例 (多轮对话)**

*   **用户第一轮**: "我要创建一个在线购物系统，需要有商品浏览和购物车。"
    *   **模型输出**: `[SHORT_PLAN_ACTION_START]创建一个在线购物系统，需求如下： 1. 商品浏览与搜索 2. 购物车管理[SHORT_PLAN_ACTION_END]`

*   **用户第二轮**: "很好，现在给我加上用户登录和优惠券功能。"
    *   **模型输出 (正确)**: `[SHORT_PLAN_ACTION_START]创建一个在线购物系统，需求如下： 1. 商品浏览与搜索 2. 购物车管理 3. 用户注册与登录 4. 优惠券系统[SHORT_PLAN_ACTION_END]`

*   **用户第三轮**: "再加一个订单管理。"
    *   **模型输出 (正确)**: `[SHORT_PLAN_ACTION_START]创建一个在线购物系统，需求如下： 1. 商品浏览与搜索 2. 购物车管理 3. 用户注册与登录 4. 优惠券系统 5. 订单管理[SHORT_PLAN_ACTION_END]`
    *   **模型输出 (灾难性错误)**: `[SHORT_PLAN_ACTION_START]为系统增加订单管理功能：1. 查看订单列表 2. 订单详情[SHORT_PLAN_ACTION_END]`  **(这个错误是因为它完全忘记了之前的购物系统、登录等所有需求，这是绝对要避免的)**"""

            # 用户对话上下文部分（纯净的用户数据，不包含系统指令）
            user_context = f"""
用户对话历史：
{context_str}

当前规划内容：
{current_plan if current_plan else "暂无规划内容"}

用户当前消息：{message}"""

            # 组合完整提示词
            prompt = f"""{system_prompt}

{user_context}"""


        else:
            # 系统提示词部分（包含所有系统指令，独立于用户对话历史）
            system_prompt = """You are the AI assistant for GTPlanner. Your core mission is to analyze user intent and output instructions according to a predefined format.

#### **1. Core Mission**
Analyze the user's intent within the conversational context and choose one of the following four types to respond with:
*   **Project Planning**: The user proposes a new project, new features, or optimization suggestions.
*   **Document Generation**: The user explicitly requests the generation of a design or technical document.
*   **Full Flow**: The user presents a complex project requirement, suitable for generating the plan and documentation in one go.
*   **Conversation**: General greetings, thanks, or standard questions.

#### **2. Output Format (Must be strictly followed)**
*   **Conversation**: `[TEXT_START]Your reply content here[TEXT_END]`
*   **Project Planning**: `[SHORT_PLAN_ACTION_START]The complete and final list of requirements[SHORT_PLAN_ACTION_END]`
*   **Document Generation**: `[LONG_DOC_ACTION_START][LONG_DOC_ACTION_END]` (No content between tags)
*   **Full Flow**: `[FULL_FLOW_ACTION_START]The complete and final list of requirements[FULL_FLOW_ACTION_END]`

**Formatting Rules**:
1.  All tags must use the paired `[TAG_START]` and `[TAG_END]` format.
2.  There must be no extra characters or spaces before or after a tag.
3.  Ensure that start and end tags are strictly paired.

#### **3. Workflow and Decision-Making**
1.  **Identify the intent** and select an `ACTION` accordingly.
2.  **Handle Project Planning**: If the intent is "Project Planning," you **must** follow the rules in Section 4.
3.  **Prohibit Conversation**: When the intent is "Project Planning" or "Document Generation," you are **forbidden** from using `[TEXT_START]` to reply.

#### **4. Requirement Processing Rules (The Core Mandate)**

**Your sole operational model is to maintain the "final state" of a project. Every output you generate must be a brand-new, complete, and final plan based on the entire conversation history.**

1.  **Mandatory Merge Workflow**:
    *   **Step 1: Review History** - Look at the complete plan from the **previous turn**.
    *   **Step 2: Understand Additions** - Analyze what new requirements or modifications the user's **current message** introduces.
    *   **Step 3: Generate Anew** - **Seamlessly integrate** the new points into the old plan to produce a **brand-new, all-encompassing** list of requirements. Your output must look as if you are seeing the project for the first time and listing everything in one go.

2.  **Output Content Guidelines**:
    *   **Absolute Completeness**: The content inside the `ACTION` tag must **always be the final, complete list that merges all historical requirements**. It is not an incremental update, not a patch, but the complete final version.
    *   **【STRICTLY FORBIDDEN: Explanations】**: Absolutely no transitional, explanatory, or comparative text. Do not use phrases like "Based on the existing plan...", "Adding to the previous scope...", or "The final plan is now...".
    *   **【PURE FORMAT】**: Directly and clearly list all requirement points, one by one.

#### **5. Example (Multi-Turn Dialogue)**

*   **User: Turn 1**: "I want to create an online shopping system. It needs product browsing and a shopping cart."
    *   **Model Output**: `[SHORT_PLAN_ACTION_START]Create an online shopping system with the following requirements: 1. Product browsing and search 2. Shopping cart management[SHORT_PLAN_ACTION_END]`

*   **User: Turn 2**: "Great, now add user login and a coupon feature."
    *   **Model Output (Correct)**: `[SHORT_PLAN_ACTION_START]Create an online shopping system with the following requirements: 1. Product browsing and search 2. Shopping cart management 3. User registration and login 4. Coupon system[SHORT_PLAN_ACTION_END]`

*   **User: Turn 3**: "Also add order management."
    *   **Model Output (Correct)**: `[SHORT_PLAN_ACTION_START]Create an online shopping system with the following requirements: 1. Product browsing and search 2. Shopping cart management 3. User registration and login 4. Coupon system 5. Order management[SHORT_PLAN_ACTION_END]`
    *   **Model Output (Catastrophic Error)**: `[SHORT_PLAN_ACTION_START]Add order management to the system: 1. View order list 2. Order details[SHORT_PLAN_ACTION_END]`  **(This is a catastrophic error because it completely forgot all previous requirements like the shopping system, login, etc. This must be avoided at all costs.)**"""

            # 用户对话上下文部分（纯净的用户数据，不包含系统指令）
            user_context = f"""
User conversation history:
{context_str}

Current plan content:
{current_plan if current_plan else "No current plan available"}

Current user message: {message}"""

            # 组合完整提示词
            prompt = f"""{system_prompt}

{user_context}"""

        # 调用LLM进行意图识别和响应生成
        yield stream_data("[STATUS_START]")
        yield stream_data("🤖 正在生成回复...")
        yield stream_data_block("[STATUS_END]")

        

        # 导入流式LLM调用
        from utils.call_llm import call_llm_stream_async

        # 流式输出LLM的响应并监听ACTION标签
        action_buffer = []
        in_action = False
        action_type = None
        content_buffer = ""
        pending_output = ""  # 缓冲待输出的内容

        async for chunk in call_llm_stream_async(prompt):
            if chunk:
                content_buffer += chunk
                pending_output += chunk

                # 处理缓冲区中的完整标签
                while True:
                    # 查找标签开始
                    start_pos = pending_output.find('[')
                    if start_pos == -1:
                        # 没有标签，输出所有内容
                        if pending_output and not in_action:
                            yield stream_data(pending_output)
                        elif pending_output and in_action:
                            action_buffer.append(pending_output)
                        pending_output = ""
                        break

                    # 输出标签前的内容
                    if start_pos > 0:
                        before_tag = pending_output[:start_pos]
                        if not in_action:
                            yield stream_data(before_tag)
                        else:
                            action_buffer.append(before_tag)

                    # 查找标签结束
                    end_pos = pending_output.find(']', start_pos)
                    if end_pos == -1:
                        # 标签不完整，保留从标签开始的所有内容
                        pending_output = pending_output[start_pos:]
                        break

                    # 提取完整标签
                    complete_tag = pending_output[start_pos:end_pos + 1]
                    remaining_content = pending_output[end_pos + 1:]

                    # 处理标签
                    if complete_tag == "[SHORT_PLAN_ACTION_START]":
                        in_action = True
                        action_buffer = []
                        action_type = "short_plan"
                        # ACTION标签不发送到前端
                    elif complete_tag == "[LONG_DOC_ACTION_START]":
                        in_action = True
                        action_buffer = []
                        action_type = "long_doc"
                        # ACTION标签不发送到前端
                    elif complete_tag == "[FULL_FLOW_ACTION_START]":
                        in_action = True
                        action_buffer = []
                        action_type = "full_flow"
                        # ACTION标签不发送到前端

                    elif complete_tag in ["[SHORT_PLAN_ACTION_END]", "[LONG_DOC_ACTION_END]", "[FULL_FLOW_ACTION_END]"] and in_action:
                        # 处理ACTION内容
                        action_content = ''.join(action_buffer).strip()
                        if action_content:
                            # 根据action_type构造action_content
                            full_action_content = f"{action_type}:{action_content}"
                            async for planning_chunk in handle_action(full_action_content, message, current_plan, language, conversation_history):
                                yield planning_chunk
                        in_action = False
                        action_buffer = []
                        action_type = None
                        # ACTION标签不发送到前端
                    else:
                        # 非ACTION标签，正常发送
                        if not in_action:
                            yield stream_data(complete_tag)
                        else:
                            action_buffer.append(complete_tag)

                    # 继续处理剩余内容
                    pending_output = remaining_content

        # 处理可能剩余的内容
        if pending_output:
            if not in_action:
                yield stream_data(pending_output)
            else:
                action_buffer.append(pending_output)

        yield stream_data_block("")  # 空行表示结束

    except Exception as e:
        # 记录详细错误信息用于调试
        import logging
        logging.error(f"Error in generate_stream_response: {str(e)}", exc_info=True)

        # 向用户返回通用错误信息，不暴露内部细节
        yield stream_data("[ERROR_START]")
        yield stream_data("❌ An internal error occurred while generating response. Please try again later.")
        yield stream_data_block("[ERROR_END]")


async def generate_direct_action_response(
    action: str,
    message: str,
    conversation_history: List[ChatMessage],
    session_id: Optional[str],
    language: str,
    context: Dict[str, Any]
):
    """
    根据明确的action直接生成响应，跳过AI意图识别
    """
   

    try:
        # 发送状态信息 - 根据语言本地化
        yield stream_data("[STATUS_START]")
        if language == "zh":
            yield stream_data("🔄 正在处理您的请求...")
        else:
            yield stream_data("🔄 Processing your request...")
        yield stream_data_block("[STATUS_END]")

        # 提取上下文信息
        current_plan = context.get("current_plan", "")

        if action == "generate_document":
            # 直接调用长文档生成
            if not current_plan:
                yield stream_data("[ERROR_START]")
                if language == "zh":
                    yield stream_data("❌ 未找到当前规划内容，无法生成文档。")
                else:
                    yield stream_data("❌ No current plan found. Cannot generate document.")
                yield stream_data_block("[ERROR_END]")
                return

            yield stream_data("[STATUS_START]")
            if language == "zh":
                yield stream_data("📄 正在生成详细设计文档...")
            else:
                yield stream_data("📄 Generating detailed design document...")
            yield stream_data_block("[STATUS_END]")

            # 调用长文档生成流式接口
            from api.v1.planning import long_planning_stream, LongPlanningRequest

            doc_request = LongPlanningRequest(
                requirement=message,
                previous_flow=current_plan,
                language=language
            )

            async for chunk in long_planning_stream(doc_request):
                yield chunk



        else:
            yield stream_data("[ERROR_START]")
            if language == "zh":
                yield stream_data(f"❌ 不支持的操作类型: {action}")
            else:
                yield stream_data(f"❌ Unsupported action type: {action}")
            yield stream_data_block("[ERROR_END]")

    except Exception as e:
        # 记录详细错误信息用于调试
        import logging
        logging.error(f"Error in generate_direct_action_response: {str(e)}", exc_info=True)

        # 向用户返回通用错误信息，不暴露内部细节
        yield stream_data("[ERROR_START]")
        if language == "zh":
            yield stream_data("❌ 处理操作时发生内部错误，请稍后重试。")
        else:
            yield stream_data("❌ An internal error occurred while processing the operation. Please try again later.")
        yield stream_data_block("[ERROR_END]")


@chat_router.post("/unified")
async def unified_conversation(body: ConversationRequest):
    """
    统一对话接口：集成意图识别、对话回复、规划生成和文档生成功能
    完全使用流式响应
    """
    message = body.message
    conversation_history = body.conversation_history or []
    session_id = body.session_id
    language = body.language
    action = body.action
    context = body.context or {}

    
    if not message:
        async def error_stream():
            yield stream_data("[ERROR_START]")
            yield stream_data("❌ Missing message in request body.")
            yield stream_data_block("[ERROR_END]")
        return StreamingResponse(error_stream(), media_type="text/plain")

    # 确定语言 - 优先使用前端传递的界面语言，确保界面语言和LLM输出语言的一致性
    language = determine_language(message, None, language)

    # 根据action字段直接调用相应功能，或使用AI意图识别
    if action:
        return StreamingResponse(
            generate_direct_action_response(action, message, conversation_history, session_id, language, context),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )
    else:
        # 返回流式响应（使用AI意图识别）
        return StreamingResponse(
            generate_stream_response(message, conversation_history, session_id, language, context),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )


