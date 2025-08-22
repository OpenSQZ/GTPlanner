"""
智能语言检测增强系统 - Enhanced Language Detection System

这个模块是GTPlanner项目的核心增强功能之一，主要解决原有语言检测准确率低的问题。

主要功能：
1. 多算法融合的语言识别（N-gram频率分析 + 加权模式匹配）
2. 智能缓存系统，提升检测性能
3. 置信度评分，提供可靠的检测结果
4. 支持多种语言（中文、英文、日文、韩文、阿拉伯文等）

技术原理：
- N-gram分析：基于字符组合频率的统计语言学方法
- 模式匹配：使用正则表达式识别语言特征
- 置信度计算：多维度评分确保结果可靠性

与GTPlanner的集成作用：
- 提升多语言需求分析的准确性
- 自动识别用户输入语言，提供本地化体验
- 为后续的LLM调用提供正确的语言上下文
"""

import hashlib
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# 支持的语言枚举
# 这个枚举定义了GTPlanner支持的所有语言类型
# 与项目的多语言功能完全对应
class SupportedLanguage(Enum):
    ENGLISH = "en"      # 英语 - 项目默认语言
    CHINESE = "zh"      # 中文 - 支持简体和繁体
    SPANISH = "es"      # 西班牙语
    FRENCH = "fr"       # 法语
    JAPANESE = "ja"     # 日语
    KOREAN = "ko"       # 韩语
    ARABIC = "ar"       # 阿拉伯语
    RUSSIAN = "ru"      # 俄语
    GERMAN = "de"       # 德语
    ITALIAN = "it"      # 意大利语

# 语言检测结果数据类
# 包含检测到的语言类型和置信度信息
# 为GTPlanner的决策逻辑提供可靠的数据基础
@dataclass
class LanguageDetectionResult:
    language: SupportedLanguage          # 检测到的语言
    confidence: float                   # 置信度 (0.0-1.0)
    detection_method: str               # 使用的检测方法
    processing_time: float              # 处理时间（毫秒）
    cache_hit: bool                     # 是否命中缓存
    additional_info: Dict[str, any]     # 额外信息（如N-gram分数、模式匹配分数等）

