#!/usr/bin/env python3
"""
测试显示所有BadCase的功能
"""

import sys
sys.path.append('utils')

from main import GTPlannerSystem

def test_full_display():
    """测试显示所有BadCase的功能"""
    print("=== 测试显示所有BadCase功能 ===")
    
    # 创建系统实例
    system = GTPlannerSystem()
    
    # 测试查询
    test_query = "列出'无关'类型的问题"
    print(f"测试查询: {test_query}")
    
    try:
        result = system.process_user_query(test_query)
        
        if result and "detail_type" in result:
            print(f"\n[明细结果] '{result['detail_label']}' 类型的badcase明细:")
            print(f"共找到 {result['detail_count']} 个匹配的BadCase:")
            
            if result['detail_count'] > 0:
                for i, badcase in enumerate(result['badcases'], 1):
                    print(f"  {i}. [{badcase['feedback_label']}] {badcase['input_prompt'][:50]}...")
                    print(f"     用户: {badcase['user_id']}, 时间: {badcase['timestamp'][:19]}")
            else:
                print("  没有找到匹配的BadCase")
                
            print(f"\n总共显示了 {len(result['badcases'])} 个BadCase")
        else:
            print("✗ 未识别为明细查询")
            
    except Exception as e:
        print(f"✗ 测试异常: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_full_display() 