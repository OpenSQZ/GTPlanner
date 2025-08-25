"""
BadCase记录系统使用示例
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils'))

from badcase_system import (
    BadCase,
    JSONStorageEngine,
    BadCaseRecorder,
    BadCaseAnalyzer
)


def main():
    """主函数 - 演示BadCase记录系统的使用"""
    
    print("=== BadCase记录系统使用示例 ===\n")
    
    # 1. 初始化组件
    print("1. 初始化组件...")
    storage_engine = JSONStorageEngine("example_badcases.json")
    recorder = BadCaseRecorder(storage_engine)
    analyzer = BadCaseAnalyzer(storage_engine)
    
    # 2. 记录一些BadCase
    print("2. 记录BadCase...")
    
    # 记录第一个BadCase
    success1 = recorder.record_badcase(
        input_prompt="请帮我写一个Python函数来计算斐波那契数列",
        output_result="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
        feedback_label="性能问题",
        user_id="user001"
    )
    print(f"   记录BadCase 1: {'成功' if success1 else '失败'}")
    
    # 记录第二个BadCase
    success2 = recorder.record_badcase(
        input_prompt="如何优化这个递归函数？",
        output_result="可以使用动态规划来优化，时间复杂度从O(2^n)降低到O(n)",
        feedback_label="代码质量",
        user_id="user001"
    )
    print(f"   记录BadCase 2: {'成功' if success2 else '失败'}")
    
    # 记录第三个BadCase
    success3 = recorder.record_badcase(
        input_prompt="解释一下什么是装饰器",
        output_result="装饰器是一种设计模式，用于在不修改原函数的情况下添加新功能",
        feedback_label="概念解释",
        user_id="user002"
    )
    print(f"   记录BadCase 3: {'成功' if success3 else '失败'}")
    
    # 记录第四个BadCase
    success4 = recorder.record_badcase(
        input_prompt="Python中的列表和元组有什么区别？",
        output_result="列表是可变的，元组是不可变的。列表使用方括号[]，元组使用圆括号()",
        feedback_label="概念解释",
        user_id="user003"
    )
    print(f"   记录BadCase 4: {'成功' if success4 else '失败'}")
    
    # 3. 分析统计信息
    print("\n3. 分析统计信息...")
    
    # 获取总数量
    total_count = analyzer.get_total_count()
    print(f"   总BadCase数量: {total_count}")
    
    # 获取标签分布
    label_distribution = analyzer.get_label_distribution()
    print(f"   标签分布: {label_distribution}")
    
    # 获取用户统计
    user_statistics = analyzer.get_user_statistics()
    print(f"   用户统计: {user_statistics}")
    
    # 获取最常见标签
    common_labels = analyzer.get_most_common_labels(top_n=3)
    print(f"   最常见标签 (前3): {common_labels}")
    
    # 4. 查询特定数据
    print("\n4. 查询特定数据...")
    
    # 查询特定用户的BadCase
    user001_badcases = storage_engine.get_badcases_by_user("user001")
    print(f"   用户user001的BadCase数量: {len(user001_badcases)}")
    
    # 查询特定标签的BadCase
    concept_badcases = storage_engine.get_badcases_by_label("概念解释")
    print(f"   标签'概念解释'的BadCase数量: {len(concept_badcases)}")
    
    # 5. 日期范围查询
    print("\n5. 日期范围查询...")
    
    # 获取今天的BadCase
    today = datetime.now().strftime("%Y-%m-%dT00:00:00")
    tomorrow = datetime.now().strftime("%Y-%m-%dT23:59:59")
    
    today_badcases = analyzer.get_badcases_by_date_range(today, tomorrow)
    print(f"   今天的BadCase数量: {len(today_badcases)}")
    
    # 6. 直接创建BadCase对象
    print("\n6. 直接创建BadCase对象...")
    
    custom_badcase = BadCase(
        input_prompt="这是一个自定义的BadCase",
        output_result="这是对应的输出结果",
        feedback_label="自定义标签",
        user_id="user004",
        timestamp=datetime.now().isoformat()
    )
    
    success5 = recorder.record_badcase_object(custom_badcase)
    print(f"   记录自定义BadCase: {'成功' if success5 else '失败'}")
    
    # 7. 最终统计
    print("\n7. 最终统计...")
    final_count = analyzer.get_total_count()
    print(f"   最终BadCase总数: {final_count}")
    
    # 显示所有BadCase的详细信息
    print("\n8. 所有BadCase详情:")
    all_badcases = storage_engine.get_all_badcases()
    for i, badcase in enumerate(all_badcases, 1):
        print(f"   BadCase {i}:")
        print(f"     用户: {badcase.user_id}")
        print(f"     标签: {badcase.feedback_label}")
        print(f"     输入: {badcase.input_prompt[:50]}...")
        print(f"     输出: {badcase.output_result[:50]}...")
        print(f"     时间: {badcase.timestamp}")
        print()
    
    print("=== 示例完成 ===")


if __name__ == "__main__":
    main() 