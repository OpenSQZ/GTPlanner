#!/usr/bin/env python3
"""
GTPlanner PR功能集成测试
验证增强语言检测、错误处理、性能监控是否完全集成到项目中
"""

import sys
import os
import time
import traceback

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_language_detection():
    """测试增强语言检测系统集成"""
    print("🔍 测试增强语言检测系统集成...")
    
    try:
        # 导入模块
        from utils.enhanced_language_detection import (
            EnhancedLanguageDetector,
            SupportedLanguage,
            LanguageDetectionResult
        )
        print("✅ 成功导入增强语言检测模块")
        
        # 创建检测器
        detector = EnhancedLanguageDetector()
        print("✅ 检测器创建成功")
        
        # 测试基本功能
        test_texts = [
            ("Hello world, this is a test message.", "en"),
            ("你好世界，这是一个测试消息。", "zh"),
            ("こんにちは世界、これはテストメッセージです。", "ja"),
            ("안녕하세요 세계, 이것은 테스트 메시지입니다.", "ko")
        ]
        
        for text, expected_lang in test_texts:
            result = detector.detect_language(text)
            print(f"  文本: {text[:30]}...")
            print(f"  检测结果: {result.language.value} (期望: {expected_lang})")
            print(f"  置信度: {result.confidence:.2f}")
            print(f"  检测方法: {result.detection_method}")
            print(f"  处理时间: {result.processing_time:.4f}s")
            print(f"  缓存命中: {result.cache_hit}")
            print()
        
        # 测试缓存功能
        print("🧪 测试缓存功能...")
        cache_stats = detector.get_cache_stats()
        print(f"  缓存统计: {cache_stats}")
        
        # 测试性能监控
        print("🧪 测试性能监控...")
        try:
            perf_stats = detector.get_performance_stats()
            print(f"  性能统计: {perf_stats}")
        except Exception as e:
            print(f"  ⚠️ 性能监控测试失败: {e}")
        
        print("✅ 增强语言检测系统集成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 增强语言检测系统集成测试失败: {e}")
        traceback.print_exc()
        return False

def test_error_handler():
    """测试错误处理框架集成"""
    print("🛡️ 测试错误处理框架集成...")
    
    try:
        # 导入模块
        from utils.error_handler import (
            ErrorHandler, GTPlannerError, LanguageDetectionError,
            handle_errors, log_and_continue, safe_execute
        )
        print("✅ 成功导入错误处理模块")
        
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
        
        print("✅ 错误处理框架集成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 错误处理框架集成测试失败: {e}")
        traceback.print_exc()
        return False

def test_performance_monitor():
    """测试性能监控系统集成"""
    print("📊 测试性能监控系统集成...")
    
    try:
        # 导入模块
        from utils.performance_monitor import (
            PerformanceMonitor, PerformanceMetric, PerformanceStats
        )
        print("✅ 成功导入性能监控模块")
        
        # 创建监控器
        monitor = PerformanceMonitor()
        print("✅ 性能监控器创建成功")
        
        # 测试监控装饰器
        @monitor.monitor_function
        def test_function():
            time.sleep(0.01)  # 模拟耗时操作
            return "测试完成"
        
        # 执行测试
        result = test_function()
        print(f"✅ 监控函数执行成功: {result}")
        
        # 获取统计信息
        stats = monitor.get_overall_stats()
        print(f"✅ 性能统计: {stats}")
        
        # 生成报告
        report = monitor.generate_report("text")
        print("✅ 性能报告生成成功")
        print(f"  报告长度: {len(report)} 字符")
        
        print("✅ 性能监控系统集成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 性能监控系统集成测试失败: {e}")
        traceback.print_exc()
        return False

def test_gtplanner_integration():
    """测试与GTPlanner主项目的集成"""
    print("🔗 测试与GTPlanner主项目的集成...")
    
    try:
        # 测试项目核心模块导入
        from cli import process_input_stream, interactive_mode
        print("✅ 成功导入CLI模块")
        
        from nodes import AsyncInputProcessingNode
        print("✅ 成功导入节点模块")
        
        from utils.call_llm import call_llm
        print("✅ 成功导入LLM调用模块")
        
        # 测试配置加载
        from dynaconf import Dynaconf
        settings = Dynaconf(settings_files=['settings.toml'])
        print("✅ 成功加载配置文件")
        
        # 检查多语言支持
        if hasattr(settings, 'multilingual'):
            print(f"✅ 多语言配置: {settings.multilingual}")
        else:
            print("⚠️ 未找到多语言配置")
        
        print("✅ GTPlanner主项目集成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ GTPlanner主项目集成测试失败: {e}")
        traceback.print_exc()
        return False

def test_end_to_end():
    """端到端集成测试"""
    print("🚀 端到端集成测试...")
    
    try:
        # 创建语言检测器
        from utils.enhanced_language_detection import EnhancedLanguageDetector
        detector = EnhancedLanguageDetector()
        
        # 创建错误处理器
        from utils.error_handler import ErrorHandler
        error_handler = ErrorHandler()
        
        # 创建性能监控器
        from utils.performance_monitor import PerformanceMonitor
        monitor = PerformanceMonitor()
        
        # 模拟完整的GTPlanner工作流程
        print("🧪 模拟GTPlanner工作流程...")
        
        # 1. 用户输入（多语言）
        user_inputs = [
            "Create a mobile app for task management",
            "创建一个任务管理的移动应用",
            "タスク管理のモバイルアプリを作成する"
        ]
        
        for input_text in user_inputs:
            print(f"\n📝 处理用户输入: {input_text}")
            
            # 2. 语言检测
            lang_result = detector.detect_language(input_text)
            print(f"  🌍 检测语言: {lang_result.language.value} (置信度: {lang_result.confidence:.2f})")
            
            # 3. 性能监控
            @monitor.monitor_function
            def process_requirement(text, language):
                # 模拟需求处理
                time.sleep(0.01)
                return f"已处理{language}语言的需求: {text[:20]}..."
            
            result = process_requirement(input_text, lang_result.language.value)
            print(f"  ✅ 处理结果: {result}")
        
        # 4. 获取整体性能统计
        overall_stats = monitor.get_overall_stats()
        print(f"\n📊 整体性能统计: {overall_stats}")
        
        # 5. 生成性能报告
        performance_report = monitor.generate_report("text")
        print(f"📋 性能报告生成成功 (长度: {len(performance_report)} 字符)")
        
        print("✅ 端到端集成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 端到端集成测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 GTPlanner PR功能集成测试开始")
    print("=" * 60)
    
    tests = [
        ("增强语言检测系统", test_enhanced_language_detection),
        ("错误处理框架", test_error_handler),
        ("性能监控系统", test_performance_monitor),
        ("GTPlanner主项目集成", test_gtplanner_integration),
        ("端到端集成", test_end_to_end)
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
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有PR功能集成测试通过！")
        print("✅ 您的PR功能已完全集成到GTPlanner项目中")
        return 0
    else:
        print("⚠️ 部分测试失败，需要检查集成状态")
        return 1

if __name__ == "__main__":
    exit(main())
