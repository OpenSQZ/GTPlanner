"""
GTPlanner主程序 - 演示BadCase系统和RAG系统的集成

展示完整的用户提问 -> RAG生成回答 -> 用户反馈 -> 记录BadCase的流程
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import dotenv_values

# 添加utils目录到Python路径
sys.path.append('utils')

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

# 打印环境变量检查
print("\n环境变量检查:")
print(f"DEEPSEEK_API_KEY: {os.getenv('DEEPSEEK_API_KEY')}")

from badcase_system import (
    BadCase,
    JSONStorageEngine,
    BadCaseRecorder,
    BadCaseAnalyzer
)

from rag_system import (
    Document,
    KnowledgeBase,
    SimpleKeywordRetriever,
    RAGEngine
)

# 尝试导入DeepSeek API
try:
    from deepseek_api import DeepSeekRAGEngine, deepseek_llm_api
    DEEPSEEK_AVAILABLE = True
    print("✓ DeepSeek API模块加载成功")
except ImportError as e:
    print(f"⚠️ DeepSeek API模块加载失败: {e}")
    DEEPSEEK_AVAILABLE = False


class GTPlannerSystem:
    """GTPlanner系统主类，集成BadCase和RAG功能"""
    
    def __init__(self):
        """初始化系统"""
        print("=== 初始化GTPlanner系统 ===\n")
        
        # 初始化BadCase系统
        print("1. 初始化BadCase系统...")
        self.badcase_storage = JSONStorageEngine("gtplanner_badcases.json")
        self.badcase_recorder = BadCaseRecorder(self.badcase_storage)
        self.badcase_analyzer = BadCaseAnalyzer(self.badcase_storage)
        print("   ✓ BadCase系统初始化完成")
        
        # 初始化RAG系统
        print("2. 初始化RAG系统...")
        self.knowledge_base = KnowledgeBase("gtplanner_knowledge_base.json")
        self.retriever = SimpleKeywordRetriever(self.knowledge_base, top_k=3)
        
        # 使用DeepSeek API
        if DEEPSEEK_AVAILABLE and os.getenv('DEEPSEEK_API_KEY'):
            try:
                self.rag_engine = DeepSeekRAGEngine(self.knowledge_base, self.retriever)
                print("   ✓ DeepSeek RAG系统初始化完成")
            except Exception as e:
                print(f"   ⚠️ DeepSeek API初始化失败，使用备用RAG引擎: {e}")
                self.rag_engine = RAGEngine(self.knowledge_base, self.retriever)
                print("   ✓ 备用RAG系统初始化完成")
        else:
            print("   ⚠️ DeepSeek API不可用，使用备用RAG引擎")
            self.rag_engine = RAGEngine(self.knowledge_base, self.retriever)
            print("   ✓ 备用RAG系统初始化完成")
        
        # 初始化知识库
        self._initialize_knowledge_base()
        
        print("✓ 系统初始化完成！\n")
    
    def _initialize_knowledge_base(self):
        """初始化知识库内容"""
        print("3. 初始化知识库...")
        
        # 检查知识库是否已有内容
        if self.knowledge_base.get_document_count() == 0:
            # 添加示例文档
            documents = [
                {
                    "title": "Python编程基础",
                    "content": "Python是一种高级编程语言，由Guido van Rossum于1991年创建。Python具有简洁的语法和强大的功能，广泛应用于Web开发、数据科学、人工智能等领域。Python支持面向对象编程、函数式编程等多种编程范式。",
                    "metadata": {"category": "programming", "language": "Python"}
                },
                {
                    "title": "机器学习入门",
                    "content": "机器学习是人工智能的一个重要分支，它使计算机能够在没有明确编程的情况下学习和改进。机器学习算法通过分析数据来识别模式，并基于这些模式做出预测或决策。常见的机器学习类型包括监督学习、无监督学习和强化学习。",
                    "metadata": {"category": "AI", "topic": "machine_learning"}
                },
                {
                    "title": "数据结构与算法",
                    "content": "数据结构是计算机科学的基础，它定义了数据的组织、存储和访问方式。常见的数据结构包括数组、链表、栈、队列、树、图等。算法是解决问题的步骤和方法，好的算法能够高效地处理数据。",
                    "metadata": {"category": "computer_science", "topic": "data_structures"}
                },
                {
                    "title": "深度学习基础",
                    "content": "深度学习是机器学习的一个子集，使用多层神经网络来模拟人脑的学习过程。深度学习在图像识别、自然语言处理、语音识别等领域取得了突破性进展。常见的深度学习框架包括TensorFlow、PyTorch等。",
                    "metadata": {"category": "AI", "topic": "deep_learning"}
                },
                {
                    "title": "Web开发技术",
                    "content": "Web开发涉及前端和后端技术。前端技术包括HTML、CSS、JavaScript等，用于构建用户界面。后端技术包括服务器端编程、数据库设计、API开发等。现代Web开发还涉及响应式设计、单页应用等概念。",
                    "metadata": {"category": "web_development", "topic": "full_stack"}
                }
            ]
            
            for doc in documents:
                self.rag_engine.add_document(
                    title=doc["title"],
                    content=doc["content"],
                    metadata=doc["metadata"]
                )
            
            print(f"   ✓ 添加了 {len(documents)} 个示例文档")
        else:
            print(f"   ✓ 知识库已有 {self.knowledge_base.get_document_count()} 个文档")
    
    def process_user_query(self, question: str, user_id: str = "default_user") -> Dict[str, Any]:
        """
        处理用户查询的完整流程
        """
        print(f"\n=== 处理用户查询: {question} ===")

        # ====== 意图识别分流 ======
        intent_result = self._detect_intent(question)
        if intent_result:
            print(f"   [意图识别] 识别到查询意图: {intent_result.get('detail_type', intent_result.get('stat_type', 'unknown'))}")
            return intent_result
        
        # ====== RAG查询流程 ======
        print("1. RAG生成回答...")
        rag_result = self.rag_engine.query(question)
        
        answer = rag_result["answer"]
        relevant_docs = rag_result["relevant_documents"]
        doc_count = rag_result["document_count"]
        
        print(f"   回答: {answer[:100]}...")
        print(f"   相关文档数: {doc_count}")

        # ====== 自动反馈判定 ======
        print("\n2. 自动反馈判定...")
        feedback = self._auto_detect_feedback(question, answer, relevant_docs)
        print(f"   系统判定: {feedback}")

        # 记录BadCase（如果反馈为负面）
        if feedback in ["错误", "不准确", "不完整", "无关"]:
            print("3. 记录BadCase...")
            success = self.badcase_recorder.record_badcase(
                input_prompt=question,
                output_result=answer,
                feedback_label=feedback,
                user_id=user_id
            )
            if success:
                print("   ✓ BadCase记录成功")
            else:
                print("   ✗ BadCase记录失败")
        else:
            print("3. 无需记录BadCase（正面反馈）")
        
        return {
            "question": question,
            "answer": answer,
            "feedback": feedback,
            "relevant_docs": relevant_docs,
            "doc_count": doc_count,
            "recorded_badcase": feedback in ["错误", "不准确", "不完整", "无关"]
        }

    def _detect_intent(self, question: str) -> Optional[Dict[str, Any]]:
        """
        检测用户意图
        
        Args:
            question: 用户问题
            
        Returns:
            Optional[Dict[str, Any]]: 如果是统计分析意图则返回结果，否则返回None
        """
        import re
        import unicodedata
        
        # 移除白名单限制，允许所有查询进入意图识别
        # 新增白名单机制：当问题包含特定统计关键词时才触发意图识别
        # stat_keywords = ["统计", "分析", "数量", "分布", "比例", "占比", "查询", "查看", "badcase"]
        # if not any(keyword in question for keyword in stat_keywords):
        #     return None

        # 归一化函数
        def normalize(s):
            if not s: return ''
            s = s.strip().replace('"', '').replace('"', '').replace('"', '').replace("'", '')
            s = unicodedata.normalize('NFKC', s)
            return s
        
        # 统计分析意图识别模式
        stat_patterns = [
            r"分析[“\"']?(.+?)[\"\"']?的数量",
            r"统计[“\"']?(.+?)[\"\"']?的数量", 
            r"(.+?)的数量",
            r"有多少(.+?)的badcase",
            r"(.+?)类型的badcase数量",
            r"统计(.+?)错误案例",
            r"分析(.+?)问题数量",
            r"查看(.+?)的统计",
            r"(.+?)的分布情况",
            r"badcase中(.+?)有多少",
            r"请统计[“\"']?(.+?)[\"\"']?类型的问题数量",
            r"统计[“\"']?(.+?)[\"\"']?类型的问题数量",
            r"分析[“\"']?(.+?)[\"\"']?类型的问题数量",
            r"请分析[“\"']?(.+?)[\"\"']?类型的问题数量",
            r"(.+?)类型的问题数量",
            r"(.+?)类型的问题有多少",
            r"有多少(.+?)类型的问题",
            r"统计(.+?)类型的问题",
            r"分析(.+?)类型的问题"
        ]
        
        # 加强明细查询模式匹配
        detail_patterns = [
            r"列出[‘\"']?(.+?)[\"'']?类型的问题",
            r"显示[‘\"']?(.+?)[\"'']?类型的问题",
            r"查看[‘\"']?(.+?)[\"'']?类型的问题",
            r"请列出[‘\"']?(.+?)[\"'']?类型的问题",
            r"请显示[‘\"']?(.+?)[\"'']?类型的问题",
            r"请查看[‘\"']?(.+?)[\"'']?类型的问题",
            r"(.+?)类型的问题(列表|明细|详情)",
            r"请?(输出|导出)[‘\"']?(.+?)[\"'']?类型的问题",
            r"(.+?)类型的问题(有哪些|都有什么)",
            r"关于[‘\"']?(.+?)[\"'']?类型的问题",
            r"列出[‘\"']?(.+?)[\"'']?问题",
            r"显示[‘\"']?(.+?)[\"'']?问题",
            r"查看[‘\"']?(.+?)[\"'']?问题"
        ]
        
        # 检查是否为统计分析请求
        for pattern in stat_patterns:
            match = re.search(pattern, question)
            if match:
                label = match.group(1).strip()
                if label:
                    # 清理标签 - 移除引号和前缀
                    label = label.strip()
                    # 移除引号
                    label = label.strip("'\"")
                    # 移除后缀
                    for suffix in ["类型的问题数量", "类型的问题", "类型的问题有多少", "类型的", "类型"]:
                        if label.endswith(suffix):
                            label = label[:-len(suffix)].strip()
                    # 移除前缀
                    for prefix in ["请分析", "分析", "统计", "查看", "有多少", "的分布情况", "的统计"]:
                        if label.startswith(prefix):
                            label = label[len(prefix):].strip()
                    
                    # 归一化标签
                    norm_label = normalize(label)
                    
                    # 获取badcase标签分布
                    label_distribution = self.badcase_analyzer.get_label_distribution()
                    count = 0
                    matched_labels = []
                    
                    # 计算匹配的标签数量
                    for k, v in label_distribution.items():
                        norm_k = normalize(k)
                        if (norm_label == norm_k or 
                            norm_label in norm_k or 
                            norm_k in norm_label or
                            label.lower() in k.lower() or
                            k.lower() in label.lower()):
                            count += v
                            matched_labels.append(k)
                    
                    print(f"   [统计分析] '{label}' 类型的badcase数量为: {count}")
                    if matched_labels:
                        print(f"   匹配的标签: {', '.join(matched_labels)}")
                    
                    return {
                        "stat_label": label,
                        "stat_count": count,
                        "stat_type": "badcase_label_count",
                        "question": question,
                        "matched_labels": matched_labels
                    }
        
        # 检查明细查询请求（加强带引号的匹配）
        for pattern in detail_patterns:
            match = re.search(pattern, question)
            if match:
                # 提取标签逻辑需要处理带引号的情况
                label = match.group(1).strip("'\"\"\"''")  # 去除所有类型的引号
                print(f"   [调试] 提取的原始标签: '{label}'")
                
                # 获取指定标签的BadCase列表
                return self._handle_detail_query(label)
        
        return None

    def _handle_detail_query(self, label: str) -> Dict[str, Any]:
        """处理明细查询请求"""
        print(f"   [明细查询] 正在获取'{label}'类型的BadCase...")
        
        all_badcases = self.badcase_storage.get_all_badcases()
        matched = []
        
        # 更灵活的标签匹配
        for bc in all_badcases:
            if (label in bc.feedback_label or 
                bc.feedback_label in label or
                label.lower() in bc.feedback_label.lower() or
                bc.feedback_label.lower() in label.lower()):
                matched.append(bc)
        
        print(f"   找到 {len(matched)} 个匹配的BadCase")
        return {
            "detail_label": label,
            "detail_count": len(matched),
            "detail_type": "badcase_label_detail",
            "badcases": [bc.__dict__ for bc in matched]
        }

    def _auto_detect_feedback(self, question: str, answer: str, relevant_docs: List[Dict]) -> str:
        """
        自动判断反馈类型
        
        判断逻辑：
        1. 无相关文档 -> 无关
        2. 回答出错 -> 错误
        3. 回答过短 -> 不完整
        4. 回答质量好 -> 满意
        5. 默认 -> 满意
        """
        print(f"   [调试] 问题: '{question}'")
        print(f"   [调试] 回答长度: {len(answer)} 字符")
        print(f"   [调试] 问题长度: {len(question)} 字符")
        
        # 规则1：无相关文档
        if not relevant_docs:
            print("   [调试] 无相关文档，返回无关")
            return "无关"
            
        # 规则2：检查回答是否出错
        error_indicators = [
            "生成回答时出错",
            "无法生成回答",
            "API调用失败",
            "网络错误",
            "超时",
            "无法理解",
            "无法识别"
        ]
        if any(indicator in answer for indicator in error_indicators):
            print("   [调试] 回答出错，返回错误")
            return "错误"
            
        # 规则3：回答长度检查（更宽松的阈值）
        question_length = len(question.strip())
        answer_length = len(answer.strip())
        
        # 如果问题很短（<10字符），使用更宽松的阈值
        if question_length < 10:
            min_answer_length = max(20, question_length * 2)  # 至少20字符或问题长度2倍
        else:
            min_answer_length = question_length * 1.5  # 问题长度1.5倍
            
        print(f"   [调试] 最小回答长度要求: {min_answer_length}")
        if answer_length < min_answer_length:
            print("   [调试] 回答长度不足，返回不完整")
            return "不完整"
        
        # 规则4：检查回答质量指标（正面判断）
        quality_indicators = [
            "根据提供的上下文信息",
            "基于上下文",
            "根据",
            "包括",
            "主要有",
            "常见的有",
            "主要技术",
            "核心技术",
            "创建",
            "设计",
            "开发",
            "诞生",
            "起源",
            "由来",
            "历史",
            "特点",
            "优势",
            "应用",
            "领域",
            "功能",
            "支持",
            "提供",
            "实现"
        ]
        
        # 如果回答包含质量指标，判定为满意
        if any(indicator in answer for indicator in quality_indicators):
            print("   [调试] 包含质量指标，返回满意")
            return "满意"
        
        # 规则5：检查回答结构（正面判断）
        structure_indicators = [
            "**",  # 粗体标记
            "1.", "2.", "3.", "4.", "5.",  # 列表
            "•", "·",  # 项目符号
            "：", ":",  # 冒号
            "（", "）", "(", ")",  # 括号
            "，", ",",  # 逗号
            "。", ".",  # 句号
        ]
        
        if any(indicator in answer for indicator in structure_indicators):
            print("   [调试] 包含结构化内容，返回满意")
            return "满意"
        
        # 规则6：检查回答详细程度（正面判断）
        if answer_length > question_length * 4:  # 回答长度是问题的4倍以上
            print("   [调试] 回答非常详细，返回满意")
            return "满意"
        
        # 规则7：检查是否回答了问题的核心（通用判断）
        # 如果回答长度合理且没有明显的错误指示，倾向于判定为满意
        if answer_length >= min_answer_length and len(answer) > 20:
            print("   [调试] 回答长度合理且无错误，返回满意")
            return "满意"
        
        print("   [调试] 默认返回满意")
        return "满意"  # 默认改为满意
    
    def show_badcase_statistics(self):
        """显示BadCase统计信息"""
        print("\n=== BadCase统计信息 ===")
        
        # 获取统计信息
        total_count = self.badcase_analyzer.get_total_count()
        label_distribution = self.badcase_analyzer.get_label_distribution()
        user_stats = self.badcase_analyzer.get_user_statistics()
        common_labels = self.badcase_analyzer.get_most_common_labels(top_n=5)
        
        print(f"总BadCase数量: {total_count}")
        print(f"标签分布: {label_distribution}")
        print(f"用户统计: {user_stats}")
        print(f"最常见标签: {common_labels}")
        
        if total_count > 0:
            print("\n详细统计:")
            for label, count in label_distribution.items():
                percentage = (count / total_count) * 100
                print(f"  {label}: {count} ({percentage:.1f}%)")
    
    def search_badcases(self, query: str):
        """搜索BadCase"""
        print(f"\n=== 搜索BadCase: {query} ===")
        
        # 按用户搜索
        user_badcases = self.badcase_storage.get_badcases_by_user("default_user")
        print(f"用户'default_user'的BadCase数量: {len(user_badcases)}")
        
        # 按标签搜索
        label_badcases = self.badcase_storage.get_badcases_by_label("错误")
        print(f"标签'错误'的BadCase数量: {len(label_badcases)}")
        
        # 显示最近的BadCase
        all_badcases = self.badcase_storage.get_all_badcases()
        if all_badcases:
            print("\n最近的BadCase:")
            recent_badcases = sorted(all_badcases, key=lambda x: x.timestamp, reverse=True)[:3]
            for i, badcase in enumerate(recent_badcases, 1):
                print(f"  {i}. [{badcase.feedback_label}] {badcase.input_prompt[:50]}...")
    
    def show_rag_statistics(self):
        """显示RAG系统统计信息"""
        print("\n=== RAG系统统计信息 ===")
        
        stats = self.rag_engine.get_knowledge_base_stats()
        print(f"知识库文档数: {stats['total_documents']}")
        print(f"总关键词数: {stats['total_keywords']}")
        print(f"平均每文档关键词数: {stats['average_keywords_per_doc']:.2f}")
        
        # 显示知识库文档
        all_docs = self.knowledge_base.get_all_documents()
        print(f"\n知识库文档:")
        for i, doc in enumerate(all_docs, 1):
            print(f"  {i}. {doc.title}")
            print(f"     关键词: {', '.join(doc.get_keywords()[:5])}...")
    
    def run_demo(self):
        """运行完整演示"""
        print("=== GTPlanner系统演示 ===\n")
        
        # 模拟用户查询
        demo_questions = [
            "什么是Python？",
            "机器学习有什么应用？",
            "如何学习数据结构？",
            "深度学习框架有哪些？",
            "Web开发需要什么技术？",
            "如何做菜？",  # 这个应该没有相关文档
            "Python编程有什么特点？",
            "人工智能的发展历史"
        ]
        
        print("开始模拟用户查询流程...")
        for i, question in enumerate(demo_questions, 1):
            print(f"\n--- 查询 {i}/{len(demo_questions)} ---")
            result = self.process_user_query(question, f"user_{i}")
            
            # 显示结果摘要
            print(f"结果摘要: 相关文档{result['doc_count']}个, 反馈'{result['feedback']}', " + 
                  ("已记录BadCase" if result['recorded_badcase'] else "未记录BadCase"))
        
        # 显示统计信息
        self.show_badcase_statistics()
        self.show_rag_statistics()
        
        # 搜索BadCase
        self.search_badcases("Python")
        
        print("\n=== 演示完成 ===")


def run_tests():
    """运行测试用例"""
    print("=== 运行测试用例 ===\n")
    
    # 创建临时系统进行测试
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_badcase_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_kb_file = f.name
    
    try:
        # 初始化测试系统
        badcase_storage = JSONStorageEngine(temp_badcase_file)
        badcase_recorder = BadCaseRecorder(badcase_storage)
        badcase_analyzer = BadCaseAnalyzer(badcase_storage)
        
        knowledge_base = KnowledgeBase(temp_kb_file)
        retriever = SimpleKeywordRetriever(knowledge_base, top_k=2)
        rag_engine = RAGEngine(knowledge_base, retriever)
        
        # 测试1: 添加文档
        print("测试1: 添加文档")
        doc_id = rag_engine.add_document("测试文档", "这是一个测试文档的内容")
        assert doc_id is not None
        print("✓ 文档添加成功")
        
        # 测试2: RAG查询
        print("测试2: RAG查询")
        result = rag_engine.query("测试")
        assert "question" in result
        assert "answer" in result
        print("✓ RAG查询成功")
        
        # 测试3: 记录BadCase
        print("测试3: 记录BadCase")
        success = badcase_recorder.record_badcase(
            "测试问题", "测试回答", "错误", "test_user"
        )
        assert success is True
        print("✓ BadCase记录成功")
        
        # 测试4: 统计功能
        print("测试4: 统计功能")
        total_count = badcase_analyzer.get_total_count()
        assert total_count == 1
        print("✓ 统计功能正常")
        
        # 测试5: 检索功能
        print("测试5: 检索功能")
        docs = retriever.retrieve("测试")
        assert len(docs) > 0
        print("✓ 检索功能正常")
        
        print("\n✓ 所有测试通过！")
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_badcase_file):
            os.unlink(temp_badcase_file)
        if os.path.exists(temp_kb_file):
            os.unlink(temp_kb_file)


def main():
    """主函数"""
    print("GTPlanner - 集成BadCase和RAG系统")
    print("=" * 50)
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_tests()
        return
    
    # 运行主演示
    try:
        system = GTPlannerSystem()
        system.run_demo()
        
        # 交互式查询（可选）
        print("\n" + "=" * 50)
        print("开始交互式查询（输入'quit'退出）:")
        
        while True:
            try:
                question = input("\n请输入您的问题: ").strip()
                if question.lower() in ['quit', 'exit', '退出']:
                    break
                if not question:
                    continue
                
                result = system.process_user_query(question)
                
                if "stat_type" in result:
                    print(f"\n[统计结果] '{result['stat_label']}' 类型的badcase数量为: {result['stat_count']}")
                elif "detail_type" in result:
                    print(f"\n[明细结果] '{result['detail_label']}' 类型的badcase明细:")
                    print(f"共找到 {result['detail_count']} 个匹配的BadCase:")
                    for i, badcase in enumerate(result['badcases'], 1):  # 显示所有BadCase
                        print(f"  {i}. [{badcase['feedback_label']}] {badcase['input_prompt'][:50]}...")
                        print(f"     用户: {badcase['user_id']}, 时间: {badcase['timestamp'][:19]}")
                    if result['detail_count'] == 0:
                        print("  没有找到匹配的BadCase")
                else:
                    print(f"\n回答: {result['answer']}")
                    print(f"反馈: {result['feedback']}")
                
            except KeyboardInterrupt:
                print("\n\n程序被用户中断")
                break
            except Exception as e:
                print(f"处理查询时出错: {e}")
        
        print("\n感谢使用GTPlanner系统！")
        
    except Exception as e:
        print(f"系统初始化失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
