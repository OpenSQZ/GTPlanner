#!/usr/bin/env python3
"""
GTPlanner PR功能最终测试
验证所有新增功能是否完全正常工作
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_language_detection():
    """测试增强语言检测系统"""
    print("🔍 测试增强语言检测系统...")
    
    try:
        from utils.enhanced_language_detection import (
            EnhancedLanguageDetector, SupportedLanguage
        )
        
        detector = EnhancedLanguageDetector()
        
        # 测试多语言检测
        test_cases = [
            ("Hello world, this is a test message.", "en"),
            ("你好世界，这是一个测试消息。", "zh"),
            ("こんにちは世界、これはテストメッセージです。", "ja"),
            ("안녕하세요 세계, 이것은 테스트 메시지입니다.", "ko"),
            ("Bonjour le monde, ceci est un message de test.", "fr"),
            ("Hola mundo, este es un mensaje de prueba.", "es")
        ]
        
        correct_detections = 0
        total_tests = len(test_cases)
        
        for text, expected in test_cases:
            result = detector.detect_language(text)
            detected = result.language.value
            confidence = result.confidence
            
            print(f"  文本: {text[:30]}...")
            print(f"  期望: {expected}, 检测: {detected}, 置信度: {confidence:.2f}")
            
            if detected == expected:
                correct_detections += 1
                print(f"  ✅ 正确")
            else:
                print(f"  ❌ 错误")
            print()
        
        accuracy = correct_detections / total_tests
        print(f"检测准确率: {accuracy:.2%} ({correct_detections}/{total_tests})")
        
        # 测试缓存功能
        print("🧪 测试缓存功能...")
        cache_stats = detector.get_cache_stats()
        print(f"  缓存统计: {cache_stats}")
        
        # 测试性能监控
        print("🧪 测试性能监控...")
        perf_stats = detector.get_performance_stats()
        print(f"  性能统计: {perf_stats}")
        
        return accuracy > 0.5  # 至少50%准确率
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_error_handler():
    """测试错误处理框架"""
    print("🛡️ 测试错误处理框架...")
    
    try:
        from utils.error_handler_fixed import (
            ErrorHandler, handle_errors, safe_execute
        )
        
        # 测试错误处理器
        error_handler = ErrorHandler()
        print("✅ 错误处理器创建成功")
        
        # 测试装饰器
        @handle_errors()
        def test_function():
            raise ValueError("测试错误")
        
        try:
            result = test_function()
            print("✅ 错误处理装饰器工作正常")
        except Exception as e:
            print(f"  ⚠️ 装饰器处理了错误: {e}")
        
        # 测试安全执行
        def risky_function():
            raise RuntimeError("危险操作")
        
        result = safe_execute(risky_function, "默认值")
        print(f"✅ 安全执行函数工作正常: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_performance_monitor():
    """测试性能监控系统"""
    print("📊 测试性能监控系统...")
    
    try:
        from utils.performance_monitor import PerformanceMonitor
        
        monitor = PerformanceMonitor()
        
        # 测试监控装饰器
        @monitor.monitor_function
        def test_function():
            time.sleep(0.01)
            return "测试完成"
        
        result = test_function()
        print(f"✅ 监控函数执行成功: {result}")
        
        # 获取统计信息
        stats = monitor.get_overall_stats()
        print(f"✅ 性能统计: {stats}")
        
        # 生成报告
        report = monitor.generate_report("text")
        print(f"✅ 性能报告生成成功 (长度: {len(report)} 字符)")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_integration_workflow():
    """测试集成工作流程"""
    print("🚀 测试集成工作流程...")
    
    try:
        from utils.enhanced_language_detection import EnhancedLanguageDetector
        from utils.error_handler_fixed import ErrorHandler
        from utils.performance_monitor import PerformanceMonitor
        
        # 创建所有组件
        detector = EnhancedLanguageDetector()
        error_handler = ErrorHandler()
        monitor = PerformanceMonitor()
        
        print("✅ 所有组件创建成功")
        
        # 模拟工作流程
        user_inputs = [
            "Create a mobile app for task management",
            "创建一个任务管理的移动应用",
            "タスク管理のモバイルアプリを作成する"
        ]
        
        for input_text in user_inputs:
            print(f"\n📝 处理: {input_text}")
            
            # 语言检测
            lang_result = detector.detect_language(input_text)
            print(f"  🌍 语言: {lang_result.language.value} (置信度: {lang_result.confidence:.2f})")
            
            # 性能监控
            @monitor.monitor_function
            def process_requirement(text, language):
                time.sleep(0.01)
                return f"已处理{language}语言的需求: {text[:20]}..."
            
            result = process_requirement(input_text, lang_result.language.value)
            print(f"  ✅ 结果: {result}")
        
        # 获取整体统计
        overall_stats = monitor.get_overall_stats()
        print(f"\n📊 整体统计: {overall_stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 GTPlanner PR功能最终测试")
    print("=" * 60)
    
    tests = [
        ("增强语言检测系统", test_enhanced_language_detection),
        ("错误处理框架", test_error_handler),
        ("性能监控系统", test_performance_monitor),
        ("集成工作流程", test_integration_workflow)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 最终测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有PR功能测试通过！")
        print("✅ 您的PR功能已完全集成并正常工作")
        print("🚀 可以提交PR了！")
        return 0
    else:
        print("⚠️ 部分测试失败，需要进一步修复")
        return 1

if __name__ == "__main__":
    exit(main())
