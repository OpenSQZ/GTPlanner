"""
集成测试脚本
测试系统的完整功能
"""

import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import GTPlannerSystem
from database_manager import DatabaseManager
from cache_manager import cache_manager
from logging_config import log_config
from config import config_manager


class IntegrationTest:
    """集成测试类"""
    
    def __init__(self):
        self.system = None
        self.test_results = []
    
    def setup(self):
        """设置测试环境"""
        print("=== 设置测试环境 ===")
        
        # 初始化系统
        self.system = GTPlannerSystem()
        
        # 初始化数据库
        self.db_manager = DatabaseManager("test.db")
        
        # 清空缓存
        cache_manager.clear()
        
        print("✓ 测试环境设置完成")
    
    def test_basic_functionality(self):
        """测试基本功能"""
        print("\n=== 测试基本功能 ===")
        
        # 测试查询处理
        test_queries = [
            "什么是Python？",
            "机器学习有什么应用？",
            "深度学习框架有哪些？"
        ]
        
        for query in test_queries:
            print(f"测试查询: {query}")
            start_time = time.time()
            
            try:
                result = self.system.process_user_query(query)
                processing_time = time.time() - start_time
                
                print(f"  回答长度: {len(result['answer'])} 字符")
                print(f"  处理时间: {processing_time:.2f} 秒")
                print(f"  反馈: {result['feedback']}")
                
                self.test_results.append({
                    'test': 'basic_functionality',
                    'query': query,
                    'success': True,
                    'processing_time': processing_time,
                    'answer_length': len(result['answer']),
                    'feedback': result['feedback']
                })
                
            except Exception as e:
                print(f"  ❌ 测试失败: {e}")
                self.test_results.append({
                    'test': 'basic_functionality',
                    'query': query,
                    'success': False,
                    'error': str(e)
                })
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        print("\n=== 测试缓存功能 ===")
        
        query = "测试缓存功能"
        
        # 第一次查询
        print("第一次查询...")
        start_time = time.time()
        result1 = self.system.process_user_query(query)
        time1 = time.time() - start_time
        
        # 第二次查询（应该从缓存获取）
        print("第二次查询（缓存）...")
        start_time = time.time()
        result2 = self.system.process_user_query(query)
        time2 = time.time() - start_time
        
        print(f"  第一次查询时间: {time1:.3f} 秒")
        print(f"  第二次查询时间: {time2:.3f} 秒")
        print(f"  缓存加速比: {time1/time2:.1f}x")
        
        # 检查缓存统计
        cache_stats = cache_manager.get_stats()
        print(f"  缓存命中率: {cache_stats['hit_rate']}")
        
        self.test_results.append({
            'test': 'cache_functionality',
            'success': True,
            'first_query_time': time1,
            'second_query_time': time2,
            'speedup_ratio': time1/time2,
            'cache_hit_rate': cache_stats['hit_rate']
        })
    
    def test_database_functionality(self):
        """测试数据库功能"""
        print("\n=== 测试数据库功能 ===")
        
        try:
            # 测试保存知识库文档
            doc_id = self.db_manager.save_knowledge_document(
                title="测试文档",
                content="这是一个测试文档的内容",
                keywords=["测试", "文档"]
            )
            print(f"  ✓ 知识库文档保存成功，ID: {doc_id}")
            
            # 测试获取知识库文档
            documents = self.db_manager.get_knowledge_documents()
            print(f"  ✓ 获取到 {len(documents)} 个知识库文档")
            
            # 测试保存BadCase
            badcase_id = self.db_manager.save_badcase(
                user_id="test_user",
                question="测试问题",
                answer="测试回答",
                feedback="满意",
                relevant_docs_count=1
            )
            print(f"  ✓ BadCase保存成功，ID: {badcase_id}")
            
            # 测试获取BadCase统计
            stats = self.db_manager.get_badcase_stats()
            print(f"  ✓ BadCase总数: {stats['total_count']}")
            
            self.test_results.append({
                'test': 'database_functionality',
                'success': True,
                'documents_count': len(documents),
                'badcase_count': stats['total_count']
            })
            
        except Exception as e:
            print(f"  ❌ 数据库测试失败: {e}")
            self.test_results.append({
                'test': 'database_functionality',
                'success': False,
                'error': str(e)
            })
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n=== 测试错误处理 ===")
        
        # 测试空查询
        try:
            result = self.system.process_user_query("")
            print("  ✓ 空查询处理正常")
        except Exception as e:
            print(f"  ❌ 空查询处理失败: {e}")
        
        # 测试超长查询
        long_query = "测试" * 1000
        try:
            result = self.system.process_user_query(long_query)
            print("  ✓ 超长查询处理正常")
        except Exception as e:
            print(f"  ❌ 超长查询处理失败: {e}")
        
        self.test_results.append({
            'test': 'error_handling',
            'success': True
        })
    
    def test_performance(self):
        """测试性能"""
        print("\n=== 测试性能 ===")
        
        queries = [
            "Python编程",
            "机器学习",
            "深度学习",
            "Web开发",
            "数据结构"
        ]
        
        total_time = 0
        total_queries = len(queries)
        
        for query in queries:
            start_time = time.time()
            try:
                result = self.system.process_user_query(query)
                query_time = time.time() - start_time
                total_time += query_time
                print(f"  {query}: {query_time:.3f} 秒")
            except Exception as e:
                print(f"  {query}: 失败 - {e}")
        
        avg_time = total_time / total_queries
        print(f"  平均查询时间: {avg_time:.3f} 秒")
        print(f"  总查询时间: {total_time:.3f} 秒")
        
        self.test_results.append({
            'test': 'performance',
            'success': True,
            'total_queries': total_queries,
            'total_time': total_time,
            'avg_time': avg_time
        })
    
    def generate_report(self):
        """生成测试报告"""
        print("\n=== 测试报告 ===")
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result['success'])
        success_rate = (successful_tests / total_tests) * 100
        
        print(f"总测试数: {total_tests}")
        print(f"成功测试数: {successful_tests}")
        print(f"成功率: {success_rate:.1f}%")
        
        # 详细结果
        for result in self.test_results:
            status = "✓" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if not result['success'] and 'error' in result:
                print(f"    错误: {result['error']}")
        
        # 保存报告
        report = {
            'timestamp': time.time(),
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': success_rate,
            'results': self.test_results
        }
        
        with open('test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n测试报告已保存到 test_report.json")
        
        return success_rate >= 80
    
    def cleanup(self):
        """清理测试环境"""
        print("\n=== 清理测试环境 ===")
        
        # 删除测试数据库
        if Path("test.db").exists():
            Path("test.db").unlink()
        
        # 清空缓存
        cache_manager.clear()
        
        print("✓ 测试环境清理完成")
    
    def run_all_tests(self):
        """运行所有测试"""
        try:
            self.setup()
            
            self.test_basic_functionality()
            self.test_cache_functionality()
            self.test_database_functionality()
            self.test_error_handling()
            self.test_performance()
            
            success = self.generate_report()
            
            if success:
                print("\n🎉 所有测试通过！")
            else:
                print("\n⚠️ 部分测试失败，请检查日志")
            
            return success
            
        finally:
            self.cleanup()


def main():
    """主函数"""
    print("GTPlanner 集成测试")
    print("=" * 50)
    
    test_runner = IntegrationTest()
    success = test_runner.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 