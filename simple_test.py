#!/usr/bin/env python3
"""
简单测试明细查询功能
"""

import sys
sys.path.append('utils')

from main import GTPlannerSystem

def test_detail_query():
    """测试明细查询功能"""
    print("=== 测试明细查询功能 ===")
    
    # 创建系统实例
    system = GTPlannerSystem()
    
    # 测试用例
    test_queries = [
        "列出'不准确'类型的问题",
        "显示'不完整'类型的问题", 
        "查看'无关'类型的问题",
        "请列出'满意'类型的问题"
    ]
    
    for query in test_queries:
        print(f"\n测试查询: {query}")
        try:
            result = system.process_user_query(query)
            
            if result and "detail_type" in result:
                print(f"✓ 成功识别为明细查询")
                print(f"  标签: {result.get('detail_label', 'N/A')}")
                print(f"  数量: {result.get('detail_count', 0)}")
                print(f"  类型: {result.get('detail_type', 'N/A')}")
            else:
                print("✗ 未识别为明细查询")
                print(f"  返回结果: {result}")
                
        except Exception as e:
            print(f"✗ 测试异常: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_detail_query() 