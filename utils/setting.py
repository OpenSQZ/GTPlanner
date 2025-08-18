import os


class Config:
    """统一配置类"""
    current_script_path = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_script_path)
    # prompt文件路径
    PROMPT_TEMPLATE_TEXT_AGENT = os.path.join(base_dir, "prompts", "prompt_template_agent.txt")
    PROMPT_TEMPLATE_TEXT_GENERATE = os.path.join(base_dir, "prompts", "prompt_template_generate.txt")
    PROMPT_TEMPLATE_TXT_GRADE = os.path.join(base_dir, "prompts", "prompt_template_grade.txt")
    PROMPT_TEMPLATE_TXT_USER_GRADE = os.path.join(base_dir, "prompts", "prompt_template_user_grade.txt")

    # 工具调用最大线程数
    MAX_WORKERS = 5
    # 是否设置DEBUG级别的日志
    DEBUG_MODE = True

    # chroma数据库配置
    CHROMA_DIRECTORY = os.path.join(base_dir, "data/chromaDB")
    CHROMA_COLLECTION = "demo001"

    # 日志持久化存储
    log_file = os.path.join(base_dir, "data/log", "app.log")
    MAX_BYTES = 5 * 1024 * 1024
    BACKUP_COUNT = 3

    # 数据库配置
    DB_URI = os.getenv("DB_URI", "postgresql://test:123456@localhost:5432/postgres?sslmode=disable")

    # openai:调用gpt模型, qwen:调用阿里通义千问大模型, oneapi:调用oneapi方案支持的模型, ollama:调用本地开源大模型
    LLM_TYPE = "qwen"

    # API服务地址和端口
    HOST = "0.0.0.0"
    PORT = 8000
