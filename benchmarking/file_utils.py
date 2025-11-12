import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging
from .test_case import TestCase

# 日志配置（仅负责文件操作相关日志）
logger = logging.getLogger("GTPlannerEvaluator.FileUtils")


def save_test_case(test_case: TestCase, save_dir: Path) -> None:
    """保存评测用例到JSON文件"""
    filename = f"{test_case.case_id}.json"
    file_path = save_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(test_case.to_dict(), f, ensure_ascii=False, indent=2)
    logger.info(f"Saved test case: {test_case.case_id} (path: {file_path})")


def load_test_cases(load_dir: Path) -> List[TestCase]:
    """从目录加载所有评测用例（仅JSON文件）"""
    test_cases = []
    for filename in os.listdir(load_dir):
        if not filename.endswith(".json"):
            continue

        file_path = load_dir / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
                test_cases.append(TestCase.from_dict(case_data))
            logger.info(f"Loaded test case: {case_data['case_id']} (path: {file_path})")
        except Exception as e:
            logger.error(f"Failed to load {filename}: {str(e)}")
    return test_cases


def save_results(results: List[Dict], version: str, save_dir: Path) -> None:
    """保存测试结果到JSON文件（带版本和时间戳）"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results_{version}_{timestamp}.json"
    file_path = save_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(results)} results: {file_path}")


def save_comparison(comparison: Dict, old_version: str, new_version: str, save_dir: Path) -> None:
    """保存版本对比结果到JSON文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"comparison_{old_version}_vs_{new_version}_{timestamp}.json"
    file_path = save_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved comparison: {file_path}")


def save_report(report_content: str, old_version: str, new_version: str, save_dir: Path) -> None:
    """保存Markdown评估报告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"evaluation_report_{old_version}_vs_{new_version}_{timestamp}.md"
    file_path = save_dir / filename
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    logger.info(f"Generated report: {file_path}")


def find_latest_results(version: str, search_dir: Path) -> Optional[List[Dict]]:
    """查找指定版本的最新测试结果（按文件创建时间排序）"""
    result_files = []
    for filename in os.listdir(search_dir):
        if filename.startswith(f"results_{version}_") and filename.endswith(".json"):
            file_path = search_dir / filename
            create_time = os.path.getctime(file_path)
            result_files.append((file_path, create_time))

    if not result_files:
        logger.warning(f"No results found for version: {version}")
        return None

    # 按创建时间倒序，取最新的文件
    latest_file = sorted(result_files, key=lambda x: x[1], reverse=True)[0][0]
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)