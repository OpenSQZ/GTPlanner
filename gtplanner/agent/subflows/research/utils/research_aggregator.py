"""
研究结果聚合器

负责将多个关键词的研究报告聚合成最终的研究总结
"""


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
        unique_insights = list(set(all_insights))[:10]  # 最多10个洞察
        unique_tech_details = list(set(all_technical_details))[:8]  # 最多8个技术细节
        unique_recommendations = list(set(all_recommendations))[:6]  # 最多6个建议
        
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
