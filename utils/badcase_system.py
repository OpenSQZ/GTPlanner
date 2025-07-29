"""
BadCase记录系统

提供BadCase的记录、存储和分析功能。
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BadCase:
    """BadCase数据类"""
    input_prompt: str
    output_result: str
    feedback_label: str
    user_id: str
    timestamp: str
    
    def __post_init__(self):
        """验证数据完整性"""
        if not self.input_prompt.strip():
            raise ValueError("input_prompt cannot be empty")
        if not self.output_result.strip():
            raise ValueError("output_result cannot be empty")
        if not self.feedback_label.strip():
            raise ValueError("feedback_label cannot be empty")
        if not self.user_id.strip():
            raise ValueError("user_id cannot be empty")
        if not self.timestamp.strip():
            raise ValueError("timestamp cannot be empty")


class JSONStorageEngine:
    """JSON存储引擎，负责BadCase的持久化存储"""
    
    def __init__(self, file_path: str = "badcases.json"):
        """
        初始化存储引擎
        
        Args:
            file_path: JSON文件路径
        """
        self.file_path = Path(file_path)
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """确保存储文件存在"""
        if not self.file_path.exists():
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._save_data([])
            logger.info(f"Created new storage file: {self.file_path}")
    
    def _load_data(self) -> List[Dict[str, Any]]:
        """加载JSON数据"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Error loading data: {e}, creating new file")
            return []
    
    def _save_data(self, data: List[Dict[str, Any]]) -> None:
        """保存数据到JSON文件"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            raise
    
    def save_badcase(self, badcase: BadCase) -> bool:
        """
        保存BadCase
        
        Args:
            badcase: BadCase对象
            
        Returns:
            bool: 保存是否成功
        """
        try:
            data = self._load_data()
            data.append(asdict(badcase))
            self._save_data(data)
            logger.info(f"Saved BadCase for user: {badcase.user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving BadCase: {e}")
            return False
    
    def get_all_badcases(self) -> List[BadCase]:
        """
        获取所有BadCase
        
        Returns:
            List[BadCase]: BadCase列表
        """
        try:
            data = self._load_data()
            return [BadCase(**item) for item in data]
        except Exception as e:
            logger.error(f"Error loading BadCases: {e}")
            return []
    
    def get_badcases_by_user(self, user_id: str) -> List[BadCase]:
        """
        根据用户ID获取BadCase
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[BadCase]: 该用户的BadCase列表
        """
        all_badcases = self.get_all_badcases()
        return [bc for bc in all_badcases if bc.user_id == user_id]
    
    def get_badcases_by_label(self, feedback_label: str) -> List[BadCase]:
        """
        根据反馈标签获取BadCase
        
        Args:
            feedback_label: 反馈标签
            
        Returns:
            List[BadCase]: 该标签的BadCase列表
        """
        all_badcases = self.get_all_badcases()
        return [bc for bc in all_badcases if bc.feedback_label == feedback_label]


class BadCaseRecorder:
    """BadCase记录器，负责记录新的BadCase"""
    
    def __init__(self, storage_engine: JSONStorageEngine):
        """
        初始化记录器
        
        Args:
            storage_engine: 存储引擎实例
        """
        self.storage_engine = storage_engine
    
    def record_badcase(
        self,
        input_prompt: str,
        output_result: str,
        feedback_label: str,
        user_id: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        记录新的BadCase
        
        Args:
            input_prompt: 输入提示
            output_result: 输出结果
            feedback_label: 反馈标签
            user_id: 用户ID
            timestamp: 时间戳，如果为None则使用当前时间
            
        Returns:
            bool: 记录是否成功
        """
        try:
            if timestamp is None:
                timestamp = datetime.now().isoformat()
            
            badcase = BadCase(
                input_prompt=input_prompt,
                output_result=output_result,
                feedback_label=feedback_label,
                user_id=user_id,
                timestamp=timestamp
            )
            
            return self.storage_engine.save_badcase(badcase)
        except Exception as e:
            logger.error(f"Error recording BadCase: {e}")
            return False
    
    def record_badcase_object(self, badcase: BadCase) -> bool:
        """
        记录BadCase对象
        
        Args:
            badcase: BadCase对象
            
        Returns:
            bool: 记录是否成功
        """
        return self.storage_engine.save_badcase(badcase)


class BadCaseAnalyzer:
    """BadCase分析器，提供统计功能"""
    
    def __init__(self, storage_engine: JSONStorageEngine):
        """
        初始化分析器
        
        Args:
            storage_engine: 存储引擎实例
        """
        self.storage_engine = storage_engine
    
    def get_label_distribution(self) -> Dict[str, int]:
        """
        获取标签分布统计
        
        Returns:
            Dict[str, int]: 标签及其出现次数
        """
        badcases = self.storage_engine.get_all_badcases()
        distribution = {}
        
        for badcase in badcases:
            label = badcase.feedback_label
            distribution[label] = distribution.get(label, 0) + 1
        
        return distribution
    
    def get_user_statistics(self) -> Dict[str, int]:
        """
        获取用户统计信息
        
        Returns:
            Dict[str, int]: 用户及其BadCase数量
        """
        badcases = self.storage_engine.get_all_badcases()
        user_stats = {}
        
        for badcase in badcases:
            user_id = badcase.user_id
            user_stats[user_id] = user_stats.get(user_id, 0) + 1
        
        return user_stats
    
    def get_total_count(self) -> int:
        """
        获取总BadCase数量
        
        Returns:
            int: 总数量
        """
        return len(self.storage_engine.get_all_badcases())
    
    def get_badcases_by_date_range(
        self,
        start_date: str,
        end_date: str
    ) -> List[BadCase]:
        """
        根据日期范围获取BadCase
        
        Args:
            start_date: 开始日期 (ISO格式)
            end_date: 结束日期 (ISO格式)
            
        Returns:
            List[BadCase]: 日期范围内的BadCase列表
        """
        badcases = self.storage_engine.get_all_badcases()
        filtered_badcases = []
        
        for badcase in badcases:
            try:
                case_date = datetime.fromisoformat(badcase.timestamp)
                start = datetime.fromisoformat(start_date)
                end = datetime.fromisoformat(end_date)
                
                if start <= case_date <= end:
                    filtered_badcases.append(badcase)
            except ValueError as e:
                logger.warning(f"Invalid date format: {e}")
                continue
        
        return filtered_badcases
    
    def get_most_common_labels(self, top_n: int = 5) -> List[tuple]:
        """
        获取最常见的标签
        
        Args:
            top_n: 返回前N个标签
            
        Returns:
            List[tuple]: (标签, 数量) 元组列表，按数量降序排列
        """
        distribution = self.get_label_distribution()
        sorted_labels = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
        return sorted_labels[:top_n] 