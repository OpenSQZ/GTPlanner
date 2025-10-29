#!/usr/bin/env python3
"""
测试意图分析器
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# 临时将分析器代码复制到这里测试
class IntentAnalyzer:
    def __init__(self):
        self.tech_keywords = ["AI", "人工智能", "机器学习"]
        self.business_keywords = ["SaaS", "电商", "商业"]
    
    def analyze_intent(self, user_input: str) -> str:
        input_lower = user_input.lower()
        tech_score = sum(1 for keyword in self.tech_keywords if keyword.lower() in input_lower)
        business_score = sum(1 for keyword in self.business_keywords if keyword.lower() in input_lower)
        
        if tech_score > business_score and tech_score > 0:
            return "technical"
        elif business_score > tech_score and business_score > 0:
            return "business"
        else:
            return "general"

# 测试用例
def test_analyzer():
    analyzer = IntentAnalyzer()
    
    test_cases = [
        ("我想做个AI图像识别系统", "technical"),
        ("开发一个SaaS电商平台", "business"), 
        ("你好，请帮我规划", "general"),
        ("需要机器学习算法", "technical"),
        ("做个商业营销工具", "business")
    ]
    
    print("🧪 测试意图分析器:")
    for input_text, expected in test_cases:
        result = analyzer.analyze_intent(input_text)
        status = "✅" if result == expected else "❌"
        print(f"  {status} 输入: '{input_text}' -> 分析: {result} (期望: {expected})")

if __name__ == "__main__":
    test_analyzer()