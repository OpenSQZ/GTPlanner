#!/usr/bin/env python3
"""
测试反馈选择机制
"""

import sys
import os
sys.path.append('utils')

from main import GTPlannerSystem

def test_feedback_choice():
    """测试反馈选择机制"""
    print("=== 测试反馈选择机制 ===")
    
    # 创建系统实例
    system = GTPlannerSystem()
    
    # 测试问题
    test_question = "Python是什么？"
    
    print(f"测试问题: {test_question}")
    
    # 模拟RAG回答
    test_answer = "基于提供的上下文信息：Python是一种高级编程语言，由Guido van Rossum于1991年创建。Python具有简洁的语法和强大的功能，广泛应用于Web开发、数据科学、人工智能等领域。"
    
    print(f"RAG回答: {test_answer}")
    
    # 测试反馈选择
    print("\n开始测试反馈选择...")
    feedback = system._get_user_feedback(test_question, test_answer, "test_user")
    
    print(f"\n最终反馈: {feedback}")

if __name__ == "__main__":
    test_feedback_choice() 