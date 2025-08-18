# 导入日志模块，用于记录程序运行时的信息

import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
# 导入系统模块，用于处理系统相关的操作，如退出程序
import sys
import threading
import time
# 导入UUID模块，用于生成唯一标识符
import uuid
# 从html模块导入escape函数，用于转义HTML特殊字符
from html import escape
# 从typing模块导入类型提示工具
from typing import Literal, Annotated, Sequence, Optional
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import HumanMessage, AIMessage
# 从typing_extensions导入TypedDict，用于定义类型化的字典
from typing_extensions import TypedDict
# 导入LangChain的提示模板类
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
# 导入LangChain的消息基类
from langchain_core.messages import BaseMessage
# 导入消息处理函数，用于追加消息
from langgraph.graph.message import add_messages
# 导入状态图和起始/结束节点的定义
from langgraph.graph import StateGraph, START, END
# 导入基础存储接口
from langgraph.store.base import BaseStore
# 导入可运行配置类
from langchain_core.runnables import RunnableConfig
# 导入Postgres存储类
from langgraph.store.postgres import PostgresStore
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
# 导入 psycopg2 的操作异常类，用于捕获数据库连接错误
from psycopg2 import OperationalError
# 导入PostgreSQL连接池类
from psycopg_pool import ConnectionPool
# 导入Pydantic的基类和字段定义工具
from pydantic import BaseModel, Field, conint
# 导入自定义的get_llm函数，用于获取LLM模型
from utils.model import get_llm
# 导入统一的 Config 类
from utils.setting import Config

# 配置日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.handlers = []  # 清空默认处理器

# 使用ConcurrentRotatingFileHandler处理日志文件
handler = ConcurrentRotatingFileHandler(
    Config.log_file,
    maxBytes=Config.MAX_BYTES,
    backupCount=Config.BACKUP_COUNT
)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
logger.addHandler(handler)

# 添加中文日志记录
logger.info("初始化日志系统完成，日志级别设置为DEBUG")


class MessagesState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_score: Annotated[Optional[str], "Relevance score of retrieved documents, 'yes' or 'no'"]
    agent_score: Annotated[Optional[str], "Relevance score of retrieved documents, 'yes' or 'no'"]
    relevance_score: Annotated[int, "Score between 0 and 100"]
    rewrite_count: Annotated[int, "Number of times query has been rewritten"]


class DocumentRelevanceScore:
    binary_score: conint(ge=0, le=100) = Field(description="Score between 0 and 100")


class UserInputScore:
    user_score = Field(description="Relevance score 'yes' or 'no'")


class ConnectionPoolError(Exception):
    pass


def get_latest_question(state: MessagesState) -> Optional[str]:
    try:
        if not state.get("messages") or not isinstance(state["messages"], (list, tuple)) or len(state["messages"]) == 0:
            logger.warning("状态中没有有效的消息列表")
            return None

        for message in reversed(state["messages"]):
            if message.__class__.__name__ == "HumanMessage" and hasattr(message, "content"):
                logger.debug(f"找到最新用户问题: {message.content}")
                return message.content

        logger.info("状态中未找到HumanMessage")
        return None
    except Exception as e:
        logger.error(f"获取最新问题时出错: {e}")
        return None


def filter_messages(message: list) -> list:
    logger.debug("开始过滤消息列表")
    filtered = [msg for msg in message if msg.__class__.__name__ in ["HumanMessage", "AIMessage"]]
    logger.debug(f"过滤后保留{len(filtered)}条消息")
    return filtered[-10:] if len(filtered) > 10 else filtered


def store_memory(question: BaseMessage, config: RunnableConfig, store: BaseStore) -> str:
    namespace = ("memories", config["configurable"]["user_id"])
    try:
        logger.debug("在存储中搜索相关记忆")
        memories = store.search(namespace, query=question.content)
        user_info = "\n".join([d.value['data'] for d in memories])

        if "记住" in question.content.lower():
            memory = escape(question.content)
            logger.info(f"存储新记忆: {memory}")
            store.put(namespace, str(uuid.uuid4()), {"data": memory})

        return user_info
    except Exception as e:
        logger.error(f"存储记忆时出错: {e}")
        return ""


