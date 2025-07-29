"""
RAG系统使用示例 - 集成DeepSeek API
"""

import sys
import os
from datetime import datetime
from pathlib import Path
from dotenv import dotenv_values

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils'))

# 加载环境变量
current_dir = Path(__file__).parent
env_path = current_dir / '.env'

print(f"检查 .env 文件路径: {env_path}")
print(f".env 文件是否存在: {env_path.exists()}")

# 直接读取 .env 文件
if env_path.exists():
    config = dotenv_values(env_path)
    print("\n.env 文件内容:")
    for key, value in config.items():
        print(f"{key}: {value}")
    
    # 设置环境变量
    for key, value in config.items():
        if value is not None:  # 只设置非空值
            os.environ[key] = value
else:
    print("警告: .env 文件不存在，将使用环境变量中的API密钥")

# 创建必要的目录
base_model_path = os.getenv('BASE_MODEL_PATH', 'D:/ai_models')
os.makedirs(os.path.join(base_model_path, 'huggingface', 'hub'), exist_ok=True)
os.makedirs(os.path.join(base_model_path, 'cache'), exist_ok=True)
os.makedirs(os.path.join(base_model_path, 'llamaindex'), exist_ok=True)

# 打印环境变量检查
print("\n环境变量检查:")
print(f"DEEPSEEK_API_KEY: {os.getenv('DEEPSEEK_API_KEY')}")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")

from rag_system import (
    Document,
    KnowledgeBase,
    SimpleKeywordRetriever,
    RAGEngine
)

# 设置请求重试
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)


