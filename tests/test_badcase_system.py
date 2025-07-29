"""
BadCase记录系统测试用例
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from utils.badcase_system import (
    BadCase,
    JSONStorageEngine,
    BadCaseRecorder,
    BadCaseAnalyzer
)


class TestBadCase:
    """测试BadCase类"""
    
    def test_badcase_creation(self):
        """测试BadCase对象创建"""
        badcase = BadCase(
            input_prompt="测试输入",
            output_result="测试输出",
            feedback_label="错误",
            user_id="user123",
            timestamp="2024-01-01T00:00:00"
        )
        
        assert badcase.input_prompt == "测试输入"
        assert badcase.output_result == "测试输出"
        assert badcase.feedback_label == "错误"
        assert badcase.user_id == "user123"
        assert badcase.timestamp == "2024-01-01T00:00:00"
    
    def test_badcase_validation_empty_input_prompt(self):
        """测试空输入提示的验证"""
        with pytest.raises(ValueError, match="input_prompt cannot be empty"):
            BadCase(
                input_prompt="",
                output_result="测试输出",
                feedback_label="错误",
                user_id="user123",
                timestamp="2024-01-01T00:00:00"
            )
    
    def test_badcase_validation_empty_output_result(self):
        """测试空输出结果的验证"""
        with pytest.raises(ValueError, match="output_result cannot be empty"):
            BadCase(
                input_prompt="测试输入",
                output_result="",
                feedback_label="错误",
                user_id="user123",
                timestamp="2024-01-01T00:00:00"
            )
    
    def test_badcase_validation_empty_feedback_label(self):
        """测试空反馈标签的验证"""
        with pytest.raises(ValueError, match="feedback_label cannot be empty"):
            BadCase(
                input_prompt="测试输入",
                output_result="测试输出",
                feedback_label="",
                user_id="user123",
                timestamp="2024-01-01T00:00:00"
            )
    
    def test_badcase_validation_empty_user_id(self):
        """测试空用户ID的验证"""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            BadCase(
                input_prompt="测试输入",
                output_result="测试输出",
                feedback_label="错误",
                user_id="",
                timestamp="2024-01-01T00:00:00"
            )
    
    def test_badcase_validation_empty_timestamp(self):
        """测试空时间戳的验证"""
        with pytest.raises(ValueError, match="timestamp cannot be empty"):
            BadCase(
                input_prompt="测试输入",
                output_result="测试输出",
                feedback_label="错误",
                user_id="user123",
                timestamp=""
            )


class TestJSONStorageEngine:
    """测试JSON存储引擎"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def storage_engine(self, temp_file):
        """创建存储引擎实例"""
        return JSONStorageEngine(temp_file)
    
    def test_storage_engine_initialization(self, temp_file):
        """测试存储引擎初始化"""
        engine = JSONStorageEngine(temp_file)
        assert engine.file_path == Path(temp_file)
        assert engine.file_path.exists()
    
    def test_save_and_load_badcase(self, storage_engine):
        """测试保存和加载BadCase"""
        badcase = BadCase(
            input_prompt="测试输入",
            output_result="测试输出",
            feedback_label="错误",
            user_id="user123",
            timestamp="2024-01-01T00:00:00"
        )
        
        # 保存BadCase
        success = storage_engine.save_badcase(badcase)
        assert success is True
        
        # 加载所有BadCase
        badcases = storage_engine.get_all_badcases()
        assert len(badcases) == 1
        assert badcases[0].input_prompt == "测试输入"
        assert badcases[0].user_id == "user123"
    
    def test_get_badcases_by_user(self, storage_engine):
        """测试根据用户ID获取BadCase"""
        # 创建多个BadCase
        badcase1 = BadCase(
            input_prompt="用户1输入",
            output_result="用户1输出",
            feedback_label="错误",
            user_id="user1",
            timestamp="2024-01-01T00:00:00"
        )
        
        badcase2 = BadCase(
            input_prompt="用户2输入",
            output_result="用户2输出",
            feedback_label="错误",
            user_id="user2",
            timestamp="2024-01-01T00:00:00"
        )
        
        storage_engine.save_badcase(badcase1)
        storage_engine.save_badcase(badcase2)
        
        # 获取用户1的BadCase
        user1_badcases = storage_engine.get_badcases_by_user("user1")
        assert len(user1_badcases) == 1
        assert user1_badcases[0].user_id == "user1"
    
    def test_get_badcases_by_label(self, storage_engine):
        """测试根据标签获取BadCase"""
        # 创建多个BadCase
        badcase1 = BadCase(
            input_prompt="输入1",
            output_result="输出1",
            feedback_label="错误",
            user_id="user1",
            timestamp="2024-01-01T00:00:00"
        )
        
        badcase2 = BadCase(
            input_prompt="输入2",
            output_result="输出2",
            feedback_label="警告",
            user_id="user2",
            timestamp="2024-01-01T00:00:00"
        )
        
        storage_engine.save_badcase(badcase1)
        storage_engine.save_badcase(badcase2)
        
        # 获取错误标签的BadCase
        error_badcases = storage_engine.get_badcases_by_label("错误")
        assert len(error_badcases) == 1
        assert error_badcases[0].feedback_label == "错误"


