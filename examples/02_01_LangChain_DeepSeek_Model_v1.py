# 加载环境变量
import os
from pathlib import Path
from dotenv import dotenv_values

# 获取当前目录
current_dir = Path(__file__).parent
env_path = current_dir / '.env'

print(f"检查 .env 文件路径: {env_path}")
print(f".env 文件是否存在: {env_path.exists()}")

# 直接读取 .env 文件
config = dotenv_values(env_path)
print("\n.env 文件内容:")
for key, value in config.items():
    print(f"{key}: {value}")

# 设置环境变量
for key, value in config.items():
    os.environ[key] = value

# 创建必要的目录
base_model_path = os.getenv('BASE_MODEL_PATH', 'D:/ai_models')
os.makedirs(os.path.join(base_model_path, 'huggingface', 'hub'), exist_ok=True)
os.makedirs(os.path.join(base_model_path, 'cache'), exist_ok=True)
os.makedirs(os.path.join(base_model_path, 'llamaindex'), exist_ok=True)

# 打印环境变量检查
print("\n环境变量检查:")
print(f"DEEPSEEK_API_KEY: {os.getenv('DEEPSEEK_API_KEY')}")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from langchain_core.documents import Document

# 设置请求重试
session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

from langchain_community.document_loaders import WebBaseLoader

try:
    loader = WebBaseLoader(
        web_paths=("https://zh.wikipedia.org/wiki/%E9%BB%91%E7%A5%9E%E8%AF%9D%EF%BC%9A%E6%82%9F%E7%A9%BA",),
        requests_kwargs={'verify': False},  # 禁用 SSL 验证
        session=session
    )
    docs = loader.load()
except Exception as e:
    print(f"加载文档时出错: {str(e)}")
    # 使用备用文本
    docs = [Document(page_content="黑神话：悟空是一款由游戏科学开发的动作角色扮演游戏。游戏场景包括：\n1. 花果山\n2. 水帘洞\n3. 天庭\n4. 地府\n5. 龙宫")]

# 2. 文档分块
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_splits = text_splitter.split_documents(docs)

# 3. 设置嵌入模型
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-small-zh-v1.5",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# 4. 创建向量存储
from langchain_core.vectorstores import InMemoryVectorStore

vector_store = InMemoryVectorStore(embeddings)
vector_store.add_documents(all_splits)

# 5. 构建用户查询
question = "黑悟空有哪些游戏场景？"

# 6. 在向量存储中搜索相关文档，并准备上下文内容
retrieved_docs = vector_store.similarity_search(question, k=3)
docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)

# 7. 构建提示模板
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template("""
                基于以下上下文，回答问题。如果上下文中没有相关信息，
                请说"我无法从提供的上下文中找到相关信息"。
                上下文: {context}
                问题: {question}
                回答:"""
                                          )

# 8. 使用大语言模型生成答案
from langchain_deepseek import ChatDeepSeek

# 直接从环境变量获取 API key
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
if not deepseek_api_key:
    raise ValueError("DEEPSEEK_API_KEY 未设置，请在 .env 文件中设置")

llm = ChatDeepSeek(
    model="deepseek-reasoner",  # DeepSeek API 支持的模型名称
    temperature=0.7,        # 控制输出的随机性
    max_tokens=2048,        # 最大输出长度
    api_key=deepseek_api_key  # 直接使用读取到的 API key
)
answer = llm.invoke(prompt.format(question=question, context=docs_content))
print(answer)


