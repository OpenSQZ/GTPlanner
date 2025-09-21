"""
JSON 流式解析器测试
"""
import pytest
import json
from typing import Dict, Any

# 添加项目根目录到 Python 路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.json_stream_parser import JSONStreamParser, JSONTemplate


class TestJSONTemplate:
    """JSONTemplate 测试类"""

    def test_init_with_dict(self):
        """测试使用字典初始化模板"""
        template_dict = {
            "name": str,
            "age": int,
            "items": [{"id": int, "value": float}]
        }
        
        template = JSONTemplate(template_dict)
        assert template.template == template_dict

    def test_init_with_none(self):
        """测试使用 None 初始化模板"""
        template = JSONTemplate(None)
        assert template.template is None

    def test_validate_structure_valid(self):
        """测试有效结构验证"""
        template_dict = {
            "name": str,
            "age": int
        }
        template = JSONTemplate(template_dict)

        data = {"name": "张三", "age": 25}
        result = template.validate_structure(data)

        assert result["valid"] is True
        assert result["missing_fields"] == []
        assert result["type_errors"] == []

    def test_validate_structure_invalid_type(self):
        """测试无效类型验证"""
        template_dict = {
            "name": str,
            "age": int
        }
        template = JSONTemplate(template_dict)

        data = {"name": "张三", "age": "25"}  # age 应该是 int
        result = template.validate_structure(data)

        assert result["valid"] is False
        assert len(result["type_errors"]) > 0

    def test_validate_structure_missing_field(self):
        """测试缺失字段验证"""
        template_dict = {
            "name": str,
            "age": int
        }
        template = JSONTemplate(template_dict)

        data = {"name": "张三"}  # 缺少 age 字段
        result = template.validate_structure(data)

        assert result["valid"] is False
        assert "age" in result["missing_fields"]


class TestJSONStreamParser:
    """JSONStreamParser 测试类"""

    def test_init_without_template(self):
        """测试不带模板初始化"""
        parser = JSONStreamParser()
        assert parser.template is None
        assert parser.current_path == []
        assert parser.field_completion == {}

    def test_init_with_template(self):
        """测试带模板初始化"""
        template = {"name": str, "age": int}
        parser = JSONStreamParser(template=template)
        
        assert parser.template is not None
        assert parser.template.template == template

    def test_parse_simple_json(self):
        """测试解析简单 JSON"""
        parser = JSONStreamParser()
        
        json_str = '{"name": "张三", "age": 25}'
        result = parser.parse(json_str)
        
        assert result["name"] == "张三"
        assert result["age"] == 25

    def test_parse_empty_string(self):
        """测试解析空字符串"""
        parser = JSONStreamParser()
        
        result = parser.parse("")
        assert result == {}
        
        result = parser.parse("   ")
        assert result == {}

    def test_parse_invalid_json(self):
        """测试解析无效 JSON"""
        parser = JSONStreamParser()
        
        # 不完整的 JSON
        json_str = '{"name": "张三", "age":'
        result = parser.parse(json_str)
        
        # 应该返回部分解析结果或空字典
        assert isinstance(result, dict)

    def test_add_chunk_incremental(self):
        """测试增量添加数据块"""
        parser = JSONStreamParser()
        
        # 分块添加 JSON 数据
        chunks = ['{"name":', ' "张三",', ' "age": 25}']
        
        results = []
        for chunk in chunks:
            result = parser.add_chunk(chunk)
            results.append(result)
        
        final_result = parser.get_result()
        assert final_result["name"] == "张三"
        assert final_result["age"] == 25

    def test_add_chunk_with_chinese(self):
        """测试处理中文字符"""
        parser = JSONStreamParser()
        
        json_str = '{"姓名": "李四", "年龄": 30, "城市": "北京"}'
        result = parser.parse(json_str)
        
        assert result["姓名"] == "李四"
        assert result["年龄"] == 30
        assert result["城市"] == "北京"

    def test_parse_nested_json(self):
        """测试解析嵌套 JSON"""
        parser = JSONStreamParser()
        
        json_str = '''
        {
            "user": {
                "id": 1,
                "name": "张三",
                "profile": {
                    "age": 25,
                    "city": "上海"
                }
            },
            "items": [
                {"id": 1, "name": "商品1"},
                {"id": 2, "name": "商品2"}
            ]
        }
        '''
        
        result = parser.parse(json_str)
        
        assert result["user"]["name"] == "张三"
        assert result["user"]["profile"]["age"] == 25
        assert len(result["items"]) == 2
        assert result["items"][0]["name"] == "商品1"

    def test_parse_with_template_validation(self):
        """测试带模板验证的解析"""
        template = {
            "user": {
                "id": int,
                "name": str
            },
            "items": [{"id": int, "name": str}]
        }
        
        parser = JSONStreamParser(template=template)
        
        json_str = '''
        {
            "user": {"id": 1, "name": "张三"},
            "items": [{"id": 1, "name": "商品1"}]
        }
        '''
        
        result = parser.parse(json_str)
        
        # 验证解析结果
        assert result["user"]["id"] == 1
        assert result["user"]["name"] == "张三"
        assert len(result["items"]) == 1

    def test_get_stats(self):
        """测试获取解析统计信息"""
        parser = JSONStreamParser()

        # 添加一些数据
        parser.add_chunk('{"name": "张三"}')
        stats = parser.get_stats()

        assert isinstance(stats, dict)
        assert "chunks_processed" in stats
        assert "total_bytes" in stats
        assert stats["chunks_processed"] == 1

    def test_reset_parser(self):
        """测试重置解析器"""
        parser = JSONStreamParser()
        
        # 添加一些数据
        parser.add_chunk('{"name": "张三"}')
        assert parser.buffer != ""
        
        # 重置
        parser.reset()
        assert parser.buffer == ""
        assert parser.result == {}
        assert parser.chunk_count == 0

    def test_large_json_performance(self):
        """测试大 JSON 性能"""
        # 创建一个较大的 JSON 对象
        large_data = {
            "users": [
                {"id": i, "name": f"用户{i}", "email": f"user{i}@example.com"}
                for i in range(100)
            ],
            "metadata": {
                "total": 100,
                "page": 1,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        json_str = json.dumps(large_data, ensure_ascii=False)
        
        parser = JSONStreamParser()
        result = parser.parse(json_str)
        
        assert len(result["users"]) == 100
        assert result["metadata"]["total"] == 100

    def test_malformed_json_recovery(self):
        """测试损坏 JSON 的恢复"""
        parser = JSONStreamParser()
        
        # 故意损坏的 JSON
        malformed_json = '{"name": "张三", "age": 25, "city":'
        
        result = parser.parse(malformed_json)
        
        # 应该能解析出部分有效数据
        assert isinstance(result, dict)
        # 可能包含 name 和 age，但 city 可能缺失

    def test_streaming_with_template(self):
        """测试带模板的流式解析"""
        template = {
            "thought": {"reasoning": str, "action": str},
            "action": {"action_type": str, "parameters": dict}
        }
        
        parser = JSONStreamParser(template=template)
        
        # 模拟流式数据
        chunks = [
            '{"thought": {"reasoning": "我需要分析',
            '这个问题", "action": "调用工具"},',
            ' "action": {"action_type": "search",',
            ' "parameters": {"query": "测试"}}}'
        ]
        
        for chunk in chunks:
            parser.add_chunk(chunk)
        
        result = parser.get_result()
        
        assert "thought" in result
        assert "action" in result
        assert result["thought"]["reasoning"].startswith("我需要分析")
        assert result["action"]["action_type"] == "search"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
