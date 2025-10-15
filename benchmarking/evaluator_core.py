import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable
import logging
from .metrics import PlanningQualityMetrics
from .test_case import TestCase
from .file_utils import (
    load_test_cases, save_test_case, save_results,
    find_latest_results, save_comparison, save_report
)

# 日志配置（仅负责核心评测逻辑日志）
logger = logging.getLogger("GTPlannerEvaluator.Core")


class BenchmarkEvaluator:
    """基准测试评估器（仅负责核心逻辑：用例执行、指标计算、版本对比）"""

    def __init__(self, test_cases_dir: str = "benchmark/test_cases",
                 results_dir: str = "benchmark/results"):
        # 初始化目录（确保目录存在）
        self.test_cases_dir = Path(test_cases_dir)
        self.results_dir = Path(results_dir)
        self.test_cases_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # 依赖注入：指标计算器和文件工具
        self.metrics = PlanningQualityMetrics()

    def save_test_case(self, test_case: TestCase) -> None:
        """保存评测用例（调用文件工具）"""
        save_test_case(test_case, self.test_cases_dir)

    def load_test_cases(self) -> List[TestCase]:
        """加载评测用例（调用文件工具）"""
        return load_test_cases(self.test_cases_dir)

    def run_test_case(self, test_case: TestCase, planner_func: Callable, version: str) -> Dict:
        """运行单个测试用例：生成文档→计算指标→返回结果"""
        start_time = time.time()
        try:
            # 1. 调用GTPlanner生成规划文档
            generated_plan = planner_func(test_case.requirements)
            execution_time = time.time() - start_time

            # 2. 计算各项质量指标
            metrics = {
                "completeness": self.metrics.calculate_completeness(generated_plan, test_case.requirements),
                "relevance": self.metrics.calculate_relevance(generated_plan, test_case.requirements),
                "structuredness": self.metrics.calculate_structuredness(generated_plan),
                "feature_coverage": {
                    feat: feat.lower() in generated_plan.lower()
                    for feat in test_case.expected_features
                },
                "avg_score": (
                    self.metrics.calculate_completeness(generated_plan, test_case.requirements) +
                    self.metrics.calculate_relevance(generated_plan, test_case.requirements) +
                    self.metrics.calculate_structuredness(generated_plan)
                ) / 3
            }

            # 3. 组装结果
            result = {
                "test_case_id": test_case.case_id,
                "version": version,
                "timestamp": datetime.now().isoformat(),
                "execution_time": execution_time,
                "metrics": metrics,
                "generated_plan": generated_plan,
                "requirements": test_case.requirements
            }
            logger.info(f"Completed case: {test_case.case_id} (version: {version})")
            return result

        except Exception as e:
            logger.error(f"Failed case: {test_case.case_id} (error: {str(e)})")
            return {
                "test_case_id": test_case.case_id,
                "version": version,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    def run_benchmark(self, planner_func: Callable, version: str, test_cases: Optional[List[TestCase]] = None) -> List[Dict]:
        """批量运行测试用例：加载用例→逐个执行→保存结果"""
        # 加载用例（未提供则从目录加载）
        test_cases = test_cases or self.load_test_cases()
        if not test_cases:
            logger.warning("No test cases to run")
            return []

        # 逐个执行用例
        results = [self.run_test_case(case, planner_func, version) for case in test_cases]

        # 保存结果
        save_results(results, version, self.results_dir)
        return results

    def compare_versions(self, old_version: str, new_version: str) -> Dict:
        """对比两个版本的测试结果：计算改进幅度→生成对比数据"""
        # 1. 加载两个版本的最新结果
        old_results = find_latest_results(old_version, self.results_dir)
        new_results = find_latest_results(new_version, self.results_dir)
        if not old_results or not new_results:
            logger.error("Comparison failed: missing results for one or both versions")
            return {}

        # 2. 按用例ID建立映射（方便对比）
        old_result_map = {r["test_case_id"]: r for r in old_results if "error" not in r}
        comparison = {
            "summary": {
                "old_version": old_version,
                "new_version": new_version,
                "overall_improvement": 0.0,
                "cases_improved": 0,
                "cases_regressed": 0,
                "cases_unchanged": 0,
                "total_cases": 0
            },
            "details": {}
        }

        # 3. 逐个用例对比
        for new_r in new_results:
            case_id = new_r["test_case_id"]
            old_r = old_result_map.get(case_id)
            if not old_r or "error" in new_r:
                continue

            # 计算分数变化
            old_score = old_r["metrics"]["avg_score"]
            new_score = new_r["metrics"]["avg_score"]
            score_diff = new_score - old_score

            # 记录详细对比
            comparison["details"][case_id] = {
                "old_score": old_score,
                "new_score": new_score,
                "score_diff": score_diff,
                "improvement": score_diff / old_score if old_score > 0 else 0,
                "metrics_change": {
                    "completeness": new_r["metrics"]["completeness"] - old_r["metrics"]["completeness"],
                    "relevance": new_r["metrics"]["relevance"] - old_r["metrics"]["relevance"],
                    "structuredness": new_r["metrics"]["structuredness"] - old_r["metrics"]["structuredness"]
                }
            }

            # 更新汇总统计（0.01为显著变化阈值）
            comparison["summary"]["total_cases"] += 1
            if score_diff > 0.01:
                comparison["summary"]["cases_improved"] += 1
            elif score_diff < -0.01:
                comparison["summary"]["cases_regressed"] += 1
            else:
                comparison["summary"]["cases_unchanged"] += 1
            comparison["summary"]["overall_improvement"] += score_diff

        # 4. 计算平均改进幅度
        if comparison["summary"]["total_cases"] > 0:
            comparison["summary"]["overall_improvement"] /= comparison["summary"]["total_cases"]

        # 5. 保存对比结果
        save_comparison(comparison, old_version, new_version, self.results_dir)
        return comparison

    def generate_evaluation_report(self, comparison: Dict) -> str:
        """生成Markdown评估报告：基于对比结果组装文档"""
        if not comparison.get("details"):
            logger.warning("No comparison data to generate report")
            return ""

        # 1. 组装报告内容
        old_version = comparison["summary"]["old_version"]
        new_version = comparison["summary"]["new_version"]
        report = [
            "# GTPlanner 评估报告",
            f"比较版本: {old_version} vs {new_version}",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 总体摘要",
            f"- 测试用例总数: {comparison['summary']['total_cases']}",
            f"- 有改善的用例: {comparison['summary']['cases_improved']}",
            f"- 有退步的用例: {comparison['summary']['cases_regressed']}",
            f"- 无显著变化的用例: {comparison['summary']['cases_unchanged']}",
            f"- 总体平均改进: {comparison['summary']['overall_improvement']:.2%}",
            "",
            "## 详细对比"
        ]

        # 2. 补充每个用例的详细对比
        for case_id, details in comparison["details"].items():
            report.extend([
                f"\n### 测试用例 {case_id}",
                f"- 旧版本得分: {details['old_score']:.4f}",
                f"- 新版本得分: {details['new_score']:.4f}",
                f"- 变化: {details['score_diff']:.4f} ({details['improvement']:.2%})",
                f"  - 完整性变化: {details['metrics_change']['completeness']:.4f}",
                f"  - 相关性变化: {details['metrics_change']['relevance']:.4f}",
                f"  - 结构化变化: {details['metrics_change']['structuredness']:.4f}"
            ])

        # 3. 保存报告并返回内容
        report_content = "\n".join(report)
        save_report(report_content, old_version, new_version, self.results_dir)
        return report_content