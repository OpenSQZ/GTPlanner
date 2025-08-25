#!/usr/bin/env python3
"""
测试明细查询功能
验证系统是否能正确识别和返回指定类型的BadCase明细
"""

import sys
import os
import tempfile
import json
from datetime import datetime

# 添加utils目录到Python路径
sys.path.append('utils')

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


class DetailQueryTester:
    """明细查询功能测试类"""
    
    def __init__(self):
        """初始化测试环境"""
        print("=== 初始化测试环境 ===")
        
        # 创建临时文件
        self.temp_badcase_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_kb_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        
        # 初始化系统组件
        self.badcase_storage = JSONStorageEngine(self.temp_badcase_file.name)
        self.badcase_recorder = BadCaseRecorder(self.badcase_storage)
        self.badcase_analyzer = BadCaseAnalyzer(self.badcase_storage)
        
        self.knowledge_base = KnowledgeBase(self.temp_kb_file.name)
        self.retriever = SimpleKeywordRetriever(self.knowledge_base, top_k=3)
        self.rag_engine = RAGEngine(self.knowledge_base, self.retriever)
        
        # 添加测试数据
        self._setup_test_data()
        
        print("✓ 测试环境初始化完成\n")
    
    def _setup_test_data(self):
        """设置测试数据"""
        print("设置测试数据...")
        
        # 添加一些测试BadCase
        test_badcases = [
            {
                "input_prompt": "什么是Python？",
                "output_result": "Python是一种编程语言",
                "feedback_label": "不准确",
                "user_id": "test_user_1",
                "timestamp": datetime.now().isoformat()
            },
            {
                "input_prompt": "机器学习有什么应用？",
                "output_result": "机器学习在图像识别中有应用",
                "feedback_label": "不完整",
                "user_id": "test_user_2",
                "timestamp": datetime.now().isoformat()
            },
            {
                "input_prompt": "如何学习数据结构？",
                "output_result": "学习数据结构需要掌握基础概念",
                "feedback_label": "不准确",
                "user_id": "test_user_1",
                "timestamp": datetime.now().isoformat()
            },
            {
                "input_prompt": "深度学习框架有哪些？",
                "output_result": "TensorFlow和PyTorch是主要框架",
                "feedback_label": "满意",
                "user_id": "test_user_3",
                "timestamp": datetime.now().isoformat()
            },
            {
                "input_prompt": "Web开发需要什么技术？",
                "output_result": "需要HTML、CSS、JavaScript",
                "feedback_label": "不完整",
                "user_id": "test_user_2",
                "timestamp": datetime.now().isoformat()
            },
            {
                "input_prompt": "如何做菜？",
                "output_result": "做菜需要准备食材和调料",
                "feedback_label": "无关",
                "user_id": "test_user_1",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # 记录测试BadCase
        for badcase_data in test_badcases:
            self.badcase_recorder.record_badcase(
                input_prompt=badcase_data["input_prompt"],
                output_result=badcase_data["output_result"],
                feedback_label=badcase_data["feedback_label"],
                user_id=badcase_data["user_id"]
            )
        
        print(f"✓ 添加了 {len(test_badcases)} 个测试BadCase")
    
    def test_detail_query_recognition(self):
        """测试明细查询识别功能"""
        print("\n=== 测试明细查询识别功能 ===")
        
        # 导入主系统的意图识别功能
        from main import GTPlannerSystem
        
        # 创建测试系统实例
        test_system = GTPlannerSystem()
        
        # 测试用例
        test_cases = [
            {
                "query": "列出'不准确'类型的问题",
                "expected_label": "不准确",
                "expected_count": 2
            },
            {
                "query": "显示'不完整'类型的问题",
                "expected_label": "不完整",
                "expected_count": 2
            },
            {
                "query": "查看'无关'类型的问题",
                "expected_label": "无关",
                "expected_count": 1
            },
            {
                "query": "请列出'满意'类型的问题",
                "expected_label": "满意",
                "expected_count": 1
            },
            {
                "query": "列出'错误'类型的问题",
                "expected_label": "错误",
                "expected_count": 0
            }
        ]
        
        success_count = 0
        total_count = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n测试 {i}/{total_count}: {test_case['query']}")
            
            try:
                # 执行意图识别
                result = test_system._detect_intent(test_case['query'])
                
                if result and "detail_type" in result:
                    actual_label = result.get("detail_label", "")
                    actual_count = result.get("detail_count", 0)
                    
                    print(f"   识别结果: 标签='{actual_label}', 数量={actual_count}")
                    
                    # 验证结果
                    if (actual_label == test_case["expected_label"] and 
                        actual_count == test_case["expected_count"]):
                        print("   ✓ 测试通过")
                        success_count += 1
                    else:
                        print(f"   ✗ 测试失败: 期望标签='{test_case['expected_label']}', 期望数量={test_case['expected_count']}")
                else:
                    print("   ✗ 测试失败: 未识别为明细查询")
                    
            except Exception as e:
                print(f"   ✗ 测试异常: {e}")
        
        print(f"\n测试结果: {success_count}/{total_count} 通过")
        return success_count == total_count
    
    def test_detail_query_processing(self):
        """测试明细查询处理功能"""
        print("\n=== 测试明细查询处理功能 ===")
        
        # 导入主系统的处理功能
        from main import GTPlannerSystem
        
        # 创建测试系统实例
        test_system = GTPlannerSystem()
        
        # 测试用例
        test_cases = [
            {
                "query": "列出'不准确'类型的问题",
                "expected_type": "badcase_label_detail"
            },
            {
                "query": "显示'不完整'类型的问题",
                "expected_type": "badcase_label_detail"
            },
            {
                "query": "查看'无关'类型的问题",
                "expected_type": "badcase_label_detail"
            }
        ]
        
        success_count = 0
        total_count = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n测试 {i}/{total_count}: {test_case['query']}")
            
            try:
                # 执行完整查询处理
                result = test_system.process_user_query(test_case['query'])
                
                if result and "detail_type" in result:
                    actual_type = result.get("detail_type", "")
                    
                    print(f"   处理结果: 类型='{actual_type}'")
                    
                    # 验证结果
                    if actual_type == test_case["expected_type"]:
                        print("   ✓ 测试通过")
                        success_count += 1
                    else:
                        print(f"   ✗ 测试失败: 期望类型='{test_case['expected_type']}'")
                else:
                    print("   ✗ 测试失败: 未返回明细查询结果")
                    
            except Exception as e:
                print(f"   ✗ 测试异常: {e}")
        
        print(f"\n测试结果: {success_count}/{total_count} 通过")
        return success_count == total_count
    
    def test_regex_patterns(self):
        """测试正则表达式模式匹配"""
        print("\n=== 测试正则表达式模式匹配 ===")
        
        import re
        
        # 测试模式
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
        
        # 测试用例
        test_cases = [
            "列出'不准确'类型的问题",
            "显示'不完整'类型的问题",
            "查看'无关'类型的问题",
            "请列出'满意'类型的问题",
            "请显示'错误'类型的问题",
            "请查看'不准确'类型的问题",
            "不准确类型的问题列表",
            "不完整类型的问题明细",
            "无关类型的问题详情",
            "输出'满意'类型的问题",
            "导出'错误'类型的问题",
            "不准确类型的问题有哪些",
            "不完整类型的问题都有什么",
            "关于'无关'类型的问题",
            "列出'满意'问题",
            "显示'错误'问题",
            "查看'不准确'问题"
        ]
        
        success_count = 0
        total_count = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n测试 {i}/{total_count}: {test_case}")
            
            matched = False
            extracted_label = None
            
            for pattern in detail_patterns:
                match = re.search(pattern, test_case)
                if match:
                    matched = True
                    extracted_label = match.group(1).strip("'\"\"\"''")
                    break
            
            if matched and extracted_label:
                print(f"   ✓ 匹配成功: 提取标签='{extracted_label}'")
                success_count += 1
            else:
                print("   ✗ 匹配失败")
        
        print(f"\n测试结果: {success_count}/{total_count} 通过")
        return success_count == total_count
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始运行明细查询功能测试...")
        
        test_results = []
        
        # 运行各项测试
        test_results.append(("正则表达式模式匹配", self.test_regex_patterns()))
        test_results.append(("明细查询识别功能", self.test_detail_query_recognition()))
        test_results.append(("明细查询处理功能", self.test_detail_query_processing()))
        
        # 输出测试总结
        print("\n" + "="*50)
        print("测试总结:")
        print("="*50)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✓ 通过" if result else "✗ 失败"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\n总体结果: {passed}/{total} 项测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！明细查询功能正常工作。")
        else:
            print("⚠️  部分测试失败，需要进一步调试。")
        
        return passed == total
    
    def cleanup(self):
        """清理测试环境"""
        print("\n清理测试环境...")
        
        # 删除临时文件
        if os.path.exists(self.temp_badcase_file.name):
            os.unlink(self.temp_badcase_file.name)
        if os.path.exists(self.temp_kb_file.name):
            os.unlink(self.temp_kb_file.name)
        
        print("✓ 测试环境清理完成")


def main():
    """主函数"""
    print("明细查询功能测试")
    print("="*50)
    
    tester = DetailQueryTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    exit(main()) 