def create_chain(llm_chat, template_file: str, structured_output=None):
    if not hasattr(create_chain, 'prompt_cache'):
        logger.debug("初始化提示模板缓存")
        create_chain.prompt_cache = {}
        create_chain.lock = threading.Lock()

    try:
        if template_file in create_chain.prompt_cache:
            logger.debug(f"使用缓存中的提示模板: {template_file}")
            prompt_template = create_chain.prompt_cache[template_file]
        else:
            with create_chain.lock:
                if template_file not in create_chain.prompt_cache:
                    logger.info(f"加载并缓存提示模板: {template_file}")
                    create_chain.prompt_cache[template_file] = PromptTemplate.from_file(template_file, encoding="utf-8")
                prompt_template = create_chain.prompt_cache[template_file]

        prompt = ChatPromptTemplate.from_messages([('human', prompt_template.template)])
        logger.debug("创建处理链完成")
        return prompt | (llm_chat.with_structured_output(structured_output) if structured_output else llm_chat)
    except FileNotFoundError:
        logger.error(f"未找到模板文件: {template_file}")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10),
       retry=retry_if_exception_type(OperationalError))
def test_connection(db_connection_pool: ConnectionPool) -> bool:
    logger.debug("测试数据库连接池")
    with db_connection_pool.getconn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result != (1,):
                logger.error("连接池测试查询失败")
                raise ConnectionPoolError("连接池测试查询失败，返回结果异常")
    logger.info("连接池测试成功")
    return True


def monitor_connection_pool(db_connection_pool: ConnectionPool, interval: int = 60):
    def _monitor():
        while not db_connection_pool.closed:
            try:
                stats = db_connection_pool.get_stats()
                active = stats.get("connections_in_use", 0)
                total = db_connection_pool.max_size
                logger.info(f"连接池状态: 使用中{active}/{total}")
                if active >= total * 0.8:
                    logger.warning(f"连接池接近容量上限: {active}/{total}")
            except Exception as e:
                logger.error(f"监控连接池失败: {e}")
            time.sleep(interval)

    logger.info("启动连接池监控线程")
    monitor_thread = threading.Thread(target=_monitor, daemon=True)
    monitor_thread.start()
    return monitor_thread


def generate_workflow(state: MessagesState, config: RunnableConfig, *, store: BaseStore, llm_chat) -> dict:
    logger.info("代理开始处理用户查询")
    try:
        question = state["messages"][-1]
        logger.debug(f"代理处理的问题: {question}")
        rewrite_count = state.get("rewrite_count", 0)

        user_info = store_memory(question, config, store)
        messages = filter_messages(state["messages"])

        agent_chain = create_chain(llm_chat, Config().PROMPT_TEMPLATE_TEXT_GENERATE)
        response = agent_chain.invoke({"question": question, "messages": messages, "userInfo": user_info})
        logger.debug("代理处理完成")
        return {"messages": [response],
                "rewrite_count": rewrite_count + 1}
    except Exception as e:
        logger.error(f"代理处理出错: {e}")
        return {"messages": [{"role": "system", "content": "处理请求时出错"}]}


def agent(state: MessagesState, llm_chat) -> dict:
    logger.info("代理开始处理用户查询")
    try:
        question = state["messages"][-1]
        logger.debug(f"代理处理的问题: {question}")

        agent_chain = create_chain(llm_chat, Config().PROMPT_TEMPLATE_TEXT_AGENT, UserInputScore)
        response = agent_chain.invoke({"question": question})
        score = response['user_score']
        if score == 'no':
            res = [AIMessage(content=response["res"])]
            logger.debug("代理处理完成")
            return {"messages": res, "agent_score": score}
        else:
            return {"agent_score": score}
    except Exception as e:
        logger.error(f"代理处理出错: {e}")
        return {"messages": [{"role": "system", "content": "处理请求时出错"}]}