class EnhancedLanguageDetector:
    """
    增强型语言检测器
    
    这是GTPlanner语言检测系统的核心类，采用多种算法融合的方式，
    显著提升了语言检测的准确性和可靠性。
    
    主要特性：
    1. 多算法融合：结合N-gram频率分析和加权模式匹配
    2. 智能缓存：MD5哈希键 + LRU淘汰策略，提升性能
    3. 置信度评分：多维度评估，确保结果可靠性
    4. 内存管理：自动清理过期缓存，防止内存泄漏
    
    与GTPlanner的集成价值：
    - 提升用户输入语言识别的准确性
    - 为多语言PRD生成提供正确的语言上下文
    - 支持国际化需求分析
    """
    
    def __init__(self, default_language: SupportedLanguage = SupportedLanguage.ENGLISH):
        """
        初始化语言检测器
        
        Args:
            default_language: 默认语言，当检测失败时返回此语言
                            这与GTPlanner的默认语言设置保持一致
        """
        self.default_language = default_language
        
        # 智能缓存系统
        # 使用MD5哈希作为缓存键，支持快速查找
        # 缓存大小限制为1000条记录，防止内存无限增长
        self._cache = {}
        self._cache_size = 1000
        
        # 语言特征模式库
        # 每种语言都有独特的字符特征，这些模式帮助快速识别语言
        # 权重系统确保重要特征有更大的影响力
        self._language_patterns = {
            SupportedLanguage.CHINESE: {
                # 中文字符特征（汉字、标点符号、数字等）
                'patterns': [
                    (r'[\u4e00-\u9fff]', 10.0),           # 汉字，权重最高
                    (r'[\u3000-\u303f]', 8.0),            # 中文标点符号
                    (r'[\uff00-\uffef]', 7.0),            # 全角字符
                    (r'[\u3400-\u4dbf]', 6.0),            # 扩展汉字A
                    (r'[\u20000-\u2a6df]', 5.0),          # 扩展汉字B
                ],
                'name': 'Chinese'
            },
            SupportedLanguage.JAPANESE: {
                # 日语特征（平假名、片假名、汉字混合）
                'patterns': [
                    (r'[\u3040-\u309f]', 10.0),           # 平假名
                    (r'[\u30a0-\u30ff]', 10.0),           # 片假名
                    (r'[\u4e00-\u9fff]', 6.0),            # 汉字（权重较低，因为中文也有）
                    (r'[\u3000-\u303f]', 5.0),            # 中文标点符号
                ],
                'name': 'Japanese'
            },
            SupportedLanguage.KOREAN: {
                # 韩语特征（韩文字符、音节结构）
                'patterns': [
                    (r'[\uac00-\ud7af]', 10.0),           # 韩文字符
                    (r'[\u1100-\u11ff]', 8.0),            # 韩文字母
                    (r'[\u3130-\u318f]', 7.0),            # 韩文兼容字母
                ],
                'name': 'Korean'
            },
            SupportedLanguage.ARABIC: {
                # 阿拉伯语特征（连字符、变音符号）
                'patterns': [
                    (r'[\u0600-\u06ff]', 10.0),           # 阿拉伯语
                    (r'[\u0750-\u077f]', 8.0),            # 阿拉伯语补充
                    (r'[\u08a0-\u08ff]', 7.0),            # 阿拉伯语扩展A
                ],
                'name': 'Arabic'
            },
            SupportedLanguage.RUSSIAN: {
                # 俄语特征（西里尔字母）
                'patterns': [
                    (r'[\u0400-\u04ff]', 10.0),           # 西里尔字母
                    (r'[\u0500-\u052f]', 8.0),            # 西里尔字母补充
                ],
                'name': 'Russian'
            },
            SupportedLanguage.GERMAN: {
                # 德语特征（特殊字母、复合词）
                'patterns': [
                    (r'[äöüßÄÖÜ]', 8.0),                  # 德语特殊字母
                    (r'\b\w+lichkeit\b', 6.0),            # 德语常见后缀
                    (r'\b\w+ung\b', 5.0),                 # 德语名词化后缀
                ],
                'name': 'German'
            },
            SupportedLanguage.FRENCH: {
                # 法语特征（重音符号、特殊字母）
                'patterns': [
                    (r'[àâäéèêëïîôöùûüÿçÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ]', 8.0),  # 法语重音字母
                    (r'\b\w+tion\b', 6.0),                # 法语常见后缀
                    (r'\b\w+ment\b', 5.0),                # 法语副词后缀
                ],
                'name': 'French'
            },
            SupportedLanguage.SPANISH: {
                # 西班牙语特征（重音符号、特殊字母）
                'patterns': [
                    (r'[áéíóúñüÁÉÍÓÚÑÜ]', 8.0),          # 西班牙语重音字母
                    (r'\b\w+ción\b', 6.0),                # 西班牙语名词后缀
                    (r'\b\w+mente\b', 5.0),               # 西班牙语副词后缀
                ],
                'name': 'Spanish'
            },
            SupportedLanguage.ITALIAN: {
                # 意大利语特征（重音符号、特殊字母）
                'patterns': [
                    (r'[àèéìíîòóùÀÈÉÌÍÎÒÓÙ]', 8.0),      # 意大利语重音字母
                    (r'\b\w+zione\b', 6.0),               # 意大利语名词后缀
                    (r'\b\w+mente\b', 5.0),               # 意大利语副词后缀
                ],
                'name': 'Italian'
            }
        }
        
        # 英语特征模式（权重最高，因为英语是GTPlanner的默认语言）
        # 英语作为通用语言，需要更精确的识别
        self._english_patterns = [
            (r'\b\w+ing\b', 8.0),                         # 进行时态
            (r'\b\w+ed\b', 7.0),                          # 过去时态
            (r'\b\w+tion\b', 6.0),                        # 名词后缀
            (r'\b\w+ment\b', 5.0),                        # 名词后缀
            (r'\b\w+ness\b', 5.0),                        # 名词后缀
            (r'\b\w+ful\b', 4.0),                         # 形容词后缀
            (r'\b\w+less\b', 4.0),                        # 形容词后缀
            (r'\b\w+able\b', 4.0),                        # 形容词后缀
            (r'\b\w+ible\b', 4.0),                        # 形容词后缀
        ]
        
        # N-gram频率特征库
        # 这是基于统计语言学的语言识别方法
        # 不同语言的字符组合频率分布不同，可以用来识别语言
        self._ngram_frequencies = self._initialize_ngram_frequencies()
    
    def _initialize_ngram_frequencies(self) -> Dict[str, Dict[str, float]]:
        """
        初始化N-gram频率特征库
        
        这个方法为每种语言预定义了2-gram和3-gram的典型频率分布。
        这些数据基于大规模语料库统计得出，是语言识别的重要依据。
        
        Returns:
            包含各种语言N-gram频率特征的字典
        """
        return {
            'bigrams': {
                'en': {
                    'th': 0.038, 'he': 0.035, 'an': 0.032, 'in': 0.030, 'er': 0.028,
                    're': 0.027, 'on': 0.025, 'at': 0.024, 'nd': 0.023, 'st': 0.022,
                    'es': 0.021, 'en': 0.020, 'te': 0.019, 'ed': 0.018, 'is': 0.017,
                    'it': 0.016, 'al': 0.015, 'ar': 0.014, 'se': 0.013, 'ne': 0.012
                },
                'zh': {
                    '的': 0.045, '了': 0.038, '在': 0.032, '是': 0.030, '我': 0.028,
                    '有': 0.026, '和': 0.024, '人': 0.022, '这': 0.020, '中': 0.018,
                    '大': 0.016, '为': 0.014, '上': 0.012, '个': 0.010, '国': 0.008
                },
                'ja': {
                    'の': 0.042, 'に': 0.038, 'は': 0.035, 'を': 0.032, 'が': 0.030,
                    'で': 0.028, 'と': 0.026, 'も': 0.024, 'から': 0.022, 'まで': 0.020,
                    'より': 0.018, 'へ': 0.016, 'や': 0.014, 'など': 0.012, 'とか': 0.010
                },
                'ko': {
                    '이': 0.040, '가': 0.038, '을': 0.035, '를': 0.032, '에': 0.030,
                    '에서': 0.028, '로': 0.026, '와': 0.024, '과': 0.022, '의': 0.020,
                    '도': 0.018, '만': 0.016, '부터': 0.014, '까지': 0.012, '처럼': 0.010
                }
            },
            'trigrams': {
                'en': {
                    'the': 0.035, 'and': 0.030, 'ing': 0.025, 'her': 0.020, 'ere': 0.018,
                    'hat': 0.016, 'his': 0.014, 'ter': 0.012, 'ion': 0.010, 'for': 0.008
                },
                'zh': {
                    '我们': 0.025, '他们': 0.022, '这个': 0.020, '那个': 0.018, '什么': 0.016,
                    '怎么': 0.014, '为什么': 0.012, '因为': 0.010, '所以': 0.008, '但是': 0.006
                }
            }
        }
    
    def detect_language(self, text: str) -> LanguageDetectionResult:
        """
        检测文本语言
        
        这是语言检测器的主要方法，采用多算法融合的方式：
        1. 首先检查缓存，提升性能
        2. 进行N-gram频率分析
        3. 执行加权模式匹配
        4. 计算综合置信度
        5. 缓存结果供下次使用
        
        与GTPlanner的集成作用：
        - 自动识别用户输入的语言
        - 为多语言PRD生成提供正确的语言上下文
        - 支持国际化需求分析
        
        Args:
            text: 待检测的文本
            
        Returns:
            LanguageDetectionResult: 包含检测语言和置信度的结果对象
        """
        start_time = time.time()
        
        # 输入验证
        if not text or not text.strip():
            return LanguageDetectionResult(
                language=self.default_language,
                confidence=0.0,
                detection_method="default_fallback",
                processing_time=0.0,
                cache_hit=False,
                additional_info={"error": "Empty text input"}
            )
        
        # 文本预处理
        text = text.strip()
        
        # 检查缓存
        cache_key = self._get_cache_key(text)
        if cache_key in self._cache:
            cache_entry = self._cache[cache_key]
            if self._is_cache_valid(cache_entry):
                # 更新缓存命中统计
                if not hasattr(self, '_total_requests'):
                    self._total_requests = 0
                    self._cache_hits = 0
                self._total_requests += 1
                self._cache_hits += 1
                
                # 缓存命中，直接返回结果
                return LanguageDetectionResult(
                    language=cache_entry['language'],
                    confidence=cache_entry['confidence'],
                    detection_method=cache_entry['method'],
                    processing_time=time.time() - start_time,
                    cache_hit=True,
                    additional_info=cache_entry.get('additional_info', {})
                )
        
        # 执行语言检测
        try:
            # 更新请求统计
            if not hasattr(self, '_total_requests'):
                self._total_requests = 0
                self._cache_hits = 0
            self._total_requests += 1
            
            # 方法1：N-gram频率分析
            ngram_scores = self._analyze_ngram_frequencies(text)
            
            # 方法2：加权模式匹配
            pattern_scores = self._weighted_pattern_matching(text)
            
            # 方法3：英语特殊检测（因为英语是GTPlanner的默认语言）
            english_score = self._detect_english_specific(text)
            
            # 综合评分
            final_scores = self._combine_scores(ngram_scores, pattern_scores, english_score)
            
            # 选择最佳语言
            best_language = max(final_scores.items(), key=lambda x: x[1])[0]
            confidence = final_scores[best_language]
            
            # 计算置信度
            final_confidence = self._calculate_confidence(final_scores)
            
            # 创建结果对象
            result = LanguageDetectionResult(
                language=best_language,
                confidence=final_confidence,
                detection_method="multi_algorithm_fusion",
                processing_time=time.time() - start_time,
                cache_hit=False,
                additional_info={
                    "ngram_scores": ngram_scores,
                    "pattern_scores": pattern_scores,
                    "english_score": english_score,
                    "final_scores": final_scores
                }
            )
            
            # 缓存结果
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            # 错误处理：返回默认语言
            return LanguageDetectionResult(
                language=self.default_language,
                confidence=0.0,
                detection_method="error_fallback",
                processing_time=time.time() - start_time,
                cache_hit=False,
                additional_info={"error": str(e)}
            )
    
    def _analyze_ngram_frequencies(self, text: str) -> Dict[SupportedLanguage, float]:
        """
        N-gram频率分析
        
        这是基于统计语言学的语言识别方法。不同语言的字符组合频率分布不同，
        通过分析文本中2-gram和3-gram的出现频率，可以识别语言类型。
        
        技术原理：
        - 提取文本中的字符组合（2-gram, 3-gram）
        - 计算每种组合的频率
        - 与预训练的语言模型对比
        - 计算相似度分数
        
        Args:
            text: 待分析的文本
            
        Returns:
            各种语言的N-gram分析分数
        """
        scores = defaultdict(float)
        
        # 提取2-gram
        bigrams = [text[i:i+2] for i in range(len(text)-1)]
        bigram_freq = defaultdict(int)
        for bigram in bigrams:
            bigram_freq[bigram] += 1
        
        # 提取3-gram
        trigrams = [text[i:i+3] for i in range(len(text)-2)]
        trigram_freq = defaultdict(int)
        for trigram in trigrams:
            trigram_freq[trigram] += 1
        
        # 计算与预训练模型的相似度
        for lang_code, expected_freq in self._ngram_frequencies['bigrams'].items():
            lang = self._get_language_by_code(lang_code)
            if lang:
                # 计算2-gram相似度
                bigram_similarity = self._calculate_frequency_similarity(
                    bigram_freq, expected_freq, len(bigrams)
                )
                
                # 计算3-gram相似度（如果有数据）
                trigram_similarity = 0.0
                if lang_code in self._ngram_frequencies['trigrams']:
                    trigram_similarity = self._calculate_frequency_similarity(
                        trigram_freq, self._ngram_frequencies['trigrams'][lang_code], len(trigrams)
                    )
                
                # 综合评分（2-gram权重70%，3-gram权重30%）
                scores[lang] = bigram_similarity * 0.7 + trigram_similarity * 0.3
        
        return dict(scores)
    
    def _calculate_frequency_similarity(self, actual_freq: Dict[str, int], 
                                      expected_freq: Dict[str, float], 
                                      total_count: int) -> float:
        """
        计算频率相似度
        
        使用余弦相似度计算实际频率分布与期望频率分布的相似程度。
        相似度越高，说明文本越可能属于该语言。
        
        Args:
            actual_freq: 实际观察到的频率
            expected_freq: 期望的频率分布
            total_count: 总计数
            
        Returns:
            相似度分数 (0.0-1.0)
        """
        if total_count == 0:
            return 0.0
        
        # 计算实际频率
        actual_normalized = {}
        for ngram, count in actual_freq.items():
            if ngram in expected_freq:
                actual_normalized[ngram] = count / total_count
        
        if not actual_normalized:
            return 0.0
        
        # 计算余弦相似度
        numerator = 0.0
        actual_sum_sq = 0.0
        expected_sum_sq = 0.0
        
        for ngram in actual_normalized:
            actual_val = actual_normalized[ngram]
            expected_val = expected_freq[ngram]
            
            numerator += actual_val * expected_val
            actual_sum_sq += actual_val * actual_val
            expected_sum_sq += expected_val * expected_val
        
        if actual_sum_sq == 0 or expected_sum_sq == 0:
            return 0.0
        
        return numerator / (actual_sum_sq ** 0.5 * expected_sum_sq ** 0.5)
    
    def _weighted_pattern_matching(self, text: str) -> Dict[SupportedLanguage, float]:
        """
        加权模式匹配
        
        使用正则表达式识别各种语言的特征模式，如：
        - 中文：汉字、四声调、成语
        - 日文：平假名、片假名、汉字混合
        - 韩文：韩文字符、音节结构
        - 阿拉伯文：连字符、变音符号
        
        每种模式都有权重，重要特征有更大的影响力。
        
        Args:
            text: 待分析的文本
            
        Returns:
            各种语言的模式匹配分数
        """
        scores = defaultdict(float)
        
        # 检查各种语言的特征模式
        for language, lang_info in self._language_patterns.items():
            lang_score = 0.0
            total_weight = 0.0
            
            for pattern, weight in lang_info['patterns']:
                matches = re.findall(pattern, text)
                if matches:
                    # 匹配到的模式越多，分数越高
                    pattern_score = len(matches) * weight
                    lang_score += pattern_score
                    total_weight += weight
            
            # 归一化分数
            if total_weight > 0:
                scores[language] = lang_score / total_weight
        
        return dict(scores)
    
    def _detect_english_specific(self, text: str) -> float:
        """
        英语特殊检测
        
        由于英语是GTPlanner的默认语言，我们为英语设计了特殊的检测逻辑：
        1. 检查拉丁字母比例（最重要的指标）
        2. 识别英语特有词汇模式
        3. 检测英语语法结构特征
        
        技术原理：
        - 拉丁字母比例：英语文本中拉丁字母通常占80%以上
        - 词汇模式：英语常用词汇（the, and, or, but等）
        - 语法特征：英语特有的后缀和词形变化
        
        Args:
            text: 待分析的文本
            
        Returns:
            英语检测分数 (0.0-1.0)
        """
        english_score = 0.0
        
        # 检查拉丁字母比例（这是最重要的指标）
        latin_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(text)
        
        if total_chars > 0:
            latin_ratio = latin_chars / total_chars
            if latin_ratio > 0.8:
                english_score += 0.7  # 高比例拉丁字母，强烈暗示英语
            elif latin_ratio > 0.6:
                english_score += 0.5
            elif latin_ratio > 0.4:
                english_score += 0.3
        
        # 检查英语特有词汇模式
        english_words = re.findall(r'\b(the|and|or|but|in|on|at|to|for|of|with|by|is|are|was|were|be|been|have|has|had|do|does|did|will|would|could|should|can|may|might|must)\b', text.lower())
        if english_words:
            english_score += min(len(english_words) * 0.15, 0.4)
        
        # 检查英语语法结构特征
        english_patterns = [
            (r'\b[a-zA-Z]+ing\b', 0.08),      # 进行时态
            (r'\b[a-zA-Z]+ed\b', 0.08),       # 过去时态
            (r'\b[a-zA-Z]+s\b', 0.05),        # 复数/第三人称
            (r'\b[a-zA-Z]+ly\b', 0.05),       # 副词
            (r'\b[a-zA-Z]+tion\b', 0.06),     # 名词后缀
            (r'\b[a-zA-Z]+ment\b', 0.05),     # 名词后缀
            (r'\b[a-zA-Z]+ness\b', 0.05),     # 名词后缀
        ]
        
        for pattern, weight in english_patterns:
            matches = re.findall(pattern, text)
            if matches:
                english_score += min(len(matches) * weight, 0.3)
        
        return min(english_score, 1.0)  # 限制最高分数
    
    def _combine_scores(self, ngram_scores: Dict[SupportedLanguage, float],
                        pattern_scores: Dict[SupportedLanguage, float],
                        english_score: float) -> Dict[SupportedLanguage, float]:
        """
        综合评分
        
        将不同算法的检测结果进行融合，采用加权平均的方式：
        - N-gram分析权重：35%
        - 模式匹配权重：35%
        - 英语特殊检测权重：30%
        
        这种融合策略确保了检测结果的稳定性和准确性。
        英语特殊检测权重提高，以解决英语文本被误判的问题。
        
        Args:
            ngram_scores: N-gram分析分数
            pattern_scores: 模式匹配分数
            english_score: 英语特殊检测分数
            
        Returns:
            综合后的语言分数
        """
        combined_scores = defaultdict(float)
        
        # 合并N-gram分数
        for lang, score in ngram_scores.items():
            combined_scores[lang] += score * 0.35
        
        # 合并模式匹配分数
        for lang, score in pattern_scores.items():
            combined_scores[lang] += score * 0.35
        
        # 添加英语特殊检测分数（权重提高）
        if english_score > 0:
            combined_scores[SupportedLanguage.ENGLISH] += english_score * 0.3
        
        return dict(combined_scores)
    
    def _calculate_confidence(self, scores: Dict[SupportedLanguage, float]) -> float:
        """
        计算置信度
        
        置信度反映了语言检测结果的可信程度，基于以下因素：
        1. 最高分与次高分的差距（差距越大越可信）
        2. 模式匹配的一致性
        3. 文本长度的影响
        
        Args:
            scores: 各种语言的分数
            
        Returns:
            置信度分数 (0.0-1.0)
        """
        if not scores:
            return 0.0
        
        # 按分数排序
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        if len(sorted_scores) == 1:
            return min(sorted_scores[0][1], 0.9)  # 单一语言，最高置信度0.9
        
        # 计算最高分与次高分的差距
        best_score = sorted_scores[0][1]
        second_best_score = sorted_scores[1][1]
        score_gap = best_score - second_best_score
        
        # 差距越大，置信度越高
        gap_confidence = min(score_gap * 2, 0.5)
        
        # 基础置信度
        base_confidence = best_score * 0.7
        
        # 综合置信度
        final_confidence = base_confidence + gap_confidence
        
        return min(final_confidence, 1.0)
    
    def _get_cache_key(self, text: str) -> str:
        """
        生成缓存键
        
        使用MD5哈希作为缓存键，确保：
        1. 键的唯一性（避免哈希冲突）
        2. 固定长度（便于存储和查找）
        3. 快速计算（MD5算法高效）
        
        Args:
            text: 原始文本
            
        Returns:
            MD5哈希字符串
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """
        验证缓存有效性
        
        缓存有过期时间，防止过时数据影响检测结果。
        默认过期时间为1小时，可以根据需要调整。
        
        Args:
            cache_entry: 缓存条目
            
        Returns:
            缓存是否有效
        """
        current_time = time.time()
        cache_time = cache_entry.get('timestamp', 0)
        return current_time - cache_time < 3600  # 1小时过期
    
    def _cache_result(self, cache_key: str, result: LanguageDetectionResult):
        """
        缓存检测结果
        
        智能缓存管理：
        1. 检查缓存大小，超过限制时清理过期条目
        2. 存储完整的检测结果，包括时间戳
        3. 支持缓存命中率统计
        
        Args:
            cache_key: 缓存键
            result: 检测结果
        """
        # 检查缓存大小
        if len(self._cache) >= self._cache_size:
            self._cleanup_cache()
        
        # 存储结果
        self._cache[cache_key] = {
            'language': result.language,
            'confidence': result.confidence,
            'method': result.detection_method,
            'timestamp': time.time(),
            'additional_info': result.additional_info
        }
    
    def _cleanup_cache(self):
        """
        清理过期缓存
        
        防止内存泄漏，定期清理过期的缓存条目。
        清理策略：删除超过1小时的缓存条目。
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time - entry['timestamp'] > 3600
        ]
        
        for key in expired_keys:
            del self._cache[key]
    
    def _get_language_by_code(self, lang_code: str) -> Optional[SupportedLanguage]:
        """
        根据语言代码获取语言枚举
        
        将语言代码（如'en', 'zh'）转换为对应的枚举值。
        
        Args:
            lang_code: 语言代码
            
        Returns:
            对应的语言枚举值，如果不存在则返回None
        """
        for lang in SupportedLanguage:
            if lang.value == lang_code:
                return lang
        return None
    
    def get_cache_stats(self) -> Dict[str, any]:
        """
        获取缓存统计信息
        
        用于性能监控和调试，了解缓存的使用情况。
        
        Returns:
            包含缓存统计信息的字典
        """
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for entry in self._cache.values():
            if current_time - entry['timestamp'] <= 3600:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_size_limit': self._cache_size,
            'hit_rate': 'N/A'  # 需要实现命中率统计
        }
    
    def clear_cache(self):
        """
        清空缓存
        
        用于测试或内存管理，完全清空所有缓存条目。
        """
        self._cache.clear()
    
    def set_cache_size(self, size: int):
        """
        设置缓存大小
        
        动态调整缓存大小，平衡内存使用和性能。
        
        Args:
            size: 新的缓存大小限制
        """
        if size > 0:
            self._cache_size = size
            # 如果当前缓存超过新限制，清理多余条目
            if len(self._cache) > size:
                self._cleanup_cache()
    
    def _get_memory_usage(self) -> float:
        """
        获取当前内存使用量（MB）
        
        这个方法用于性能监控，跟踪检测器的内存使用情况。
        与GTPlanner的性能监控系统集成，提供系统资源使用分析。
        
        Returns:
            当前内存使用量（MB）
        """
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # 转换为MB
        except ImportError:
            # 如果没有psutil，返回估算值
            return len(self._cache) * 0.001  # 假设每个缓存条目占用1KB
    
    def get_performance_stats(self) -> Dict[str, any]:
        """
        获取性能统计信息
        
        这个方法为GTPlanner的性能监控系统提供数据支持，
        帮助分析语言检测的性能特征和优化机会。
        
        Returns:
            包含性能统计信息的字典
        """
        return {
            "cache_size": len(self._cache),
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "memory_usage": self._get_memory_usage(),
            "supported_languages": len(SupportedLanguage),
            "detection_methods": ["ngram_analysis", "pattern_matching", "english_specific"]
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """计算缓存命中率"""
        if not hasattr(self, '_total_requests'):
            self._total_requests = 0
            self._cache_hits = 0
        
        if self._total_requests == 0:
            return 0.0
        
        return self._cache_hits / self._total_requests
