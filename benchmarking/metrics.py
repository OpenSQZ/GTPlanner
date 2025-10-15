import difflib
from typing import List


class PlanningQualityMetrics:
    """规划文档质量评估指标（仅负责计算，无其他依赖）"""

    @staticmethod
    def calculate_completeness(generated_content: str, requirements: str) -> float:
        """计算需求覆盖率（0.0-1.0）：生成内容覆盖原始需求点的比例"""
        requirement_points = [p.strip() for p in requirements.split('.') if p.strip()]
        if not requirement_points:
            return 0.0

        covered_count = sum(
            1 for point in requirement_points
            if point.lower() in generated_content.lower()
        )
        return covered_count / len(requirement_points)

    @staticmethod
    def calculate_relevance(generated_content: str, requirements: str) -> float:
        """计算内容相关性（0.0-1.0）：基于文本序列匹配的相似度"""
        return difflib.SequenceMatcher(
            None, generated_content.lower(), requirements.lower()
        ).ratio()

    @staticmethod
    def calculate_structuredness(generated_content: str) -> float:
        """计算文档结构化程度（0.0-1.0）：检测Markdown格式元素占比"""
        structure_elements = ['#', '*', '-', '1.', '2.', '3.', '##', '###', '####', '#####', '######']
        lines = generated_content.split('\n')
        if not lines:
            return 0.0

        structured_lines = sum(
            1 for line in lines
            if any(line.strip().startswith(elem) for elem in structure_elements)
        )
        return structured_lines / len(lines)