def grade_documents(state: MessagesState, llm_chat) -> dict:
    logger.info("开始评估文档相关性")
    if not state.get("messages"):
        logger.error("状态中没有消息")
        return {
            "messages": [{"role": "system", "content": "状态为空，无法评分"}],
            "relevance_score": None
        }

    try:
        original_messages = state["messages"][:-1]
        question = get_latest_question(state)
        context = state["messages"][-1].content
        logger.debug(f"评估相关性 - 问题: {question}, 上下文: {context}")

        grade_chain = create_chain(llm_chat, Config.PROMPT_TEMPLATE_TXT_GRADE, DocumentRelevanceScore)
        scored_result = grade_chain.invoke({"question": question, "context": context})
        score = scored_result['binary_score']
        logger.info(f"文档相关性评分结果: {score}")

        return {
            "messages": original_messages,
            "relevance_score": int(score)
        }
    except (IndexError, KeyError) as e:
        logger.error(f"访问消息出错: {e}")
        return {
            "messages": [{"role": "system", "content": "无法评分文档"}],
            "relevance_score": None
        }
    except Exception as e:
        logger.error(f"评估文档时发生未知错误: {e}")
        return {
            "messages": state["messages"],
            "relevance_score": None
        }


def route_after_agent(state: MessagesState) -> Literal["generate_workflow", "__end__"]:
    if not isinstance(state, dict):
        logger.error("状态不是字典类型，默认路由到end")
        return "__end__"

    if "messages" not in state or not isinstance(state["messages"], (list, tuple)):
        logger.error("状态缺少有效的messages字段，默认路由到end")
        return "__end__"

    if not state["messages"]:
        logger.warning("消息列表为空，默认路由到end")
        return "__end__"

    relevance_score = state.get("agent_score")
    logger.info(f"基于意图分析评分路由: {relevance_score}")

    try:
        if not isinstance(relevance_score, str):
            logger.warning(f"无效的relevance_score类型: {type(relevance_score)}，默认路由到rewrite")
            return "__end__"

        if relevance_score.lower() == "yes":
            logger.info("需要生成结构图，转到generate_workflow")
            return "generate_workflow"

        logger.info("用户不需要生成结构图，转到end")
        return "__end__"

    except AttributeError:
        logger.error("relevance_score不是字符串或为None，默认路由到end")
        return "__end__"
    except Exception as e:
        logger.error(f"路由评分后发生未知错误: {e}，默认路由到end")
        return "__end__"


def route_after_grade(state: MessagesState) -> Literal["__end__", "generate_workflow"]:
    if not isinstance(state, dict):
        logger.error("状态不是字典类型，默认路由到generate_workflow")
        return "generate_workflow"

    if "messages" not in state or not isinstance(state["messages"], (list, tuple)):
        logger.error("状态缺少有效的messages字段，默认路由到generate_workflow")
        return "generate_workflow"

    if not state["messages"]:
        logger.warning("消息列表为空，默认路由到generate_workflow")
        return "generate_workflow"

    relevance_score = state.get("relevance_score")
    rewrite_count = state.get("rewrite_count", 0)
    logger.info(f"基于相关性评分路由: {relevance_score}, 重写次数: {rewrite_count - 1}")

    if rewrite_count > 3:
        logger.info("达到最大重写限制，转到user_input")
        return "__end__"

    try:
        if not isinstance(relevance_score, int):
            logger.warning(f"无效的relevance_score类型: {type(relevance_score)}，默认路由到generate_workflow")
            return "generate_workflow"

        if relevance_score < 75:
            logger.info("评分过低，转到generate_workflow")
            return "generate_workflow"

        logger.info("文档过低或评分失败，转到generate_workflow")
        return "__end__"

    except AttributeError:
        logger.error("relevance_score不是整数或为None，默认路由到generate_workflow")
        return "generate_workflow"
    except Exception as e:
        logger.error(f"路由评分后发生未知错误: {e}，默认路由到generate_workflow")
        return "generate_workflow"


