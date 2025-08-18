import os
import logging
from typing import Tuple

from utils.embedding_setting import DashScopeEmbeddings
from langchain_community.chat_models import ChatTongyi
from langchain_openai import ChatOpenAI

# 设置日志模板
logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(levelname)s : %(message)s')
logger = logging.getLogger(__name__)

# 配置模型字典
MODEL_CONFIGS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "api_key": os.getenv('DEEPSEEK_API_KEY'),
        "chat_model": "deepseek-chat",
        "embedding_model": "text-embedding-3-small"
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "chat_model": "qwen-max",
        "embedding_model": "text-embedding-v1"
    },
    "qwen_dmt": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "chat_model": "qwen-vl-max",
        "embedding_model": "text-embedding-v1"
    },
    "oneapi": {
        "base_url": "http://139.224.72.218:3000/v1",
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "chat_model": "qwen-max",
        "embedding_model": "text-embedding-v1"
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "chat_model": "qwen2.5:32b",
        "embedding_model": "bge-m3:latest"
    },
}

# 默认配置
DEFAULT_LLM_TYPE = "qwen"
DEFAULT_TEMPERATURE = 0.5


class LLMInitializationError(Exception):
    """自定义异常类用于LLM初始化错误"""
    pass


def initialize_llm(llm_type: str = DEFAULT_LLM_TYPE) -> tuple[ChatTongyi | ChatOpenAI, DashScopeEmbeddings]:
    """
    初始化LLM实例

    Args:
        llm_type (str): LLM类型，可选值为 'deepseek', 'oneapi', 'qwen', 'ollama'

    Returns:
        ChatOpenAI: 初始化后的LLM实例

    Raises:
        LLMInitializationError: 当LLM初始化失败时抛出
    """
    try:
        # 检查llm_type是否有效
        if llm_type not in MODEL_CONFIGS:
            raise ValueError(f"不支持的LLM类型: {llm_type}. 可用的类型: {list(MODEL_CONFIGS.keys())}")

        config = MODEL_CONFIGS[llm_type]

        if llm_type == "ollama":
            os.environ["OPENAI_API_KEY"] = "NA"
        if llm_type == "qwen_dmt":
            llm_chat = ChatTongyi(model=config["chat_model"], api_key=os.getenv("DASHSCOPE_API_KEY"))
        else:
            # 创建LLM实例
            llm_chat = ChatOpenAI(base_url=config["base_url"],
                                  api_key=config["api_key"],
                                  model=config["chat_model"],
                                  temperature=DEFAULT_TEMPERATURE,
                                  timeout=30,
                                  max_retries=2)

        llm_embeddings = DashScopeEmbeddings(base_url=config["base_url"],
                                             api_key=config["api_key"],
                                             model=config["embedding_model"])

        logger.info(f'成功初始化模型：{llm_type}')
        return llm_chat, llm_embeddings
    except ValueError as ve:
        logger.error(f"LLM配置错误: {str(ve)}")
        raise LLMInitializationError(f"LLM配置错误: {str(ve)}")
    except Exception as e:
        logger.error(f'模型初始化失败：{str(e)}')
        raise LLMInitializationError(f'模型初始化失败：{str(e)}')


def get_llm(llm_type: str = DEFAULT_LLM_TYPE):
    try:
        return initialize_llm(llm_type=llm_type)
    except LLMInitializationError as e:
        logger.warning(f"使用默认配置重试: {str(e)}")
        if llm_type != DEFAULT_LLM_TYPE:
            return initialize_llm(DEFAULT_LLM_TYPE)
        raise


# 示例使用
if __name__ == "__main__":
    # 测试不同类型的LLM初始化
    llm_openai = get_llm("qwen")[1]
    # a = llm_openai.invoke('你好')
    # print(a)
    texts = ['nihao', '123']
    a = llm_openai.embed_documents(texts)
    print(a)
