"""
增强语言检测模块测试套件 - Enhanced Language Detection Test Suite

这个测试文件是GTPlanner项目增强语言检测功能的全面测试覆盖，
确保新功能的正确性、稳定性和性能。

测试覆盖范围：
1. 基本语言检测功能测试
2. 边界情况和异常处理测试
3. 置信度评分准确性测试
4. 缓存系统功能测试
5. 性能特性测试
6. 多语言支持测试

测试目标：
- 验证语言检测算法的准确性
- 确保缓存系统的正确性
- 测试错误处理的健壮性
- 验证性能优化的效果
- 确保向后兼容性

与GTPlanner的集成作用：
- 保证语言检测功能的可靠性
- 支持多语言PRD生成的稳定性
- 为性能优化提供测试基准
- 确保系统整体质量
"""

import unittest
import time
import tempfile
import os
from unittest.mock import patch, MagicMock
from typing import List, Dict, Any

# 导入被测试的模块
from utils.enhanced_language_detection import (
    EnhancedLanguageDetector,
    SupportedLanguage,
    LanguageDetectionResult
)

class TestEnhancedLanguageDetector(unittest.TestCase):
    """
    增强语言检测器测试类
    
    全面测试增强语言检测器的各种功能，包括：
    1. 基本语言检测
    2. 边界情况处理
    3. 缓存系统
    4. 性能特性
    5. 错误处理
    """
    
    def setUp(self):
        """
        测试前的准备工作
        
        为每个测试用例创建新的检测器实例，确保测试的独立性。
        """
        self.detector = EnhancedLanguageDetector()
        
        # 测试用的多语言文本样本
        self.test_texts = {
            'english': [
                "Hello world, this is a test message in English.",
                "The quick brown fox jumps over the lazy dog.",
                "This is a sample text for testing language detection.",
                "Python is a programming language that emphasizes code readability."
            ],
            'chinese': [
                "你好世界，这是一个中文测试消息。",
                "今天天气很好，适合出去散步。",
                "这是一个用于测试语言检测的样本文本。",
                "Python是一种强调代码可读性的编程语言。"
            ],
            'japanese': [
                "こんにちは世界、これは日本語のテストメッセージです。",
                "今日は天気が良くて、散歩に適しています。",
                "これは言語検出をテストするためのサンプルテキストです。",
                "Pythonはコードの可読性を重視するプログラミング言語です。"
            ],
            'korean': [
                "안녕하세요 세계, 이것은 한국어 테스트 메시지입니다.",
                "오늘 날씨가 좋아서 산책하기에 적합합니다.",
                "이것은 언어 감지를 테스트하기 위한 샘플 텍스트입니다.",
                "Python은 코드 가독성을 중시하는 프로그래밍 언어입니다."
            ],
            'mixed': [
                "Hello 世界! This is a mixed 语言 text.",
                "こんにちは! 今天天气很好! Hello!",
                "안녕하세요! こんにちは! Hello! 你好!"
            ]
        }
    
    def tearDown(self):
        """
        测试后的清理工作
        
        清理测试过程中创建的资源，确保测试环境的清洁。
        """
        # 清理缓存
        self.detector.clear_cache()
    
    def test_initialization(self):
        """
        测试检测器初始化
        
        验证检测器是否正确初始化，包括：
        - 默认语言设置
        - 缓存系统初始化
        - 语言模式库加载
        """
        # 验证默认语言
        self.assertEqual(self.detector.default_language, SupportedLanguage.ENGLISH)
        
        # 验证缓存系统
        self.assertIsInstance(self.detector._cache, dict)
        self.assertEqual(self.detector._cache_size, 1000)
        
        # 验证语言模式库
        self.assertIsInstance(self.detector._language_patterns, dict)
        self.assertGreater(len(self.detector._language_patterns), 0)
        
        # 验证N-gram频率库
        self.assertIsInstance(self.detector._ngram_frequencies, dict)
        self.assertIn('bigrams', self.detector._ngram_frequencies)
        self.assertIn('trigrams', self.detector._ngram_frequencies)
    
    def test_english_detection(self):
        """
        测试英语检测
        
        验证英语文本的检测准确性，包括：
        - 纯英语文本
        - 包含特殊字符的英语文本
        - 技术术语英语文本
        """
        for text in self.test_texts['english']:
            with self.subTest(text=text):
                result = self.detector.detect_language(text)
                
                # 验证检测结果
                self.assertIsInstance(result, LanguageDetectionResult)
                self.assertEqual(result.language, SupportedLanguage.ENGLISH)
                self.assertGreater(result.confidence, 0.5)  # 置信度应该较高
                self.assertEqual(result.detection_method, "multi_algorithm_fusion")
                self.assertFalse(result.cache_hit)  # 第一次检测不应该命中缓存
    
    def test_chinese_detection(self):
        """
        测试中文检测
        
        验证中文文本的检测准确性，包括：
        - 简体中文文本
        - 包含标点符号的中文文本
        - 技术术语中文文本
        """
        for text in self.test_texts['chinese']:
            with self.subTest(text=text):
                result = self.detector.detect_language(text)
                
                # 验证检测结果
                self.assertIsInstance(result, LanguageDetectionResult)
                self.assertEqual(result.language, SupportedLanguage.CHINESE)
                self.assertGreater(result.confidence, 0.6)  # 中文检测置信度应该很高
                self.assertEqual(result.detection_method, "multi_algorithm_fusion")
                
                # 验证额外信息
                self.assertIn('ngram_scores', result.additional_info)
                self.assertIn('pattern_scores', result.additional_info)
    
    def test_japanese_detection(self):
        """
        测试日语检测
        
        验证日语文本的检测准确性，包括：
        - 平假名文本
        - 片假名文本
        - 汉字混合文本
        """
        for text in self.test_texts['japanese']:
            with self.subTest(text=text):
                result = self.detector.detect_language(text)
                
                # 验证检测结果
                self.assertIsInstance(result, LanguageDetectionResult)
                self.assertEqual(result.language, SupportedLanguage.JAPANESE)
                self.assertGreater(result.confidence, 0.5)
                self.assertEqual(result.detection_method, "multi_algorithm_fusion")
    
    def test_korean_detection(self):
        """
        测试韩语检测
        
        验证韩语文本的检测准确性，包括：
        - 韩文字符文本
        - 韩文标点符号
        - 韩文技术术语
        """
        for text in self.test_texts['korean']:
            with self.subTest(text=text):
                result = self.detector.detect_language(text)
                
                # 验证检测结果
                self.assertIsInstance(result, LanguageDetectionResult)
                self.assertEqual(result.language, SupportedLanguage.KOREAN)
                self.assertGreater(result.confidence, 0.5)
                self.assertEqual(result.detection_method, "multi_algorithm_fusion")
    
    def test_mixed_language_detection(self):
        """
        测试混合语言检测
        
        验证包含多种语言的文本的检测准确性，这是GTPlanner多语言支持的重要场景。
        """
        for text in self.test_texts['mixed']:
            with self.subTest(text=text):
                result = self.detector.detect_language(text)
                
                # 验证检测结果
                self.assertIsInstance(result, LanguageDetectionResult)
                self.assertIn(result.language, [
                    SupportedLanguage.ENGLISH,
                    SupportedLanguage.CHINESE,
                    SupportedLanguage.JAPANESE,
                    SupportedLanguage.KOREAN
                ])
                self.assertGreater(result.confidence, 0.3)  # 混合语言置信度可能较低
    
    def test_empty_text_handling(self):
        """
        测试空文本处理
        
        验证检测器对空文本和无效输入的处理，确保系统的健壮性。
        """
        # 测试空字符串
        result = self.detector.detect_language("")
        self.assertEqual(result.language, SupportedLanguage.ENGLISH)  # 默认语言
        self.assertEqual(result.confidence, 0.0)
        self.assertEqual(result.detection_method, "default_fallback")
        
        # 测试None值
        result = self.detector.detect_language(None)
        self.assertEqual(result.language, SupportedLanguage.ENGLISH)
        self.assertEqual(result.confidence, 0.0)
        
        # 测试只包含空格的文本
        result = self.detector.detect_language("   \n\t   ")
        self.assertEqual(result.language, SupportedLanguage.ENGLISH)
        self.assertEqual(result.confidence, 0.0)
    
    def test_cache_functionality(self):
        """
        测试缓存功能
        
        验证智能缓存系统的正确性，包括：
        - 缓存命中
        - 缓存键生成
        - 缓存清理
        """
        text = "Hello world, this is a test message."
        
        # 第一次检测
        result1 = self.detector.detect_language(text)
        self.assertFalse(result1.cache_hit)
        
        # 第二次检测（应该命中缓存）
        result2 = self.detector.detect_language(text)
        self.assertTrue(result2.cache_hit)
        
        # 验证结果一致性
        self.assertEqual(result1.language, result2.language)
        self.assertEqual(result1.confidence, result2.confidence)
        
        # 验证缓存统计
        cache_stats = self.detector.get_cache_stats()
        self.assertGreater(cache_stats['total_entries'], 0)
        self.assertGreater(cache_stats['valid_entries'], 0)
    
    def test_cache_key_uniqueness(self):
        """
        测试缓存键唯一性
        
        验证不同文本生成不同的缓存键，确保缓存的正确性。
        """
        text1 = "Hello world"
        text2 = "Hello world!"  # 稍微不同的文本
        
        key1 = self.detector._get_cache_key(text1)
        key2 = self.detector._get_cache_key(text2)
        
        # 验证键的唯一性
        self.assertNotEqual(key1, key2)
        
        # 验证相同文本生成相同键
        key1_again = self.detector._get_cache_key(text1)
        self.assertEqual(key1, key1_again)
    
    def test_cache_cleanup(self):
        """
        测试缓存清理
        
        验证缓存系统的内存管理功能，防止内存泄漏。
        """
        # 添加一些测试数据
        for i in range(10):
            text = f"Test text {i}"
            self.detector.detect_language(text)
        
        # 验证缓存中有数据
        initial_stats = self.detector.get_cache_stats()
        self.assertGreater(initial_stats['total_entries'], 0)
        
        # 清理缓存
        self.detector.clear_cache()
        
        # 验证缓存已清空
        final_stats = self.detector.get_cache_stats()
        self.assertEqual(final_stats['total_entries'], 0)
    
    def test_confidence_scoring(self):
        """
        测试置信度评分
        
        验证置信度计算的准确性，这是语言检测可靠性的重要指标。
        """
        # 测试纯英语文本（应该高置信度）
        result = self.detector.detect_language("Hello world, this is a test message.")
        self.assertGreater(result.confidence, 0.7)
        
        # 测试混合语言文本（应该较低置信度）
        result = self.detector.detect_language("Hello 世界!")
        self.assertLess(result.confidence, 0.8)
        
        # 验证置信度范围
        self.assertGreaterEqual(result.confidence, 0.0)
        self.assertLessEqual(result.confidence, 1.0)
    
    def test_performance_characteristics(self):
        """
        测试性能特性
        
        验证检测器的性能表现，确保在实际使用中的效率。
        """
        text = "Hello world, this is a test message for performance testing."
        
        # 测试执行时间
        start_time = time.time()
        result = self.detector.detect_language(text)
        execution_time = time.time() - start_time
        
        # 验证执行时间合理（应该很快）
        self.assertLess(execution_time, 1.0)  # 1秒内应该完成
        
        # 验证处理时间记录
        self.assertGreaterEqual(result.processing_time, 0.0)
        self.assertLess(result.processing_time, 1.0)
    
    def test_error_handling(self):
        """
        测试错误处理
        
        验证检测器在异常情况下的健壮性，确保系统稳定性。
        """
        # 测试异常情况下的降级处理
        with patch.object(self.detector, '_analyze_ngram_frequencies', side_effect=Exception("Test error")):
            result = self.detector.detect_language("Hello world")
            
            # 应该返回默认语言
            self.assertEqual(result.language, SupportedLanguage.ENGLISH)
            self.assertEqual(result.confidence, 0.0)
            self.assertEqual(result.detection_method, "error_fallback")
    
    def test_language_specific_patterns(self):
        """
        测试语言特定模式
        
        验证各种语言的特定模式识别，确保检测的准确性。
        """
        # 测试中文汉字模式
        chinese_text = "汉字测试"
        result = self.detector.detect_language(chinese_text)
        self.assertEqual(result.language, SupportedLanguage.CHINESE)
        
        # 测试日语假名模式
        japanese_text = "ひらがなカタカナ"
        result = self.detector.detect_language(japanese_text)
        self.assertEqual(result.language, SupportedLanguage.JAPANESE)
        
        # 测试韩文字符模式
        korean_text = "한글테스트"
        result = self.detector.detect_language(korean_text)
        self.assertEqual(result.language, SupportedLanguage.KOREAN)
    
    def test_ngram_analysis(self):
        """
        测试N-gram分析
        
        验证N-gram频率分析的正确性，这是语言检测的核心算法。
        """
        # 测试英语文本的N-gram分析
        english_text = "The quick brown fox"
        ngram_scores = self.detector._analyze_ngram_frequencies(english_text)
        
        # 验证返回结果
        self.assertIsInstance(ngram_scores, dict)
        self.assertIn(SupportedLanguage.ENGLISH, ngram_scores)
        
        # 验证英语分数应该较高
        english_score = ngram_scores.get(SupportedLanguage.ENGLISH, 0)
        self.assertGreater(english_score, 0)
    
    def test_pattern_matching(self):
        """
        测试模式匹配
        
        验证加权模式匹配的正确性，这是语言检测的另一个重要算法。
        """
        # 测试中文文本的模式匹配
        chinese_text = "你好世界"
        pattern_scores = self.detector._weighted_pattern_matching(chinese_text)
        
        # 验证返回结果
        self.assertIsInstance(pattern_scores, dict)
        self.assertIn(SupportedLanguage.CHINESE, pattern_scores)
        
        # 验证中文分数应该较高
        chinese_score = pattern_scores.get(SupportedLanguage.CHINESE, 0)
        self.assertGreater(chinese_score, 0)
    
    def test_english_specific_detection(self):
        """
        测试英语特定检测
        
        验证英语特殊模式的识别，因为英语是GTPlanner的默认语言。
        """
        # 测试英语后缀模式
        english_text = "This is a beautiful creation with wonderful development"
        english_score = self.detector._detect_english_specific(english_text)
        
        # 验证英语特定分数
        self.assertGreater(english_score, 0)
        
        # 测试不包含英语特定模式的文本
        chinese_text = "你好世界"
        english_score = self.detector._detect_english_specific(chinese_text)
        self.assertEqual(english_score, 0)
    
    def test_score_combination(self):
        """
        测试分数融合
        
        验证不同算法分数的融合策略，确保最终结果的准确性。
        """
        # 模拟不同算法的分数
        ngram_scores = {SupportedLanguage.ENGLISH: 0.8, SupportedLanguage.CHINESE: 0.2}
        pattern_scores = {SupportedLanguage.ENGLISH: 0.7, SupportedLanguage.CHINESE: 0.3}
        english_score = 0.6
        
        # 测试分数融合
        combined_scores = self.detector._combine_scores(ngram_scores, pattern_scores, english_score)
        
        # 验证融合结果
        self.assertIsInstance(combined_scores, dict)
        self.assertIn(SupportedLanguage.ENGLISH, combined_scores)
        self.assertIn(SupportedLanguage.CHINESE, combined_scores)
        
        # 验证英语分数应该最高
        english_final = combined_scores[SupportedLanguage.ENGLISH]
        chinese_final = combined_scores[SupportedLanguage.CHINESE]
        self.assertGreater(english_final, chinese_final)
    
    def test_confidence_calculation(self):
        """
        测试置信度计算
        
        验证置信度计算的逻辑，确保结果的可靠性。
        """
        # 测试高置信度情况（分数差距大）
        scores = {SupportedLanguage.ENGLISH: 0.9, SupportedLanguage.CHINESE: 0.1}
        confidence = self.detector._calculate_confidence(scores)
        self.assertGreater(confidence, 0.7)
        
        # 测试低置信度情况（分数接近）
        scores = {SupportedLanguage.ENGLISH: 0.51, SupportedLanguage.CHINESE: 0.49}
        confidence = self.detector._calculate_confidence(scores)
        self.assertLess(confidence, 0.6)
        
        # 验证置信度范围
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_cache_validation(self):
        """
        测试缓存验证
        
        验证缓存有效性的检查逻辑，确保缓存系统的正确性。
        """
        # 创建测试缓存条目
        cache_entry = {
            'timestamp': time.time(),
            'language': SupportedLanguage.ENGLISH,
            'confidence': 0.8
        }
        
        # 测试有效缓存
        is_valid = self.detector._is_cache_valid(cache_entry)
        self.assertTrue(is_valid)
        
        # 测试过期缓存
        old_cache_entry = {
            'timestamp': time.time() - 7200,  # 2小时前
            'language': SupportedLanguage.ENGLISH,
            'confidence': 0.8
        }
        is_valid = self.detector._is_cache_valid(old_cache_entry)
        self.assertFalse(is_valid)
    
    def test_language_code_mapping(self):
        """
        测试语言代码映射
        
        验证语言代码到枚举值的正确映射。
        """
        # 测试有效的语言代码
        english = self.detector._get_language_by_code('en')
        self.assertEqual(english, SupportedLanguage.ENGLISH)
        
        chinese = self.detector._get_language_by_code('zh')
        self.assertEqual(chinese, SupportedLanguage.CHINESE)
        
        # 测试无效的语言代码
        invalid = self.detector._get_language_by_code('invalid')
        self.assertIsNone(invalid)
    
    def test_cache_size_management(self):
        """
        测试缓存大小管理
        
        验证缓存大小的动态调整功能。
        """
        # 设置较小的缓存大小
        self.detector.set_cache_size(5)
        
        # 添加超过限制的条目
        for i in range(10):
            text = f"Test text {i}"
            self.detector.detect_language(text)
        
        # 验证缓存大小被限制
        cache_stats = self.detector.get_cache_stats()
        self.assertLessEqual(cache_stats['total_entries'], 5)
    
    def test_system_integration(self):
        """
        测试系统集成
        
        验证检测器与GTPlanner系统的集成兼容性。
        """
        # 测试与多语言系统的集成
        detector = EnhancedLanguageDetector(default_language=SupportedLanguage.CHINESE)
        
        # 验证默认语言设置
        self.assertEqual(detector.default_language, SupportedLanguage.CHINESE)
        
        # 测试空文本处理
        result = detector.detect_language("")
        self.assertEqual(result.language, SupportedLanguage.CHINESE)
    
    def test_performance_under_load(self):
        """
        测试负载下的性能
        
        验证检测器在高负载情况下的性能表现。
        """
        # 准备大量测试文本
        test_texts = [f"Test text {i} for performance testing under load conditions." 
                     for i in range(100)]
        
        start_time = time.time()
        
        # 批量检测
        results = []
        for text in test_texts:
            result = self.detector.detect_language(text)
            results.append(result)
        
        total_time = time.time() - start_time
        
        # 验证性能（100个文本应该在合理时间内完成）
        self.assertLess(total_time, 10.0)  # 10秒内应该完成
        
        # 验证所有结果都有效
        for result in results:
            self.assertIsInstance(result, LanguageDetectionResult)
            self.assertGreater(result.confidence, 0.0)
    
    def test_memory_efficiency(self):
        """
        测试内存效率
        
        验证检测器的内存使用效率，防止内存泄漏。
        """
        # 记录初始内存使用
        initial_memory = self.detector._get_memory_usage()
        
        # 执行大量检测操作
        for i in range(1000):
            text = f"Memory test text {i} for testing memory efficiency under load."
            self.detector.detect_language(text)
        
        # 记录最终内存使用
        final_memory = self.detector._get_memory_usage()
        
        # 验证内存增长在合理范围内（不应该无限增长）
        memory_growth = final_memory - initial_memory
        self.assertLess(memory_growth, 100.0)  # 内存增长应该小于100MB
    
    def test_backward_compatibility(self):
        """
        测试向后兼容性
        
        验证新功能与现有系统的兼容性，确保平滑升级。
        """
        # 测试基本接口兼容性
        text = "Hello world"
        result = self.detector.detect_language(text)
        
        # 验证返回结果包含所有必要属性
        self.assertIsInstance(result.language, SupportedLanguage)
        self.assertIsInstance(result.confidence, float)
        self.assertIsInstance(result.detection_method, str)
        self.assertIsInstance(result.processing_time, float)
        self.assertIsInstance(result.cache_hit, bool)
        self.assertIsInstance(result.additional_info, dict)
    
    def test_error_recovery(self):
        """
        测试错误恢复
        
        验证检测器在遇到错误后的恢复能力。
        """
        # 模拟各种错误情况
        error_texts = [
            "",           # 空文本
            None,         # None值
            "   ",        # 只包含空格
            "a",          # 单个字符
            "123",        # 纯数字
            "!@#$%",      # 纯符号
        ]
        
        for text in error_texts:
            with self.subTest(text=text):
                try:
                    result = self.detector.detect_language(text)
                    # 应该返回默认语言
                    self.assertEqual(result.language, SupportedLanguage.ENGLISH)
                    self.assertEqual(result.confidence, 0.0)
                except Exception as e:
                    self.fail(f"检测器应该能够处理文本 '{text}'，但抛出了异常: {e}")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
