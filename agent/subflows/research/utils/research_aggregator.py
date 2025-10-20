"""
研究结果聚合器

负责将多个关键词的研究报告聚合成最终的研究总结
"""

import re
from difflib import SequenceMatcher
from typing import List, Union, Dict, Any, Sequence


class ResearchAggregator:
    """研究结果聚合器"""
    
    @staticmethod
    def aggregate_research_results(research_report):
        """3. 结果聚合"""
        if not research_report:
            return {
                "overall_summary": "未找到有效的研究结果",
                "key_findings": [],
                "technical_insights": [],
                "recommendations": [],
                "coverage_analysis": {
                    "total_keywords": 0,
                    "successful_keywords": 0,
                    "average_relevance": 0.0
                }
            }
        
        # 聚合所有关键洞察
        all_insights = []
        all_technical_details = []
        all_recommendations = []
        relevance_scores = []
        
        for report in research_report:
            analysis = report.get("analysis", {})
            
            # 收集洞察
            insights = analysis.get("key_insights", [])
            all_insights.extend(insights)
            
            # 收集技术细节
            tech_details = analysis.get("technical_details", [])
            all_technical_details.extend(tech_details)
            
            # 收集建议
            recommendations = analysis.get("recommendations", [])
            all_recommendations.extend(recommendations)
            
            # 收集相关性分数
            relevance = analysis.get("relevance_score", 0.0)
            relevance_scores.append(relevance)
        
        # 去重和排序
        # 去重和排序（基于内容相似度的智能去重）
        unique_insights = ResearchAggregator._deduplicate_and_rank(all_insights, max_items=10)
        unique_tech_details = ResearchAggregator._deduplicate_and_rank(all_technical_details, max_items=8)
        unique_recommendations = ResearchAggregator._deduplicate_and_rank(all_recommendations, max_items=6)
        
        # 计算平均相关性
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0
        
        return {
            "overall_summary": f"完成了{len(research_report)}个关键词的研究分析，平均相关性: {avg_relevance:.2f}",
            "key_findings": unique_insights,
            "technical_insights": unique_tech_details,
            "recommendations": unique_recommendations,
            "coverage_analysis": {
                "total_keywords": len(research_report),
                "successful_keywords": len([r for r in research_report if r.get("analysis", {}).get("relevance_score", 0) > 0.5]),
                "average_relevance": avg_relevance,
                "high_quality_results": len([r for r in research_report if r.get("analysis", {}).get("relevance_score", 0) > 0.7])
            }
        }
    
    @staticmethod
    def _deduplicate_and_rank(items: Sequence[Union[str, Dict[str, Any]]], max_items: int = 10) -> List[Union[str, Dict[str, Any]]]:
        """
        基于内容相似度的智能去重和排序
        
        Args:
            items: 需要去重的项目列表（可以是字符串或字典）
            max_items: 返回的最大项目数
            
        Returns:
            去重并排序后的项目列表
        """
        if not items:
            return []
        
        # 标准化处理函数
        def normalize_text(text: str) -> str:
            """标准化文本用于相似度比较"""
            if not text:
                return ""
            # 移除多余空白和标点
            text = re.sub(r'\s+', ' ', text.strip())
            text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)  # 保留中英文和数字，标点替换为空格
            return text.lower()
        
        def extract_text(item: Union[str, Dict[str, Any]]) -> str:
            """从项目中提取文本内容"""
            if isinstance(item, str):
                return item
            elif isinstance(item, dict):
                # 优先级：content > description > title > 其他字符串值
                text_parts = []
                priority_keys = ['content', 'description', 'title', 'text', 'summary']
                
                # 先收集优先级高的字段
                for key in priority_keys:
                    if key in item and isinstance(item[key], str) and item[key].strip():
                        text_parts.append(item[key])
                
                # 如果没有找到优先字段，收集所有字符串值
                if not text_parts:
                    for value in item.values():
                        if isinstance(value, str) and value.strip():
                            text_parts.append(value)
                
                return ' '.join(text_parts) if text_parts else ""
            return str(item)
        
        def extract_keywords(text: str) -> set:
            """从文本中提取关键词（改进中文支持）"""
            normalized = normalize_text(text)
            
            # 英文单词分割
            english_words = set(re.findall(r'[a-zA-Z]+', normalized))
            
            # 中文关键词提取（基于常见词汇模式）
            chinese_keywords = set()
            
            # 提取中文2-4字词组
            chinese_chars = re.findall(r'[\u4e00-\u9fff]+', normalized)
            for chars in chinese_chars:
                if len(chars) >= 2:
                    # 添加2字词组
                    for i in range(len(chars) - 1):
                        chinese_keywords.add(chars[i:i+2])
                    # 添加3字词组
                    for i in range(len(chars) - 2):
                        chinese_keywords.add(chars[i:i+3])
                    # 添加4字词组
                    for i in range(len(chars) - 3):
                        chinese_keywords.add(chars[i:i+4])
                    # 添加整个词组（如果合理长度）
                    if 2 <= len(chars) <= 8:
                        chinese_keywords.add(chars)
            
            # 数字
            numbers = set(re.findall(r'\d+', normalized))
            
            return english_words | chinese_keywords | numbers
        
        def calculate_similarity(text1: str, text2: str) -> float:
            """计算两个文本的相似度（改进版）"""
            norm_text1 = normalize_text(text1)
            norm_text2 = normalize_text(text2)
            
            if not norm_text1 or not norm_text2:
                return 0.0
            
            # 如果文本完全相同，返回1.0
            if norm_text1 == norm_text2:
                return 1.0
                
            # 使用 SequenceMatcher 计算序列相似度
            sequence_similarity = SequenceMatcher(None, norm_text1, norm_text2).ratio()
            
            # 关键词级别的相似度检查（改进版）
            keywords1 = extract_keywords(text1)
            keywords2 = extract_keywords(text2)
            
            if not keywords1 or not keywords2:
                return sequence_similarity
            
            # Jaccard 相似度（交集/并集）
            intersection = len(keywords1 & keywords2)
            union = len(keywords1 | keywords2)
            jaccard_similarity = intersection / union if union > 0 else 0.0
            
            # 包含关系检查（短文本的关键词是否完全包含在长文本中）
            if len(keywords1) < len(keywords2):
                containment = len(keywords1 & keywords2) / len(keywords1) if keywords1 else 0.0
            else:
                containment = len(keywords1 & keywords2) / len(keywords2) if keywords2 else 0.0
            
            # 综合相似度计算：序列相似度30% + Jaccard相似度50% + 包含关系20%
            combined_similarity = 0.3 * sequence_similarity + 0.5 * jaccard_similarity + 0.2 * containment
            
            return min(combined_similarity, 1.0)
        
        def calculate_quality_score(item: Union[str, Dict[str, Any]]) -> float:
            """计算项目的质量分数（改进版）"""
            text = extract_text(item)
            
            if not text or not text.strip():
                return 0.0
            
            # 基础分数
            score = 0.3
            
            # 长度评分（更细致的长度评估）
            text_len = len(text.strip())
            if text_len < 10:  # 太短的文本降分
                score += 0.0
            elif 10 <= text_len < 30:  # 短文本
                score += 0.1
            elif 30 <= text_len < 100:  # 中等长度
                score += 0.3
            elif 100 <= text_len < 300:  # 理想长度
                score += 0.4
            elif 300 <= text_len < 500:  # 较长但可接受
                score += 0.3
            else:  # 过长可能含有冗余信息
                score += 0.2
            
            # 信息密度评分（扩展关键词库）
            technical_keywords = [
                '技术', '方法', '实现', '建议', '优化', '性能', '安全', '架构', '算法', '策略',
                '解决方案', '最佳实践', '框架', '系统', '平台', '工具', '流程', '标准',
                'technology', 'method', 'implementation', 'recommendation', 'optimization',
                'performance', 'security', 'architecture', 'algorithm', 'strategy',
                'solution', 'practice', 'framework', 'system', 'platform', 'tool',
                'process', 'standard', 'approach', 'technique'
            ]
            
            normalized_text = normalize_text(text)
            keyword_matches = sum(1 for keyword in technical_keywords 
                                if keyword.lower() in normalized_text)
            
            # 关键词密度奖励（最多0.3分）
            keyword_density = min(keyword_matches / 10.0, 0.3)
            score += keyword_density
            
            # 结构化信息奖励
            if isinstance(item, dict):
                score += 0.1
                
                # 优先级字段奖励
                priority_fields = ['priority', 'importance', 'weight', 'score', 'relevance']
                if any(field in item for field in priority_fields):
                    score += 0.1
                    
                # 如果有明确的优先级标记
                priority_value = item.get('priority', '').lower()
                if priority_value in ['high', 'critical', 'important', '高', '重要', '关键']:
                    score += 0.1
                elif priority_value in ['medium', 'normal', '中', '一般']:
                    score += 0.05
            
            # 信息完整性评分（是否包含具体的技术细节）
            detail_indicators = ['包括', '例如', '具体', '详细', '步骤', '方式', '如何',
                               'include', 'such as', 'specific', 'detail', 'step', 'how']
            if any(indicator in normalized_text for indicator in detail_indicators):
                score += 0.1
            
            return min(score, 1.0)
        
        # 改进的去重处理
        unique_items = []
        similarity_threshold = 0.45  # 降低阈值以提高去重效果
        
        # 预处理：按质量分数排序，优先保留高质量项目
        items_with_scores = [(item, calculate_quality_score(item)) for item in items]
        items_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        for item, item_score in items_with_scores:
            item_text = extract_text(item)
            if not item_text.strip():  # 跳过空内容
                continue
                
            is_duplicate = False
            duplicate_index = -1
            max_similarity = 0.0
            
            # 检查是否与已存在项目重复
            for i, existing_item in enumerate(unique_items):
                existing_text = extract_text(existing_item)
                similarity = calculate_similarity(item_text, existing_text)
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    duplicate_index = i
                
                if similarity > similarity_threshold:
                    is_duplicate = True
                    break
            
            if is_duplicate and duplicate_index >= 0:
                # 保留质量更高的项目
                existing_score = calculate_quality_score(unique_items[duplicate_index])
                if item_score > existing_score:
                    unique_items[duplicate_index] = item
            elif not is_duplicate:
                unique_items.append(item)
        
        # 最终排序（按质量分数）
        unique_items.sort(key=lambda x: calculate_quality_score(x), reverse=True)
        
        # 返回前 max_items 个项目
        return unique_items[:max_items]