def save_graph_visualization(graph: StateGraph, filename: str = "graph.png") -> None:
    try:
        with open(filename, "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
        logger.info(f"状态图可视化已保存为 {filename}")
    except IOError as e:
        logger.warning(f"保存状态图可视化失败: {e}")


def create_graph(db_connection_pool: ConnectionPool, llm_chat, llm_embedding) -> CompiledStateGraph:
    if db_connection_pool is None or db_connection_pool.closed:
        logger.error("数据库连接池未初始化或已关闭")
        raise ConnectionPoolError("数据库连接池未初始化或已关闭")

    try:
        active_connections = db_connection_pool.get_stats().get("connections_in_use", 0)
        max_connections = db_connection_pool.max_size
        if active_connections >= max_connections:
            logger.error(f"连接池已耗尽: {active_connections}/{max_connections}")
            raise ConnectionPoolError("连接池已耗尽，无可用连接")
        if not test_connection(db_connection_pool):
            raise ConnectionPoolError("连接池测试失败")
        logger.info("连接池状态: 测试连接成功")
    except OperationalError as e:
        logger.error(f"数据库操作错误: {e}")
        raise ConnectionPoolError(f"连接池测试失败，可能已关闭或超时: {str(e)}")
    except Exception as e:
        logger.error(f"验证连接池状态失败: {e}")
        raise ConnectionPoolError(f"无法验证连接池状态: {str(e)}")

    try:
        logger.info("初始化检查点保存器")
        checkpointer = MemorySaver()
    except Exception as e:
        logger.error(f"设置检查点保存器失败: {e}")
        raise ConnectionPoolError(f"检查点初始化失败: {str(e)}")

    try:
        logger.info("初始化Postgres存储")
        store = PostgresStore(db_connection_pool, index={"dims": 1536, "embed": llm_embedding})
        store.setup()
    except Exception as e:
        logger.error(f"设置PostgresStore失败: {e}")
        raise ConnectionPoolError(f"存储初始化失败: {str(e)}")

    logger.info("创建状态图实例")
    workflow = StateGraph(MessagesState)

    logger.debug("添加代理节点")
    workflow.add_node("generate_workflow",
                      lambda state, config: generate_workflow(state, config, store=store, llm_chat=llm_chat))

    logger.debug("添加文档评分节点")
    workflow.add_node("grade_documents", lambda state: grade_documents(state, llm_chat=llm_chat))

    logger.debug("添加意图分析节点")
    workflow.add_node("agent", lambda state: agent(state, llm_chat=llm_chat))

    logger.debug("添加从起始到意图分析的边")
    workflow.add_edge(START, end_key="agent")

    logger.debug("添加从意图分析到生成工作流的边")
    workflow.add_conditional_edges(source="agent", path=route_after_agent,
                                   path_map={"generate_workflow": "generate_workflow", END: END})

    logger.debug("添加从工作流到相关性评分的边")
    workflow.add_edge(start_key="generate_workflow", end_key="grade_documents")

    logger.debug("添加评分的条件边")
    workflow.add_conditional_edges(source="grade_documents", path=route_after_grade,
                                   path_map={"generate_workflow": "generate_workflow", END: END})

    logger.info("编译状态图")
    return workflow.compile(checkpointer=checkpointer, store=store)


def graph_response(graph: StateGraph, user_input: str, config: dict) -> None:
    try:
        logger.info("开始处理用户输入")
        events = graph.stream({"messages": [{"role": "user", "content": user_input}], "rewrite_count": 0}, config)

        for event in events:
            for value in event.values():
                if "messages" not in value or not isinstance(value["messages"], list):
                    logger.warning("响应中没有有效的消息")
                    continue

                last_message = value["messages"][-1]

                if hasattr(last_message, "content"):
                    content = str(last_message.content)

                    if hasattr(last_message, "type") and last_message.type == "ai":
                        logger.info(f"AI回复: {content}")
                        print(f"Assistant: {content}")
                    elif last_message.__class__.__name__ == "AIMessage":
                        logger.info(f"AI回复: {content}")
                        print(f"Assistant: {content}")
                    elif hasattr(last_message, "name") and last_message.name:
                        logger.info(f"[{last_message.name}]: {content}")
                        print(f"[{last_message.name}]: {content}")
                    else:
                        logger.info(f"默认回复: {content}")
                        print(f"Assistant: {content}")
                else:
                    logger.info(f"消息没有内容，消息类型: {type(last_message)}, 类: {last_message.__class__.__name__}")
                    if hasattr(last_message, "additional_kwargs"):
                        logger.debug(f"消息附加参数: {last_message.additional_kwargs}")

    except ValueError as ve:
        logger.error(f"处理响应时值错误: {ve}")
        print("Assistant: 处理响应时发生值错误")
    except TypeError as te:
        logger.error(f"处理响应时类型错误: {te}")
        print("Assistant: 处理响应时发生类型错误")
    except Exception as e:
        logger.error(f"处理响应时出错: {e}")
        logger.error(f"错误类型: {type(e)}")
        import traceback
        logger.error(f"堆栈跟踪: {traceback.format_exc()}")
        print("Assistant: 处理响应时发生未知错误")


def main():
    db_connection_pool = None
    try:
        logger.info("开始初始化聊天机器人")

        logger.debug("获取LLM模型")
        llm_chat, llm_embedding = get_llm(Config.LLM_TYPE)

        connection_kwargs = {"autocommit": True, "prepare_threshold": 0, "connect_timeout": 5}
        logger.info(f"初始化数据库连接池，最大连接数: 20")
        db_connection_pool = ConnectionPool(conninfo=Config.DB_URI, max_size=20, min_size=2, kwargs=connection_kwargs,
                                            timeout=10)

        try:
            logger.debug("打开数据库连接池")
            db_connection_pool.open()
            logger.info("数据库连接池初始化成功")
        except Exception as e:
            logger.error(f"打开连接池失败: {e}")
            raise ConnectionPoolError(f"无法打开数据库连接池: {str(e)}")

        logger.info("启动连接池监控")
        monitor_thread = monitor_connection_pool(db_connection_pool, interval=60)

        try:
            logger.info("创建状态图")
            graph = create_graph(db_connection_pool, llm_chat, llm_embedding)
        except ConnectionPoolError as e:
            logger.error(f"创建状态图失败: {e}")
            print(f"错误: {e}")
            sys.exit(1)

        logger.debug("保存状态图可视化")
        save_graph_visualization(graph)

        print("聊天机器人准备就绪！输入 'quit'、'exit' 或 'q' 结束对话。")
        config = {"configurable": {"thread_id": "1", "user_id": "1"}}

        while True:
            user_input = input("User: ").strip()
            if user_input.lower() in {"quit", "exit", "q"}:
                logger.info("用户请求退出")
                print("拜拜!")
                break
            if not user_input:
                logger.warning("用户输入为空")
                print("请输入聊天内容！")
                continue

            try:
                logger.info(f"处理用户输入: {user_input}")
                initial_state = {
                    "messages": [HumanMessage(content=user_input)],
                    "rewrite_count": 0
                }

                events = graph.stream(initial_state, config)

                for event in events:
                    for value in event.values():
                        if "messages" not in value or not isinstance(value["messages"], list):
                            continue

                        last_message = value["messages"][-1]

                        if hasattr(last_message, "content") and last_message.content:
                            content = str(last_message.content)

                            if last_message.__class__.__name__ == "AIMessage":
                                logger.info(f"AI回复: {content}")
                                print(f"Assistant: {content}")
                            elif last_message.__class__.__name__ == "HumanMessage":
                                pass
                            else:
                                logger.info(f"默认回复: {content}")
                                print(f"Assistant: {content}")

            except Exception as e:
                logger.error(f"处理消息时出错: {e}")
                print("Assistant: 处理消息时出错")

    except ConnectionPoolError as e:
        logger.error(f"连接池错误: {e}")
        print(f"错误: 数据库连接池问题 - {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"初始化错误: {e}")
        print(f"错误: 初始化失败 - {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("被用户中断")
        print("\n被用户打断。再见！")
    except Exception as e:
        logger.error(f"未知错误: {e}")
        print(f"错误: 发生未知错误 - {e}")
        sys.exit(1)
    finally:
        if db_connection_pool and not db_connection_pool.closed:
            logger.info("关闭数据库连接池")
            db_connection_pool.close()


if __name__ == "__main__":
    logger.info("启动主程序")
    main()
    logger.info("主程序结束")