class TestBadCaseRecorder:
    """测试BadCase记录器"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def recorder(self, temp_file):
        """创建记录器实例"""
        storage_engine = JSONStorageEngine(temp_file)
        return BadCaseRecorder(storage_engine)
    
    def test_record_badcase(self, recorder):
        """测试记录BadCase"""
        success = recorder.record_badcase(
            input_prompt="测试输入",
            output_result="测试输出",
            feedback_label="错误",
            user_id="user123"
        )
        
        assert success is True
        
        # 验证记录是否保存
        badcases = recorder.storage_engine.get_all_badcases()
        assert len(badcases) == 1
        assert badcases[0].input_prompt == "测试输入"
        assert badcases[0].user_id == "user123"
    
    def test_record_badcase_with_timestamp(self, recorder):
        """测试带时间戳记录BadCase"""
        timestamp = "2024-01-01T12:00:00"
        success = recorder.record_badcase(
            input_prompt="测试输入",
            output_result="测试输出",
            feedback_label="错误",
            user_id="user123",
            timestamp=timestamp
        )
        
        assert success is True
        
        badcases = recorder.storage_engine.get_all_badcases()
        assert badcases[0].timestamp == timestamp
    
    def test_record_badcase_object(self, recorder):
        """测试记录BadCase对象"""
        badcase = BadCase(
            input_prompt="测试输入",
            output_result="测试输出",
            feedback_label="错误",
            user_id="user123",
            timestamp="2024-01-01T00:00:00"
        )
        
        success = recorder.record_badcase_object(badcase)
        assert success is True
        
        badcases = recorder.storage_engine.get_all_badcases()
        assert len(badcases) == 1


class TestBadCaseAnalyzer:
    """测试BadCase分析器"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def analyzer(self, temp_file):
        """创建分析器实例"""
        storage_engine = JSONStorageEngine(temp_file)
        return BadCaseAnalyzer(storage_engine)
    
    def test_get_label_distribution(self, analyzer):
        """测试获取标签分布"""
        # 添加测试数据
        recorder = BadCaseRecorder(analyzer.storage_engine)
        recorder.record_badcase("输入1", "输出1", "错误", "user1")
        recorder.record_badcase("输入2", "输出2", "错误", "user2")
        recorder.record_badcase("输入3", "输出3", "警告", "user3")
        
        distribution = analyzer.get_label_distribution()
        assert distribution["错误"] == 2
        assert distribution["警告"] == 1
    
    def test_get_user_statistics(self, analyzer):
        """测试获取用户统计"""
        # 添加测试数据
        recorder = BadCaseRecorder(analyzer.storage_engine)
        recorder.record_badcase("输入1", "输出1", "错误", "user1")
        recorder.record_badcase("输入2", "输出2", "错误", "user1")
        recorder.record_badcase("输入3", "输出3", "警告", "user2")
        
        user_stats = analyzer.get_user_statistics()
        assert user_stats["user1"] == 2
        assert user_stats["user2"] == 1
    
    def test_get_total_count(self, analyzer):
        """测试获取总数量"""
        # 添加测试数据
        recorder = BadCaseRecorder(analyzer.storage_engine)
        recorder.record_badcase("输入1", "输出1", "错误", "user1")
        recorder.record_badcase("输入2", "输出2", "错误", "user2")
        
        total_count = analyzer.get_total_count()
        assert total_count == 2
    
    def test_get_badcases_by_date_range(self, analyzer):
        """测试根据日期范围获取BadCase"""
        # 添加测试数据
        recorder = BadCaseRecorder(analyzer.storage_engine)
        recorder.record_badcase("输入1", "输出1", "错误", "user1", "2024-01-01T00:00:00")
        recorder.record_badcase("输入2", "输出2", "错误", "user2", "2024-01-15T00:00:00")
        recorder.record_badcase("输入3", "输出3", "警告", "user3", "2024-02-01T00:00:00")
        
        # 获取1月份的BadCase
        january_badcases = analyzer.get_badcases_by_date_range(
            "2024-01-01T00:00:00",
            "2024-01-31T23:59:59"
        )
        assert len(january_badcases) == 2
    
    def test_get_most_common_labels(self, analyzer):
        """测试获取最常见标签"""
        # 添加测试数据
        recorder = BadCaseRecorder(analyzer.storage_engine)
        recorder.record_badcase("输入1", "输出1", "错误", "user1")
        recorder.record_badcase("输入2", "输出2", "错误", "user2")
        recorder.record_badcase("输入3", "输出3", "错误", "user3")
        recorder.record_badcase("输入4", "输出4", "警告", "user4")
        recorder.record_badcase("输入5", "输出5", "警告", "user5")
        recorder.record_badcase("输入6", "输出6", "信息", "user6")
        
        common_labels = analyzer.get_most_common_labels(top_n=3)
        assert len(common_labels) == 3
        assert common_labels[0][0] == "错误"  # 最多的是"错误"
        assert common_labels[0][1] == 3
        assert common_labels[1][0] == "警告"  # 第二多的是"警告"
        assert common_labels[1][1] == 2


class TestIntegration:
    """集成测试"""
    
    @pytest.fixture
    def temp_file(self):
        """创建临时文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            yield f.name
        os.unlink(f.name)
    
    def test_full_workflow(self, temp_file):
        """测试完整工作流程"""
        # 创建组件
        storage_engine = JSONStorageEngine(temp_file)
        recorder = BadCaseRecorder(storage_engine)
        analyzer = BadCaseAnalyzer(storage_engine)
        
        # 记录多个BadCase
        recorder.record_badcase("输入1", "输出1", "错误", "user1")
        recorder.record_badcase("输入2", "输出2", "错误", "user1")
        recorder.record_badcase("输入3", "输出3", "警告", "user2")
        recorder.record_badcase("输入4", "输出4", "信息", "user3")
        
        # 验证分析结果
        assert analyzer.get_total_count() == 4
        assert analyzer.get_label_distribution()["错误"] == 2
        assert analyzer.get_user_statistics()["user1"] == 2
        
        # 验证按用户查询
        user1_badcases = storage_engine.get_badcases_by_user("user1")
        assert len(user1_badcases) == 2
        
        # 验证按标签查询
        error_badcases = storage_engine.get_badcases_by_label("错误")
        assert len(error_badcases) == 2 