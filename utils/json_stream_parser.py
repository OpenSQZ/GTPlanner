"""
高性能流式JSON解析器

基于状态机的真正增量解析，避免重复解析整个缓冲区：
1. 状态机驱动 - 只解析新增的字符
2. 事件驱动 - 构建JSON对象
3. 错误修复 - 自动修复不完整的JSON
4. 结构化优化 - 根据JSON模板进行优化解析

使用方法：
    # 一次性解析
    parser = JSONStreamParser()
    result = parser.parse(json_string)

    # 增量解析
    parser = JSONStreamParser()
    for chunk in chunks:
        result = parser.add_chunk(chunk)
    final_result = parser.get_result()

    # 结构化解析（根据模板优化）
    template = {
        "user": {"id": int, "name": str},
        "items": [{"id": int, "value": float}]
    }
    parser = JSONStreamParser(template=template)
    result = parser.parse(json_string)
"""

import json
import re
from typing import Dict, Any, Optional, List, Union
from enum import Enum


class JSONTemplate:
    """JSON结构模板类"""

    def __init__(self, template: Dict[str, Any]):
        """
        初始化JSON模板

        Args:
            template: JSON结构模板，例如：
                {
                    "user": {"id": int, "name": str},
                    "items": [{"id": int, "value": float}],
                    "metadata": {"version": str, "count": int}
                }
        """
        self.template = template
        self.field_priorities = self._analyze_template()
        self.required_fields = self._extract_required_fields()
        self.field_types = self._extract_field_types()

    def _analyze_template(self) -> Dict[str, int]:
        """分析模板，确定字段优先级"""
        priorities = {}

        def analyze_recursive(obj, path="", priority=0):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    priorities[current_path] = priority
                    analyze_recursive(value, current_path, priority + 1)
            elif isinstance(obj, list) and obj:
                # 分析数组元素模板
                analyze_recursive(obj[0], f"{path}[]", priority + 1)

        analyze_recursive(self.template)
        return priorities

    def _extract_required_fields(self) -> set:
        """提取必需字段"""
        required = set()

        def extract_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    required.add(current_path)
                    extract_recursive(value, current_path)
            elif isinstance(obj, list) and obj:
                extract_recursive(obj[0], f"{path}[]")

        extract_recursive(self.template)
        return required

    def _extract_field_types(self) -> Dict[str, type]:
        """提取字段类型信息"""
        types = {}

        def extract_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if isinstance(value, type):
                        types[current_path] = value
                    else:
                        extract_recursive(value, current_path)
            elif isinstance(obj, list) and obj:
                extract_recursive(obj[0], f"{path}[]")

        extract_recursive(self.template)
        return types

    def get_field_priority(self, field_path: str) -> int:
        """获取字段优先级"""
        return self.field_priorities.get(field_path, 999)

    def is_required_field(self, field_path: str) -> bool:
        """检查是否为必需字段"""
        return field_path in self.required_fields

    def get_expected_type(self, field_path: str) -> Optional[type]:
        """获取字段期望类型"""
        return self.field_types.get(field_path)

    def validate_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据结构是否符合模板"""
        validation_result = {
            "valid": True,
            "missing_fields": [],
            "type_errors": [],
            "extra_fields": []
        }

        def validate_recursive(template_obj, data_obj, path=""):
            if isinstance(template_obj, dict):
                if not isinstance(data_obj, dict):
                    validation_result["type_errors"].append({
                        "field": path or "root",
                        "expected": "dict",
                        "actual": type(data_obj).__name__
                    })
                    validation_result["valid"] = False
                    return

                for key, expected_value in template_obj.items():
                    current_path = f"{path}.{key}" if path else key

                    if key not in data_obj:
                        validation_result["missing_fields"].append(current_path)
                        validation_result["valid"] = False
                    else:
                        if isinstance(expected_value, type):
                            # 检查类型
                            actual_value = data_obj[key]
                            if not isinstance(actual_value, expected_value):
                                # 特殊处理：int可以接受float（如果是整数）
                                if expected_value == int and isinstance(actual_value, float) and actual_value.is_integer():
                                    pass  # 允许
                                else:
                                    validation_result["type_errors"].append({
                                        "field": current_path,
                                        "expected": expected_value.__name__,
                                        "actual": type(actual_value).__name__
                                    })
                                    validation_result["valid"] = False
                        else:
                            validate_recursive(expected_value, data_obj[key], current_path)

            elif isinstance(template_obj, list):
                if not isinstance(data_obj, list):
                    validation_result["type_errors"].append({
                        "field": path or "root",
                        "expected": "list",
                        "actual": type(data_obj).__name__
                    })
                    validation_result["valid"] = False
                    return

                if template_obj and data_obj:
                    # 验证数组元素（使用第一个元素作为模板）
                    element_template = template_obj[0]
                    for i, item in enumerate(data_obj):
                        validate_recursive(element_template, item, f"{path}[{i}]")

        validate_recursive(self.template, data)
        return validation_result


class ParseState(Enum):
    """解析状态"""
    START = "start"
    IN_OBJECT = "in_object"
    IN_ARRAY = "in_array"
    IN_STRING = "in_string"
    IN_NUMBER = "in_number"
    IN_LITERAL = "in_literal"
    EXPECT_KEY = "expect_key"
    EXPECT_COLON = "expect_colon"
    EXPECT_VALUE = "expect_value"
    EXPECT_COMMA_OR_END = "expect_comma_or_end"


class JSONStreamParser:
    """高性能流式JSON解析器"""

    def __init__(self, template: Optional[Dict[str, Any]] = None, subscribed_fields: Optional[List[str]] = None):
        """
        初始化解析器

        Args:
            template: 可选的JSON结构模板，用于优化解析
            subscribed_fields: 订阅的字段路径列表，如 ["thought.reasoning", "action.action_type"]
        """
        self.template = JSONTemplate(template) if template else None
        self.current_path = []  # 当前解析路径
        self.field_completion = {}  # 字段完成状态

        # 订阅字段功能
        self.subscribed_fields = set(subscribed_fields or [])
        self.field_subscribers = {}  # 字段订阅回调
        self.field_buffers = {}  # 字段缓冲区，存储已输出的内容
        self.field_positions = {}  # 字段当前输出位置

        self.reset()
    
    def reset(self):
        """重置解析器状态"""
        self.buffer = ""
        self.position = 0  # 当前解析位置
        self.state = ParseState.START
        self.state_stack = []
        self.value_stack = []
        self.key_stack = []
        self.current_key = None
        self.current_value = ""
        self.in_string = False
        self.escape_next = False
        self.result = {}
        self.chunk_count = 0
        self.total_bytes = 0
        self.current_path = []  # 重置路径跟踪
        self.field_completion = {}  # 重置字段完成状态

        # 重置订阅字段状态
        self.field_buffers = {}
        self.field_positions = {}
        for field in self.subscribed_fields:
            self.field_buffers[field] = ""
            self.field_positions[field] = 0
    
    def parse(self, json_str: str) -> Dict[str, Any]:
        """
        一次性解析JSON字符串

        Args:
            json_str: JSON字符串（可能不完整）

        Returns:
            解析结果字典
        """
        if not json_str or not json_str.strip():
            return {}

        # 如果有模板，使用增量解析以支持路径跟踪
        if self.template:
            # 重置状态
            self.reset()
            # 使用增量解析
            self.add_chunk(json_str.strip())
            return self.get_result()

        # 无模板时使用标准解析
        try:
            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            # 标准解析失败，尝试修复
            return self._parse_with_repair(json_str.strip())
    
    def add_chunk(self, chunk: str) -> Dict[str, Any]:
        """
        增量添加数据块（真正的增量解析）
        
        Args:
            chunk: 新的数据块
            
        Returns:
            当前解析结果
        """
        self.buffer += chunk
        self.chunk_count += 1
        self.total_bytes += len(chunk)
        
        # 增量解析新添加的字符
        self._parse_incremental()

        return self.result.copy()
    
    def get_result(self) -> Dict[str, Any]:
        """获取最终解析结果"""
        return self.result.copy()

    def finalize_parsing(self):
        """完成解析，通知所有订阅字段的完成状态"""
        # 通知所有已解析的字段完成
        for field_path in self.subscribed_fields:
            if field_path in self.field_buffers and self.field_buffers[field_path]:
                self._notify_field_update(field_path, "", is_complete=True)

    def get_current_path(self) -> str:
        """获取当前解析路径"""
        return ".".join(self.current_path)

    def get_completion_status(self) -> Dict[str, Any]:
        """获取字段完成状态"""
        if not self.template:
            return {"template_enabled": False}

        # 只计算模板中定义的字段
        required_fields = self.template.required_fields
        completed_required_fields = len([f for f in required_fields if self.field_completion.get(f, False)])

        return {
            "template_enabled": True,
            "total_required_fields": len(required_fields),
            "completed_fields": completed_required_fields,
            "completion_percentage": (completed_required_fields / len(required_fields) * 100) if required_fields else 100,
            "missing_fields": [f for f in required_fields if not self.field_completion.get(f, False)],
            "field_status": {f: self.field_completion.get(f, False) for f in required_fields}
        }

    def validate_result(self) -> Dict[str, Any]:
        """验证解析结果是否符合模板"""
        if not self.template:
            return {"template_enabled": False, "valid": True}

        return self.template.validate_structure(self.result)

    def get_stats(self) -> Dict[str, Any]:
        """获取解析统计信息"""
        return {
            "chunks_processed": self.chunk_count,
            "total_bytes": self.total_bytes,
            "buffer_size": len(self.buffer),
            "parse_position": self.position,
            "avg_chunk_size": self.total_bytes / self.chunk_count if self.chunk_count > 0 else 0
        }

    def subscribe_field(self, field_path: str, callback):
        """
        订阅字段的实时更新

        Args:
            field_path: 字段路径，如 "thought.reasoning"
            callback: 回调函数，接收 (field_path, new_content, is_complete) 参数
        """
        self.subscribed_fields.add(field_path)
        self.field_subscribers[field_path] = callback
        self.field_buffers[field_path] = ""
        self.field_positions[field_path] = 0

    def unsubscribe_field(self, field_path: str):
        """取消订阅字段"""
        self.subscribed_fields.discard(field_path)
        self.field_subscribers.pop(field_path, None)
        self.field_buffers.pop(field_path, None)
        self.field_positions.pop(field_path, None)

    def _get_current_field_path(self) -> str:
        """获取当前字段的完整路径"""
        if not self.current_path:
            return ""
        return ".".join(self.current_path)

    def _notify_field_update(self, field_path: str, new_value: str, is_complete: bool = False):
        """通知字段更新（支持异步回调）"""
        if field_path not in self.subscribed_fields:
            return

        # 获取新增内容
        current_buffer = self.field_buffers.get(field_path, "")
        if new_value != current_buffer:
            new_content = new_value[len(current_buffer):]
            self.field_buffers[field_path] = new_value

            # 调用回调函数（支持异步）
            callback = self.field_subscribers.get(field_path)
            if callback:
                try:
                    import asyncio
                    if asyncio.iscoroutinefunction(callback):
                        # 异步回调：创建任务
                        asyncio.create_task(callback(field_path, new_content, is_complete))
                    else:
                        # 同步回调：直接调用
                        callback(field_path, new_content, is_complete)
                except Exception as e:
                    # 静默处理回调错误，但可以打印调试信息
                    print(f"⚠️ JSONStreamParser回调错误: {e}")
                    pass
    
    def _parse_incremental(self):
        """增量解析新字符（核心算法）"""
        start_position = self.position
        iterations = 0
        max_iterations = len(self.buffer) * 3  # 更宽松的限制

        while self.position < len(self.buffer):
            iterations += 1

            # 更智能的无限循环检测
            if iterations > max_iterations:
                # 如果位置没有前进，才认为是真正的无限循环
                if self.position == start_position and iterations > 1000:
                    # 静默处理，避免干扰用户体验
                    break
                # 如果位置有前进，更新起始位置并重置计数
                elif self.position > start_position:
                    start_position = self.position
                    iterations = 0
                    max_iterations = (len(self.buffer) - self.position) * 3
                else:
                    break

            char = self.buffer[self.position]

            # 跳过空白字符（除非在字符串中）
            if not self.in_string and char in ' \t\n\r':
                self.position += 1
                continue

            # 处理转义字符
            if self.escape_next:
                self.current_value += char
                self._notify_current_field_update()  # 实时通知
                self.escape_next = False
                self.position += 1
                continue

            # 处理字符串状态
            if self.in_string:
                if char == '\\':
                    self.escape_next = True
                    self.current_value += char
                    self._notify_current_field_update()  # 实时通知
                elif char == '"':
                    self.in_string = False
                    self._handle_string_end()
                else:
                    self.current_value += char
                    self._notify_current_field_update()  # 实时通知
                self.position += 1
                continue

            # 处理非字符串状态
            if char == '"':
                self.in_string = True
                self.current_value = ""
                self.state = ParseState.IN_STRING
            elif char == '{':
                self._handle_object_start()
            elif char == '}':
                self._handle_object_end()
            elif char == '[':
                self._handle_array_start()
            elif char == ']':
                self._handle_array_end()
            elif char == ':':
                self._handle_colon()
            elif char == ',':
                self._handle_comma()
            elif char in '0123456789.-+' and self.state == ParseState.EXPECT_VALUE:
                self._handle_number_start()
                continue  # 数字处理会移动position
            elif char in 'tfn' and self.state == ParseState.EXPECT_VALUE:
                self._handle_literal_start()
                continue  # 字面量处理会移动position

            self.position += 1
    
    def _handle_string_end(self):
        """处理字符串结束"""
        if self.state == ParseState.IN_STRING:
            # 判断当前上下文是期待键还是值
            if self.value_stack and isinstance(self.value_stack[-1], dict) and self.current_key is None:
                # 在对象中且没有当前键，这是一个键
                self.current_key = self.current_value
                self._update_path_for_key(self.current_value)
                self.state = ParseState.EXPECT_COLON
            else:
                # 这是一个值
                self._set_value(self.current_value)
                self.state = ParseState.EXPECT_COMMA_OR_END

        self.current_value = ""

    def _update_path_for_key(self, key: str):
        """更新当前路径（当遇到新键时）"""
        # 暂时不添加到路径，等到设置值时再添加
        pass

    def _update_path_for_value(self):
        """更新路径并标记字段完成"""
        if self.template and self.current_key:
            # 构建完整路径
            path_parts = self.current_path + [self.current_key]
            field_path = ".".join(path_parts)

            # 标记字段完成
            self.field_completion[field_path] = True

            # 同时标记父路径完成
            for i in range(len(path_parts)):
                parent_path = ".".join(path_parts[:i+1])
                self.field_completion[parent_path] = True

    def _enter_object(self, key: Optional[str] = None):
        """进入对象时更新路径"""
        if key:
            self.current_path.append(key)

    def _exit_object(self):
        """退出对象时更新路径"""
        if self.current_path:
            self.current_path.pop()

    def _enter_array(self, key: Optional[str] = None):
        """进入数组时更新路径"""
        if key:
            self.current_path.append(key)

    def _exit_array(self):
        """退出数组时更新路径"""
        if self.current_path:
            self.current_path.pop()
    
    def _handle_object_start(self):
        """处理对象开始"""
        new_obj = {}

        if self.state == ParseState.START:
            # 这是根对象
            self.result = new_obj
        else:
            # 这是嵌套对象
            # 先进入对象路径（如果有键）
            if self.current_key:
                self._enter_object(self.current_key)
            # 然后设置对象值，但不触发路径更新
            self._set_value_without_path_update(new_obj)

        # 将新对象推入栈
        self.value_stack.append(new_obj)
        self.key_stack.append(self.current_key)
        self.current_key = None
        self.state_stack.append(self.state)
        self.state = ParseState.EXPECT_KEY
    
    def _handle_object_end(self):
        """处理对象结束"""
        if self.value_stack:
            self.value_stack.pop()
        if self.key_stack:
            self.current_key = self.key_stack.pop()
        if self.state_stack:
            self.state = self.state_stack.pop()
        else:
            self.state = ParseState.EXPECT_COMMA_OR_END

        # 退出对象时更新路径
        self._exit_object()
    
    def _handle_array_start(self):
        """处理数组开始"""
        new_array = []
        # 先进入数组路径（如果有键）
        if self.current_key:
            self._enter_array(self.current_key)
        # 然后设置数组值，但不触发路径更新
        self._set_value_without_path_update(new_array)
        self.value_stack.append(new_array)
        self.key_stack.append(self.current_key)
        self.current_key = None
        self.state_stack.append(self.state)
        self.state = ParseState.EXPECT_VALUE
    
    def _handle_array_end(self):
        """处理数组结束"""
        if self.value_stack:
            self.value_stack.pop()
        if self.key_stack:
            self.current_key = self.key_stack.pop()
        if self.state_stack:
            self.state = self.state_stack.pop()
        else:
            self.state = ParseState.EXPECT_COMMA_OR_END

        # 退出数组时更新路径
        self._exit_array()
    
    def _handle_colon(self):
        """处理冒号"""
        if self.state == ParseState.EXPECT_COLON:
            self.state = ParseState.EXPECT_VALUE
    
    def _handle_comma(self):
        """处理逗号"""
        if self.state == ParseState.EXPECT_COMMA_OR_END:
            if self.value_stack and isinstance(self.value_stack[-1], dict):
                self.state = ParseState.EXPECT_KEY
            else:
                self.state = ParseState.EXPECT_VALUE
    
    def _handle_number_start(self):
        """处理数字开始"""
        start_pos = self.position

        # 扫描数字字符
        while (self.position < len(self.buffer) and
               self.buffer[self.position] in '0123456789.-+eE'):
            self.position += 1

        # 如果到达缓冲区末尾，数字可能不完整，等待更多数据
        if self.position >= len(self.buffer):
            self.position = start_pos
            return

        # 检查数字是否完整（后面必须是分隔符）
        if self.buffer[self.position] not in ' \t\n\r,}]':
            # 数字可能不完整，等待更多数据
            self.position = start_pos
            return

        number_str = self.buffer[start_pos:self.position]

        # 解析数字
        if number_str and number_str not in ['-', '.', '+', '']:
            try:
                if '.' in number_str or 'e' in number_str.lower():
                    value = float(number_str)
                else:
                    value = int(number_str)
                self._set_value(value)
                self.state = ParseState.EXPECT_COMMA_OR_END
            except ValueError:
                # 数字格式错误，回退
                self.position = start_pos

        self.position -= 1  # 回退一位，因为外层循环会+1
    
    def _handle_literal_start(self):
        """处理字面量开始 (true, false, null)"""
        start_pos = self.position

        # 扫描字母字符
        while (self.position < len(self.buffer) and
               self.buffer[self.position].isalpha()):
            self.position += 1

        literal = self.buffer[start_pos:self.position]

        # 检查字面量是否完整
        expected_literals = {'true': 4, 'false': 5, 'null': 4}

        # 如果字面量可能不完整，等待更多数据
        for expected, length in expected_literals.items():
            if expected.startswith(literal) and len(literal) < length:
                if (self.position >= len(self.buffer) or
                    self.buffer[self.position] not in ' \t\n\r,}]'):
                    # 可能不完整，等待更多数据
                    self.position = start_pos
                    return

        # 处理完整的字面量
        if literal == 'true':
            self._set_value(True)
            self.state = ParseState.EXPECT_COMMA_OR_END
        elif literal == 'false':
            self._set_value(False)
            self.state = ParseState.EXPECT_COMMA_OR_END
        elif literal == 'null':
            self._set_value(None)
            self.state = ParseState.EXPECT_COMMA_OR_END
        else:
            # 未知字面量，回退
            self.position = start_pos

        self.position -= 1  # 回退一位，因为外层循环会+1
    
    def _set_value(self, value: Any):
        """设置值到当前容器"""
        if not self.value_stack:
            return

        current_container = self.value_stack[-1]
        if isinstance(current_container, dict):
            if self.current_key is not None:
                current_container[self.current_key] = value

                # 构建字段路径并通知订阅者
                field_path = self._build_field_path_for_key(self.current_key)
                if field_path:
                    self._notify_field_update(field_path, str(value), is_complete=True)

                # 更新路径和字段完成状态
                self._update_path_for_value()
                self.current_key = None
        elif isinstance(current_container, list):
            current_container.append(value)

    def _build_field_path_for_key(self, key: str) -> str:
        """为指定键构建完整的字段路径"""
        if not self.current_path:
            return key
        return ".".join(self.current_path + [key])

    def _notify_current_field_update(self):
        """通知当前字段的实时更新"""
        if not self.current_key or not self.current_value:
            return

        # 构建当前字段路径
        field_path = self._build_field_path_for_key(self.current_key)
        if field_path in self.subscribed_fields:
            self._notify_field_update(field_path, self.current_value, is_complete=False)

    def _set_value_without_path_update(self, value: Any):
        """设置值到当前容器（不更新路径跟踪）"""
        if not self.value_stack:
            return

        current_container = self.value_stack[-1]
        if isinstance(current_container, dict):
            if self.current_key is not None:
                current_container[self.current_key] = value
                self.current_key = None
        elif isinstance(current_container, list):
            current_container.append(value)

    def _parse_with_repair(self, json_str: str) -> Dict[str, Any]:
        """带修复功能的JSON解析（回退方案）"""
        # 清理输入
        json_str = self._clean_json_string(json_str)

        # 尝试修复并解析
        fixed_json = self._fix_incomplete_json(json_str)

        try:
            return json.loads(fixed_json)
        except json.JSONDecodeError:
            # 修复失败，尝试提取部分内容
            return self._extract_partial_json(json_str)

    def _clean_json_string(self, json_str: str) -> str:
        """清理JSON字符串"""
        # 移除markdown代码块
        json_str = re.sub(r'^```json\s*', '', json_str)
        json_str = re.sub(r'\s*```$', '', json_str)

        # 查找JSON开始位置
        start_idx = json_str.find('{')
        if start_idx != -1:
            json_str = json_str[start_idx:]
        elif not json_str.startswith('{'):
            json_str = '{' + json_str

        return json_str

    def _fix_incomplete_json(self, json_str: str) -> str:
        """修复不完整的JSON字符串"""
        # 修复未闭合的字符串
        json_str = self._fix_unclosed_strings(json_str)

        # 修复未闭合的括号
        json_str = self._fix_unclosed_brackets(json_str)

        return json_str

    def _fix_unclosed_strings(self, json_str: str) -> str:
        """修复未闭合的字符串"""
        result = []
        in_string = False
        escape_next = False

        for char in json_str:
            if escape_next:
                result.append(char)
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                result.append(char)
                continue

            if char == '"':
                in_string = not in_string

            result.append(char)

        # 如果字符串未闭合，添加闭合引号
        if in_string:
            result.append('"')

        return ''.join(result)

    def _fix_unclosed_brackets(self, json_str: str) -> str:
        """修复未闭合的括号"""
        brace_count = 0
        bracket_count = 0
        in_string = False
        escape_next = False

        for char in json_str:
            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            if char == '"':
                in_string = not in_string
                continue

            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                elif char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1

        # 添加缺失的闭合括号
        result = json_str
        for _ in range(bracket_count):
            result += ']'
        for _ in range(brace_count):
            result += '}'

        return result

    def _extract_partial_json(self, json_str: str) -> Dict[str, Any]:
        """从损坏的JSON中提取部分内容"""
        result = {}

        # 使用正则表达式提取键值对
        patterns = [
            r'"([^"]+)"\s*:\s*"([^"]*)"',  # 字符串值
            r'"([^"]+)"\s*:\s*(true|false|null)',  # 布尔值和null
            r'"([^"]+)"\s*:\s*(-?\d+\.?\d*)',  # 数字值
        ]

        for pattern in patterns:
            matches = re.findall(pattern, json_str)
            for match in matches:
                key = match[0]
                value = match[1]

                # 转换值类型
                if pattern.endswith(r'(-?\d+\.?\d*)'):
                    try:
                        value = float(value) if '.' in value else int(value)
                    except ValueError:
                        pass
                elif value == 'true':
                    value = True
                elif value == 'false':
                    value = False
                elif value == 'null':
                    value = None

                result[key] = value

        return result

    def parse_react_response(self, response_text: str) -> Dict[str, Any]:
        """专门解析ReAct响应"""
        # 解析JSON
        parsed = self.parse(response_text)

        # 确保ReAct结构完整
        react_result = {
            "thought": parsed.get("thought", {}),
            "action_decision": parsed.get("action_decision", {}),
            "observation": parsed.get("observation", {})
        }

        # 补充默认值
        if not react_result["thought"]:
            react_result["thought"] = {
                "reasoning": "正在思考中...",
                "current_goal": "处理用户请求",
                "known_information": [],
                "gaps_identified": []
            }

        if not react_result["action_decision"]:
            react_result["action_decision"] = {
                "should_act": False,
                "action_type": "wait",
                "action_rationale": "等待更多信息",
                "confidence": 0.1
            }

        if not react_result["observation"]:
            react_result["observation"] = {
                "should_continue_cycle": True,
                "goal_achieved": False,
                "requires_user_input": False,
                "current_progress": "处理中"
            }

        return react_result


# 便捷函数
def parse_json(json_str: str) -> Dict[str, Any]:
    """便捷函数：解析JSON字符串"""
    parser = JSONStreamParser()
    return parser.parse(json_str)


def parse_react_response(response_text: str) -> Dict[str, Any]:
    """便捷函数：解析ReAct响应"""
    parser = JSONStreamParser()
    return parser.parse_react_response(response_text)


def create_streaming_parser() -> JSONStreamParser:
    """便捷函数：创建流式解析器实例"""
    return JSONStreamParser()
