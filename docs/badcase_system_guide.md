# BadCase记录系统使用指南

## 概述

BadCase记录系统是一个用于记录、存储和分析AI模型输出问题的工具。它可以帮助开发者追踪和分析模型的不良表现，从而改进模型质量。

## 系统架构

系统包含以下核心组件：

1. **BadCase类** - 数据模型，包含输入提示、输出结果、反馈标签、用户ID和时间戳
2. **JSONStorageEngine** - JSON文件存储引擎，负责数据持久化
3. **BadCaseRecorder** - 记录器，负责创建和保存BadCase
4. **BadCaseAnalyzer** - 分析器，提供统计和分析功能

## 安装和依赖

系统使用Python标准库，无需额外安装依赖：

```python
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
```

## 快速开始

### 1. 基本使用

```python
from utils.badcase_system import (
    BadCase,
    JSONStorageEngine,
    BadCaseRecorder,
    BadCaseAnalyzer
)

# 初始化组件
storage_engine = JSONStorageEngine("badcases.json")
recorder = BadCaseRecorder(storage_engine)
analyzer = BadCaseAnalyzer(storage_engine)

# 记录一个BadCase
success = recorder.record_badcase(
    input_prompt="用户的问题",
    output_result="模型的回答",
    feedback_label="错误类型",
    user_id="user123"
)

# 获取统计信息
total_count = analyzer.get_total_count()
label_distribution = analyzer.get_label_distribution()
```

### 2. 数据模型

#### BadCase类

```python
@dataclass
class BadCase:
    input_prompt: str      # 用户输入
    output_result: str     # 模型输出
    feedback_label: str    # 反馈标签
    user_id: str          # 用户ID
    timestamp: str        # 时间戳
```

所有字段都是必填的，空值会触发验证错误。

### 3. 存储引擎

#### JSONStorageEngine

```python
# 初始化存储引擎
storage = JSONStorageEngine("my_badcases.json")

# 保存BadCase
badcase = BadCase(...)
success = storage.save_badcase(badcase)

# 查询BadCase
all_badcases = storage.get_all_badcases()
user_badcases = storage.get_badcases_by_user("user123")
label_badcases = storage.get_badcases_by_label("错误")
```

### 4. 记录器

#### BadCaseRecorder

```python
recorder = BadCaseRecorder(storage_engine)

# 记录BadCase（自动生成时间戳）
success = recorder.record_badcase(
    input_prompt="问题",
    output_result="回答",
    feedback_label="标签",
    user_id="用户ID"
)

# 记录BadCase（指定时间戳）
success = recorder.record_badcase(
    input_prompt="问题",
    output_result="回答",
    feedback_label="标签",
    user_id="用户ID",
    timestamp="2024-01-01T12:00:00"
)

# 记录BadCase对象
badcase = BadCase(...)
success = recorder.record_badcase_object(badcase)
```

### 5. 分析器

#### BadCaseAnalyzer

```python
analyzer = BadCaseAnalyzer(storage_engine)

# 获取标签分布
distribution = analyzer.get_label_distribution()
# 返回: {"错误": 10, "警告": 5, "信息": 3}

# 获取用户统计
user_stats = analyzer.get_user_statistics()
# 返回: {"user1": 5, "user2": 3, "user3": 10}

# 获取总数量
total = analyzer.get_total_count()

# 获取最常见标签
common_labels = analyzer.get_most_common_labels(top_n=5)
# 返回: [("错误", 10), ("警告", 5), ("信息", 3)]

# 按日期范围查询
date_badcases = analyzer.get_badcases_by_date_range(
    "2024-01-01T00:00:00",
    "2024-01-31T23:59:59"
)
```

## 高级功能

### 1. 自定义存储路径

```python
# 使用自定义路径
storage = JSONStorageEngine("/path/to/custom/badcases.json")
```

### 2. 批量操作

```python
# 批量记录BadCase
badcases = [
    BadCase("问题1", "回答1", "错误", "user1", "2024-01-01T00:00:00"),
    BadCase("问题2", "回答2", "警告", "user2", "2024-01-01T00:00:00"),
]

for badcase in badcases:
    recorder.record_badcase_object(badcase)
```

### 3. 数据验证

系统会自动验证数据完整性：

```python
# 这会抛出ValueError
try:
    badcase = BadCase("", "回答", "标签", "用户", "时间")
except ValueError as e:
    print(f"验证错误: {e}")
```

### 4. 错误处理

所有操作都包含错误处理：

```python
# 存储操作返回布尔值表示成功/失败
success = recorder.record_badcase(...)
if not success:
    print("记录失败")

# 查询操作在出错时返回空列表
badcases = storage.get_all_badcases()
if not badcases:
    print("没有找到BadCase或发生错误")
```

## 测试

运行测试用例：

```bash
# 运行所有测试
pytest tests/test_badcase_system.py -v

# 运行特定测试类
pytest tests/test_badcase_system.py::TestBadCase -v

# 运行特定测试方法
pytest tests/test_badcase_system.py::TestBadCase::test_badcase_creation -v
```

## 示例

查看完整的使用示例：

```bash
python examples/badcase_example.py
```

## 数据格式

### JSON存储格式

```json
[
  {
    "input_prompt": "用户的问题",
    "output_result": "模型的回答",
    "feedback_label": "错误类型",
    "user_id": "user123",
    "timestamp": "2024-01-01T12:00:00"
  },
  {
    "input_prompt": "另一个问题",
    "output_result": "另一个回答",
    "feedback_label": "警告",
    "user_id": "user456",
    "timestamp": "2024-01-01T13:00:00"
  }
]
```

### 时间戳格式

使用ISO 8601格式：`YYYY-MM-DDTHH:MM:SS`

例如：`2024-01-01T12:30:45`

## 最佳实践

1. **标签命名**：使用一致的标签命名规范，如"错误"、"警告"、"信息"
2. **用户ID**：使用有意义的用户标识符
3. **时间戳**：使用ISO格式确保兼容性
4. **文件管理**：定期备份JSON文件
5. **性能考虑**：大量数据时考虑使用数据库存储

## 扩展功能

系统设计为可扩展的，可以轻松添加：

- 数据库存储引擎
- 更复杂的分析功能
- Web界面
- API接口
- 数据导出功能

## 故障排除

### 常见问题

1. **文件权限错误**：确保有写入权限
2. **JSON格式错误**：检查文件完整性
3. **时间戳格式错误**：使用正确的ISO格式
4. **内存不足**：大量数据时考虑分批处理

### 日志

系统使用Python logging模块，可以通过以下方式查看日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 贡献

欢迎提交Issue和Pull Request来改进系统。 