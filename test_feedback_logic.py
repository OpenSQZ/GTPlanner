"""
测试自动反馈判定逻辑
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('utils')

from main import GTPlannerSystem


def test_feedback_logic():
    """测试自动反馈判定逻辑"""
    print("=== 测试自动反馈判定逻辑 ===\n")
    
    # 创建测试系统
    system = GTPlannerSystem()
    
    # 测试用例
    test_cases = [
        {
            "question": "python的由来",
            "answer": "Python是由荷兰程序员Guido van Rossum（吉多·范罗苏姆）于1991年创建的。它的设计初衷是提供一种语法简洁、易读性强且功能强大的高级编程语言。Python的名字并非源自蟒蛇，而是来自Guido喜爱的英国喜剧团体Monty Python（蒙提·派森），体现了语言轻松幽默的风格。Python的诞生填补了当时对可读性高、易于维护的脚本语言的需求，并逐渐发展成为支持多种编程范式（如面向对象、函数式编程）的通用语言，广泛应用于Web开发、数据科学、人工智能等领域。",
            "expected": "满意",
            "description": "详细回答Python的由来"
        },
        {
            "question": "java的由来",
            "answer": "Java是由Sun Microsystems公司（现为Oracle公司）的James Gosling等人于1995年开发的。Java的设计目标是创建一种可以在任何平台上运行的编程语言，即'一次编写，到处运行'。Java的名字来源于印度尼西亚的爪哇岛，因为开发团队喜欢喝爪哇咖啡。Java最初被称为Oak，后来改名为Java。",
            "expected": "满意",
            "description": "详细回答Java的由来"
        },
        {
            "question": "深度学习框架有哪些？",
            "answer": "根据上下文信息，常见的深度学习框架包括 **TensorFlow** 和 **PyTorch**。",
            "expected": "满意",
            "description": "回答包含框架信息"
        },
        {
            "question": "如何做菜？",
            "answer": "这是对'如何做菜？'的回答。由于没有相关上下文，我只能提供一般性信息。",
            "expected": "无关",
            "description": "无相关文档的情况"
        },
        {
            "question": "什么是Python？",
            "answer": "Python是一种编程语言。",
            "expected": "不完整",
            "description": "回答过短"
        },
        {
            "question": "机器学习算法",
            "answer": "机器学习算法包括监督学习、无监督学习和强化学习等类型。",
            "expected": "满意",
            "description": "包含算法信息"
        },
        {
            "question": "Web开发技术",
            "answer": "Web开发涉及前端和后端技术。前端技术包括HTML、CSS、JavaScript等，用于构建用户界面。后端技术包括服务器端编程、数据库设计、API开发等。",
            "expected": "满意",
            "description": "详细的技术介绍"
        },
        {
            "question": "测试问题",
            "answer": "生成回答时出错：API调用失败",
            "expected": "错误",
            "description": "回答出错的情况"
        }
    ]
    
    # 运行测试
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试 {i}/{total}: {test_case['description']}")
        print(f"问题: {test_case['question']}")
        print(f"回答: {test_case['answer'][:100]}...")
        
        # 模拟相关文档（除了"如何做菜"）
        relevant_docs = []
        if "做菜" not in test_case['question']:
            relevant_docs = [{"title": "测试文档", "content": "测试内容"}]
        
        # 调用自动反馈判定
        result = system._auto_detect_feedback(
            test_case['question'], 
            test_case['answer'], 
            relevant_docs
        )
        
        # 检查结果
        expected = test_case['expected']
        if result == expected:
            print(f"✓ 通过: 期望 '{expected}', 实际 '{result}'")
            passed += 1
        else:
            print(f"✗ 失败: 期望 '{expected}', 实际 '{result}'")
        
        print("-" * 50)
    
    # 输出测试结果
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败，需要进一步优化")
    
    return passed == total


def test_specific_case():
    """测试特定案例：python的由来"""
    print("\n=== 测试特定案例：python的由来 ===")
    
    system = GTPlannerSystem()
    
    question = "python的由来"
    answer = "Python是由荷兰程序员Guido van Rossum（吉多·范罗苏姆）于1991年创建的。它的设计初衷是提供一种语法简洁、易读性强且功能强大的高级编程语言。Python的名字并非源自蟒蛇，而是来自Guido喜爱的英国喜剧团体Monty Python（蒙提·派森），体现了语言轻松幽默的风格。Python的诞生填补了当时对可读性高、易于维护的脚本语言的需求，并逐渐发展成为支持多种编程范式（如面向对象、函数式编程）的通用语言，广泛应用于Web开发、数据科学、人工智能等领域。"
    relevant_docs = [{"title": "Python文档", "content": "Python相关内容"}]
    
    print(f"问题: {question}")
    print(f"回答长度: {len(answer)} 字符")
    print(f"问题长度: {len(question)} 字符")
    
    result = system._auto_detect_feedback(question, answer, relevant_docs)
    
    print(f"判定结果: {result}")
    
    if result == "满意":
        print("✓ 修复成功！")
    else:
        print("✗ 仍需进一步优化")


if __name__ == "__main__":
    # 运行测试
    test_feedback_logic()
    test_specific_case() 