#!/usr/bin/env python3
"""
测试新的反馈选择功能
"""

import sys
import os
sys.path.append('utils')

from main import GTPlannerSystem

def test_new_feedback():
    """测试新的反馈选择功能"""
    print("=== 测试新的反馈选择功能 ===")
    
    # 创建系统实例
    system = GTPlannerSystem()
    
    # 测试一个简单的问题
    test_question = "Python是什么？"
    test_answer = "基于提供的上下文信息：Python是一种高级编程语言。"
    
    print(f"问题: {test_question}")
    print(f"回答: {test_answer}")
    
    # 测试反馈选择
    print("\n开始测试反馈选择...")
    feedback = system._get_user_feedback(test_question, test_answer, "test_user")
    
    print(f"\n最终反馈: {feedback}")

if __name__ == "__main__":
    test_new_feedback() 