def deepseek_llm_api(prompt: str, context: str = "") -> str:
    """
    使用DeepSeek API生成回答
    
    Args:
        prompt: 用户问题
        context: 上下文信息
        
    Returns:
        str: 生成的回答
    """
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
    if not deepseek_api_key:
        print("⚠️ DEEPSEEK_API_KEY 未设置，将使用备用回答")
        return f"这是对'{prompt}'的回答。由于没有相关上下文，我只能提供一般性信息。"
    
    try:
        # 构建提示
        if context:
            full_prompt = f"""基于以下上下文，回答问题。如果上下文中没有相关信息，
请说"我无法从提供的上下文中找到相关信息"。

上下文: {context}
问题: {prompt}
回答:"""
        else:
            full_prompt = f"问题: {prompt}\n回答:"
        
        # 调用DeepSeek API
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {deepseek_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": full_prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        response = session.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # 提取回答内容
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "API返回格式异常"
            
    except Exception as e:
        print(f"DeepSeek API调用失败: {e}")
        return f"API调用失败：{str(e)}"


def main():
    """主函数 - 演示RAG系统的使用"""
    
    print("=== RAG系统使用示例（集成DeepSeek API）===\n")
    
    # 1. 初始化RAG系统
    print("1. 初始化RAG系统...")
    knowledge_base = KnowledgeBase("example_knowledge_base.json")
    retriever = SimpleKeywordRetriever(knowledge_base, top_k=3)
    
    # 使用DeepSeek API的RAG引擎
    if os.getenv('DEEPSEEK_API_KEY'):
        print("   使用DeepSeek API...")
        rag_engine = RAGEngine(knowledge_base, retriever, llm_function=deepseek_llm_api)
    else:
        print("   使用备用RAG引擎...")
        rag_engine = RAGEngine(knowledge_base, retriever)
    
    # 2. 添加知识库文档
    print("2. 添加知识库文档...")
    
    # 添加Python相关文档
    doc1_id = rag_engine.add_document(
        title="Python编程基础",
        content="Python是一种高级编程语言，由Guido van Rossum于1991年创建。Python具有简洁的语法和强大的功能，广泛应用于Web开发、数据科学、人工智能等领域。Python支持面向对象编程、函数式编程等多种编程范式。",
        metadata={"category": "programming", "language": "Python"}
    )
    print(f"   添加文档1: {doc1_id}")
    
    # 添加机器学习文档
    doc2_id = rag_engine.add_document(
        title="机器学习入门",
        content="机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习和改进。机器学习算法通过分析数据来识别模式，并基于这些模式做出预测或决策。常见的机器学习类型包括监督学习、无监督学习和强化学习。",
        metadata={"category": "AI", "topic": "machine_learning"}
    )
    print(f"   添加文档2: {doc2_id}")
    
    # 添加数据结构文档
    doc3_id = rag_engine.add_document(
        title="数据结构与算法",
        content="数据结构是计算机科学的基础，它定义了数据的组织、存储和访问方式。常见的数据结构包括数组、链表、栈、队列、树、图等。算法是解决问题的步骤和方法，好的算法能够高效地处理数据。",
        metadata={"category": "computer_science", "topic": "data_structures"}
    )
    print(f"   添加文档3: {doc3_id}")
    
    # 添加深度学习文档
    doc4_id = rag_engine.add_document(
        title="深度学习基础",
        content="深度学习是机器学习的一个子集，使用多层神经网络来模拟人脑的学习过程。深度学习在图像识别、自然语言处理、语音识别等领域取得了突破性进展。常见的深度学习框架包括TensorFlow、PyTorch等。",
        metadata={"category": "AI", "topic": "deep_learning"}
    )
    print(f"   添加文档4: {doc4_id}")
    
    # 添加游戏相关文档（测试新内容）
    doc5_id = rag_engine.add_document(
        title="黑神话：悟空游戏介绍",
        content="黑神话：悟空是一款由游戏科学开发的动作角色扮演游戏。游戏场景包括：花果山、水帘洞、天庭、地府、龙宫等。游戏以中国古典小说《西游记》为背景，讲述了孙悟空的故事。",
        metadata={"category": "gaming", "topic": "action_rpg"}
    )
    print(f"   添加文档5: {doc5_id}")
    
    # 3. 查看知识库统计信息
    print("\n3. 知识库统计信息...")
    stats = rag_engine.get_knowledge_base_stats()
    print(f"   总文档数: {stats['total_documents']}")
    print(f"   总关键词数: {stats['total_keywords']}")
    print(f"   平均每文档关键词数: {stats['average_keywords_per_doc']:.2f}")
    
    # 4. 进行查询测试
    print("\n4. 查询测试（使用DeepSeek API）...")
    
    # 测试Python相关查询
    print("\n   查询1: 什么是Python？")
    result1 = rag_engine.query("什么是Python？")
    print(f"   回答: {result1['answer']}")
    print(f"   相关文档数: {result1['document_count']}")
    
    # 测试机器学习相关查询
    print("\n   查询2: 机器学习是什么？")
    result2 = rag_engine.query("机器学习是什么？")
    print(f"   回答: {result2['answer']}")
    print(f"   相关文档数: {result2['document_count']}")
    
    # 测试数据结构相关查询
    print("\n   查询3: 什么是数据结构？")
    result3 = rag_engine.query("什么是数据结构？")
    print(f"   回答: {result3['answer']}")
    print(f"   相关文档数: {result3['document_count']}")
    
    # 测试深度学习相关查询
    print("\n   查询4: 深度学习有什么应用？")
    result4 = rag_engine.query("深度学习有什么应用？")
    print(f"   回答: {result4['answer']}")
    print(f"   相关文档数: {result4['document_count']}")
    
    # 测试游戏相关查询
    print("\n   查询5: 黑悟空有哪些游戏场景？")
    result5 = rag_engine.query("黑悟空有哪些游戏场景？")
    print(f"   回答: {result5['answer']}")
    print(f"   相关文档数: {result5['document_count']}")
    
    # 测试无关查询
    print("\n   查询6: 如何做菜？")
    result6 = rag_engine.query("如何做菜？")
    print(f"   回答: {result6['answer']}")
    print(f"   相关文档数: {result6['document_count']}")
    
    # 5. 测试检索器功能
    print("\n5. 测试检索器功能...")
    
    # 测试关键词检索
    print("   检索'Python'相关文档:")
    python_docs = retriever.retrieve("Python")
    for i, doc in enumerate(python_docs, 1):
        print(f"     {i}. {doc.title}")
    
    print("   检索'机器学习'相关文档:")
    ml_docs = retriever.retrieve("机器学习")
    for i, doc in enumerate(ml_docs, 1):
        print(f"     {i}. {doc.title}")
    
    print("   检索'游戏'相关文档:")
    game_docs = retriever.retrieve("游戏")
    for i, doc in enumerate(game_docs, 1):
        print(f"     {i}. {doc.title}")
    
    # 6. 测试知识库搜索功能
    print("\n6. 测试知识库搜索功能...")
    
    search_results = knowledge_base.search_documents("编程")
    print(f"   搜索'编程'的结果数: {len(search_results)}")
    for doc in search_results:
        print(f"     - {doc.title}")
    
    # 7. 测试文档管理功能
    print("\n7. 测试文档管理功能...")
    
    # 获取特定文档
    doc = knowledge_base.get_document(doc1_id)
    if doc:
        print(f"   获取文档: {doc.title}")
        print(f"   关键词: {doc.get_keywords()[:5]}...")  # 显示前5个关键词
    
    # 获取所有文档
    all_docs = knowledge_base.get_all_documents()
    print(f"   知识库中的文档:")
    for i, doc in enumerate(all_docs, 1):
        print(f"     {i}. {doc.title} (ID: {doc.id})")
    
    # 8. 测试DeepSeek API直接调用
    print("\n8. 测试DeepSeek API直接调用...")
    
    # 测试带上下文的API调用
    context = "Python是一种编程语言，语法简洁易学。"
    answer1 = deepseek_llm_api("什么是Python？", context)
    print(f"   带上下文的回答: {answer1}")
    
    # 测试不带上下文的API调用
    answer2 = deepseek_llm_api("什么是Python？")
    print(f"   不带上下文的回答: {answer2}")
    
    # 9. 显示详细查询结果
    print("\n9. 详细查询结果示例...")
    
    detailed_result = rag_engine.query("Python编程有什么特点？")
    print(f"   问题: {detailed_result['question']}")
    print(f"   回答: {detailed_result['answer']}")
    print(f"   相关文档数: {detailed_result['document_count']}")
    
    if detailed_result['relevant_documents']:
        print("   相关文档:")
        for i, doc_dict in enumerate(detailed_result['relevant_documents'], 1):
            print(f"     {i}. {doc_dict['title']}")
            print(f"        内容: {doc_dict['content'][:50]}...")
    
    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    main() 