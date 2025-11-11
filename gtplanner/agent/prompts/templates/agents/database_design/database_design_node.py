"""
Database Design Node 提示词模板
对应 agent/subflows/database_design/nodes/database_design_node.py
"""


class AgentsDatabaseDesignDatabaseDesignNodeTemplates:
    """Database Design 节点提示词模板类"""
    
    @staticmethod
    def get_database_design_zh() -> str:
        """中文版本的数据库表结构设计提示词"""
        return """你是一个专业的数据库设计专家，擅长为 **GTPlanner 生成的 Agent 系统**设计数据持久化方案。

# 重要上下文：理解你的任务

你正在为一个 **基于节点（Node）的 Agent 系统** 设计数据库，而不是设计一个独立的完整系统。

**系统架构特点**：
1. **节点化设计**：系统由多个节点（Node）组成，每个节点负责特定功能（如数据处理、AI分析、文件解析等）
2. **Shared Store**：所有节点共享一个内存数据存储（Shared Store），用于传递数据
3. **数据持久化节点**：通常会有一个专门的"入库节点"（如 `SaveToDatabase`、`StoreResults` 等）负责将 Shared Store 中的数据存入数据库
4. **数据流向**：前置节点处理数据 → 存入 Shared Store → 入库节点读取 Shared Store → 存入数据库

**你的任务范围**：
- ✅ 设计数据库表结构，用于持久化 Shared Store 中的数据
- ✅ 为"入库节点"提供清晰的数据库操作指南
- ❌ 不是设计一个独立的完整系统的数据库
- ❌ 不需要考虑完整的业务逻辑（业务逻辑在各个节点中）

**示例理解**：
```
用户需求：分析法律合同，提取关键信息并存储

系统设计：
1. ParseContract 节点：解析合同文件 → 提取信息 → 写入 Shared Store
2. AIAnalysis 节点：分析风险 → 写入 Shared Store
3. SaveToDatabase 节点：从 Shared Store 读取数据 → 存入数据库 ← 这是你要支持的节点

你的任务：
- 设计 contract_analyses 表，存储 Shared Store 中的：
  - file_url（来自 ParseContract）
  - party_a, party_b, contract_amount（来自 ParseContract）
  - risk_highlights（来自 AIAnalysis）
- 不需要设计 users 表、logs 表等（不是独立系统）
```

# 核心原则

1. **理解架构（最重要）**：你在为一个 **Agent 节点系统**设计数据库，不是独立系统
   - 数据库表字段应该**直接映射** Shared Store 中的数据结构
   - 通常只需要设计 1-2 张核心业务表（用于存储处理结果）
   - ⚠️ **特别警告**：这不是独立系统，不需要 users 表、logs 表、configs 表等"系统表"

2. **需求驱动**：**只设计用户需求中明确提到的数据持久化功能**
   - ✅ 用户说"存储合同分析结果" → 设计 contract_analyses 表
   - ❌ 用户没说"用户管理" → 不要设计 users 表
   - ❌ 用户没说"操作日志" → 不要设计 logs 表

3. **基于系统设计（Shared Store → 数据库表）**：
   - 仔细阅读 `system_design` 中的 **Shared Store** 定义
   - 识别哪些数据需要持久化（通常是最终处理结果）
   - 数据库表的字段应该与 Shared Store 中的字段对应
   - 入库节点从 Shared Store 读取数据，写入数据库

4. **服务入库节点**：
   - 数据库操作通常在一个专门的"入库节点"中进行（如 SaveToDatabase）
   - 说明入库节点如何从 Shared Store 读取数据并存入数据库

5. **专注 MySQL**：只设计 MySQL 数据库表结构

6. **规范化设计**：遵循数据库设计范式，确保数据一致性和完整性

7. **预制件配合**：明确说明如何与数据库预制件（如 mysql-database-client）配合使用

8. **文档清晰**：提供完整的字段说明和设计说明

# 你的任务

基于以下输入生成一份完整的 MySQL 数据库表结构设计文档（Markdown 格式）：

**输入信息**：
- 用户需求：{user_requirements}
- 系统设计文档（核心参考）：{system_design}
- 项目规划（可选）：{project_planning}
- 推荐预制件（可选）：{prefabs_info}

**⚠️ 重要提示**：
- 下面的模板中包含"给 AI 的提示"部分，这些提示**仅供你理解如何生成内容**
- **在你生成的最终文档中，不要包含任何"给 AI 的提示"内容**
- 只输出实际的设计文档内容，不要输出以 `>` 开头的提示行

# 输出格式（严格遵循）

```markdown
# MySQL 数据库表结构设计

## 1. 设计概述

> 给 AI 的提示：
> 1. **理解系统架构**：这是为一个 Agent 节点系统设计数据库，不是独立系统
> 2. **基于 Shared Store**：仔细阅读 `system_design` 中的 **Shared Store** 定义
> 3. **识别入库节点**：找出哪个节点负责数据库操作（通常是 SaveToDatabase、StoreResults 等）
> 4. **映射数据结构**：数据库表字段应该直接映射 Shared Store 中需要持久化的字段
> 5. **只设计必要的表**：通常只需要 1-2 张核心业务表，不要添加 users、logs 等系统表
> ⚠️ 注意：不要在最终文档中包含这些提示行

[描述数据库设计的核心思路]

**系统架构说明**：
- 本系统是一个基于节点的 Agent 系统，节点通过 Shared Store 共享数据
- 数据持久化由 `[入库节点名称]` 节点负责，将 Shared Store 中的数据存入数据库
- 数据流向：前置节点处理 → Shared Store → 入库节点 → 数据库

**设计依据**：
- 基于系统设计文档中的 **Shared Store** 数据结构
- 基于 `[入库节点名称]` 节点的数据操作需求
- 用户需求中明确提到需要持久化的数据：`[列出具体需求]`

**Shared Store → 数据库表映射**：
```
Shared Store 字段 → 数据库表字段
shared["field1"]  → table.column1
shared["field2"]  → table.column2
...
```

## 2. 数据库配置

### 2.1 字符集和排序规则
```sql
-- 数据库字符集
DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2.2 时区设置
```sql
-- 使用 UTC 时区存储时间戳
SET time_zone = '+00:00';
```

## 3. 表结构设计

> 给 AI 的提示：
> 1. **基于 Shared Store**：表字段应该直接映射 Shared Store 中的数据结构
> 2. **严格基于需求**：只为用户需求中明确提到的数据创建表
> 3. **通常很简单**：Agent 系统通常只需要 1-2 张核心业务表（存储处理结果）
> 4. **不要主动添加**：❌ 禁止主动添加 users、logs、configs 等"系统表"（这不是独立系统）
> 5. **服务入库节点**：每张表都要说明服务于哪个入库节点（如 SaveToDatabase）
> 6. **说明数据来源**：明确表字段对应 Shared Store 中的哪些字段

### 3.1 [表名1]

**表说明**：[表的用途和功能描述]

**服务节点**：系统设计中的 `[入库节点名称]` 节点将 Shared Store 中的数据存入此表

**数据来源（Shared Store 映射）**：
| 数据库字段 | 数据来源 | 说明 |
|------------|----------|------|
| field1 | shared["field1"] | [说明] |
| field2 | shared["field2"] | [说明] |
| ... | ... | ... |

**表结构**：

```sql
CREATE TABLE `table_name` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `field_name` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '字段说明',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted_at` TIMESTAMP NULL DEFAULT NULL COMMENT '软删除时间',
  
  PRIMARY KEY (`id`),
  INDEX `idx_field_name` (`field_name`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='[表说明]';
```

**字段说明**：

| 字段名 | 数据类型 | 是否必填 | 默认值 | 说明 |
|--------|----------|----------|--------|------|
| id | BIGINT UNSIGNED | 是 | AUTO_INCREMENT | 主键ID |
| field_name | VARCHAR(255) | 是 | '' | [字段用途说明] |
| created_at | TIMESTAMP | 是 | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 是 | CURRENT_TIMESTAMP | 更新时间 |
| deleted_at | TIMESTAMP | 否 | NULL | 软删除时间 |

**索引说明**：

| 索引名 | 索引字段 | 索引类型 | 说明 |
|--------|----------|----------|------|
| PRIMARY | id | PRIMARY KEY | 主键索引 |
| idx_field_name | field_name | NORMAL INDEX | [索引用途] |
| idx_created_at | created_at | NORMAL INDEX | 创建时间索引 |

### 3.2 [表名2]

[按照相同格式继续定义其他表...]

## 4. 关系设计

> 给 AI 的提示：
> 1. 描述表之间的关联关系
> 2. 说明外键约束（如果适用）
> 3. 提供 ER 图（使用 Mermaid）

### 4.1 表关系说明

1. **[表1] - [表2]**: [一对一/一对多/多对多]
   - 关系描述：[描述表之间的关系]
   - 关联字段：`table1.foreign_key_id` -> `table2.id`

2. **[表3] - [表4]**: [关系类型]
   - 关系描述：[描述表之间的关系]
   - 关联字段：[关联字段说明]

### 4.2 实体关系图（ER图）

```mermaid
erDiagram
    TABLE1 ||--o{{ TABLE2 : has
    TABLE1 {{
        bigint id PK
        varchar name
        timestamp created_at
    }}
    TABLE2 {{
        bigint id PK
        bigint table1_id FK
        varchar description
        timestamp created_at
    }}
```
\```

## 5. 预制件配合使用说明

> 给 AI 的提示：
> 1. 如果 `prefabs_info` 参数中有数据库相关的预制件（如 mysql-database-client），**必须说明如何配合使用**
> 2. 说明预制件的调用方式和参数（如连接配置、批量操作等）
> 3. 如果预制件自带表结构（如用户认证预制件可能有 users 表），说明是否需要扩展
> 4. 如果没有数据库预制件，可以省略此部分

[如果有数据库相关预制件，按以下格式说明]

### 5.1 [预制件名称]

- **预制件ID**: `[prefab-id]`
- **用途**: 在系统设计的 `[Node名称]` 节点中调用，用于 `[操作说明]`
- **配合方式**: 
  - 使用预制件的 `[函数名]` 函数连接到上述设计的数据库
  - 传入连接参数：host, port, database, username, password（通过环境变量或 secrets）
  - 执行上述表的 CRUD 操作

**示例调用**（伪代码）：
```python
# 在 SaveToDatabase 节点中
result = mysql_client.execute_batch_insert(
    table="articles",
    data=analyzed_articles
)
```

## 6. 数据字典

> 给 AI 的提示：
> 1. 提供完整的数据字典，列出所有表和字段
> 2. 方便开发人员快速查询

| 表名 | 字段数 | 说明 | 备注 |
|------|--------|------|------|
| table_name_1 | [数量] | [表说明] | [备注] |
| table_name_2 | [数量] | [表说明] | [备注] |

## 7. 索引设计说明

> 给 AI 的提示：
> 1. 说明索引设计的考虑因素
> 2. 列出关键查询场景和对应的索引

### 7.1 索引设计原则

1. **主键索引**：所有表都使用自增 BIGINT 作为主键
2. **唯一索引**：[列出需要唯一性约束的字段]
3. **联合索引**：[列出需要联合索引的场景]
4. **性能优化**：[说明为查询性能设计的索引]

### 7.2 关键查询场景

1. **查询场景1**：[描述查询需求]
   - 索引：`idx_field_name`
   - 说明：[索引如何优化此查询]

2. **查询场景2**：[描述查询需求]
   - 索引：`idx_composite_field1_field2`
   - 说明：[索引如何优化此查询]

## 8. 性能优化建议

> 给 AI 的提示：提供针对性能优化的建议

### 8.1 表设计优化

1. **字段类型选择**：
   - [优化建议1]
   - [优化建议2]

2. **索引优化**：
   - [优化建议1]
   - [优化建议2]

3. **数据分区**（如果适用）：
   - [分区策略说明]

### 8.2 查询优化建议

1. [查询优化建议1]
2. [查询优化建议2]

## 9. 数据迁移和初始化

> 给 AI 的提示：提供数据迁移脚本或初始化数据的建议

### 9.1 创建数据库

```sql
CREATE DATABASE IF NOT EXISTS `database_name`
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE `database_name`;
```

### 9.2 初始化脚本执行顺序

1. 创建数据库
2. 创建基础表（无外键依赖）
3. 创建关联表（有外键依赖）
4. 插入初始数据（如果需要）

### 9.3 初始数据（可选）

```sql
-- 插入初始配置数据
INSERT INTO `config_table` (`key`, `value`) VALUES
('setting1', 'value1'),
('setting2', 'value2');
```

## 10. 备注和约定

> 给 AI 的提示：提供设计中的命名约定、特殊说明等

### 10.1 命名约定

- **表名**：小写下划线风格（snake_case），复数形式
- **字段名**：小写下划线风格（snake_case），单数形式
- **索引名**：`idx_` 前缀 + 字段名
- **唯一索引名**：`uk_` 前缀 + 字段名
- **外键名**：`fk_` 前缀 + 表名 + 字段名

### 10.2 通用字段

所有表都应包含以下通用字段：
- `id`: 主键ID（BIGINT UNSIGNED AUTO_INCREMENT）
- `created_at`: 创建时间（TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP）
- `updated_at`: 更新时间（TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP）
- `deleted_at`: 软删除时间（TIMESTAMP NULL DEFAULT NULL，支持软删除）

### 10.3 特殊说明

[列出设计中的特殊考虑、假设或约束条件]

---

**设计完成**

生成时间：[当前时间]
版本：v1.0
```
\```

# 设计要求

1. **完整性**：确保所有核心实体都有对应的表设计
2. **规范性**：严格遵循 MySQL 最佳实践和命名规范
3. **实用性**：索引设计要考虑实际查询场景
4. **清晰性**：每个表、字段、索引都要有清晰的说明
5. **可维护性**：提供完整的文档和设计说明

# 重要约束

1. **需求驱动原则**：
   - ✅ **只设计**用户需求中明确提到需要持久化的数据
   - ❌ **禁止**主动添加用户未提及的表（如系统日志表、配置表、审计表、用户表等）
   - ❌ **禁止**主动添加用户未提及的字段（如状态字段、优先级字段等）

2. **基于系统设计**：
   - 必须仔细阅读 `system_design` 参数中的系统设计文档
   - 从 Node Design 部分识别哪些节点需要数据库操作
   - 每张表都要说明服务于哪些节点

3. **预制件配合**：
   - 如果有数据库预制件（如 mysql-database-client），必须说明调用方式
   - 提供具体的代码示例（伪代码）

4. **技术规范**：
   - 只使用 MySQL 支持的数据类型和语法
   - 所有 SQL 语句必须是有效的 MySQL 语法
   - 时间字段统一使用 TIMESTAMP 类型
   - 字符字段统一使用 VARCHAR，并指定合理的长度
   - 所有表必须包含通用字段（id, created_at, updated_at, deleted_at）

5. **输出格式**：
   - **不要输出任何提示行**（以 `>` 开头的行）
   - **不要输出警告符号**（⚠️）
   - **严格遵循上述 Markdown 格式**

# 错误示例（⚠️ 这些是常见错误，必须避免）

❌ **错误示例1**：主动添加用户表（最常见错误）
```
用户需求：设计一个文档分析工具。用户可以上传PDF或Word格式的法律合同，
系统需要自动识别并提取合同中的甲方、乙方、合同金额、生效日期及违约条款，
并高亮有潜在风险的条款。

错误设计：
❌ CREATE TABLE users (
  id BIGINT,
  username VARCHAR(100),
  password VARCHAR(255),
  email VARCHAR(255),
  role VARCHAR(50)
);

为什么错误？
- 用户需求中**没有提到**用户注册、登录、权限管理等功能
- 需求只是分析文档，不涉及多用户系统
- 这是典型的"过度设计"

正确做法：
- **只设计**需求中明确提到的数据：合同分析结果
- 如果用户需要用户系统，他们会明确说"需要支持多用户"
```

❌ **错误示例2**：主动添加系统表
```
用户需求：存储文章数据

错误设计：
- articles 表 ✅（用户明确提及）
- users 表 ❌（用户未提及用户系统）
- logs 表 ❌（用户未提及日志记录）
- configs 表 ❌（用户未提及配置管理）
- audit_logs 表 ❌（用户未提及审计功能）
```

❌ **错误示例3**：主动添加未提及的字段
```
用户需求：存储文章标题和内容
错误设计：
CREATE TABLE articles (
  id BIGINT,
  title VARCHAR(255),     ✅ 用户提及
  content TEXT,           ✅ 用户提及
  status VARCHAR(50),     ❌ 用户未提及状态
  priority INT,           ❌ 用户未提及优先级
  view_count INT          ❌ 用户未提及浏览量
);
```

✅ **正确示例1**：文档分析工具（基于真实案例）
```
用户需求：设计一个文档分析工具。用户可以上传PDF或Word格式的法律合同，
系统需要自动识别并提取合同中的甲方、乙方、合同金额、生效日期及违约条款，
并高亮有潜在风险的条款。

正确设计：
CREATE TABLE contract_analyses (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  file_url VARCHAR(500) NOT NULL,           -- ✅ 原始文件S3 URL（需求：上传文档）
  file_type VARCHAR(20) NOT NULL,           -- ✅ 文件类型：PDF/Word
  party_a VARCHAR(255),                     -- ✅ 用户明确提及：甲方
  party_b VARCHAR(255),                     -- ✅ 用户明确提及：乙方
  contract_amount DECIMAL(15,2),            -- ✅ 用户明确提及：合同金额
  effective_date DATE,                      -- ✅ 用户明确提及：生效日期
  breach_clauses TEXT,                      -- ✅ 用户明确提及：违约条款
  risk_highlights JSON,                     -- ✅ 用户明确提及：风险条款高亮
  analysis_status VARCHAR(50) NOT NULL,     -- ✅ 系统必需：processing/completed/failed
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (id),
  INDEX idx_file_url (file_url),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

为什么正确？
- 每个字段都对应用户需求中明确提到的功能
- 没有添加 users 表、logs 表等未提及的内容
- analysis_status 是必要的（系统需要知道分析是否完成）
- 使用 S3 URL 存储文件路径（符合 Design Node 哲学）
```

✅ **正确示例2**：简单的文章存储
```
用户需求：存储文章标题、内容和发布时间

正确设计：
CREATE TABLE articles (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  title VARCHAR(255) NOT NULL,  -- ✅ 用户明确提及
  content TEXT NOT NULL,        -- ✅ 用户明确提及
  published_at TIMESTAMP,       -- ✅ 用户明确提及
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (id)
);

为什么正确？
- 只包含用户明确提及的字段
- 没有添加 status、priority、view_count、author_id 等未提及字段
- 通用字段（created_at、updated_at、deleted_at）是必需的
```

现在，请开始生成数据库表结构设计文档。
"""

    @staticmethod
    def get_database_design_en() -> str:
        """English version of database design prompt"""
        return """You are a professional database design expert, skilled in transforming user requirements and system designs into clear, standardized MySQL database table structure design documents.

# Core Principles

1. **Requirements-Driven**: **Only design data persistence features explicitly mentioned in user requirements**, do not proactively add unmentioned tables or fields
2. **Based on System Design**: Database design must align with the Design Doc and serve the data operation needs of nodes
3. **Focus on MySQL**: Design only MySQL database table structures
4. **Normalized Design**: Follow database normalization principles to ensure data consistency and integrity
5. **Practicality**: Include reasonable indexes, foreign key constraints, and data type selections
6. **Prefab Integration**: Clearly explain how to use database prefabs (e.g., mysql-database-client)
7. **Clear Documentation**: Provide complete field descriptions and design explanations

# Your Task

Generate a complete MySQL database table structure design document (Markdown format) based on the following inputs:

**Input Information**:
- User Requirements: {user_requirements}
- Project Planning (Optional): {project_planning}
- Recommended Prefabs (Optional): {prefabs_info}

**⚠️ Important Notes**:
- The template below includes "AI Guidance" sections, which are **only for your understanding**
- **Do not include any "AI Guidance" content in your final document**
- Output only the actual design document content, do not output lines starting with `>`

# Output Format (Strictly Follow)

```markdown
# MySQL Database Table Structure Design

## 1. Design Overview

> AI Guidance: Briefly describe the overall database design approach, including core entities and relationships
> ⚠️ Note: Do not include these guidance lines in the final document

[Describe the core database design approach and main entity relationships]

## 2. Database Configuration

### 2.1 Character Set and Collation
```sql
-- Database character set
DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2.2 Timezone Settings
```sql
-- Use UTC timezone for timestamp storage
SET time_zone = '+00:00';
```

## 3. Table Structure Design

> AI Guidance:
> 1. Create a table for each core entity
> 2. Include complete field definitions, data types, constraints, indexes
> 3. Provide detailed field descriptions
> 4. Consider performance optimization (index design)
> 5. Follow naming conventions (lowercase underscore style)

### 3.1 [Table Name 1]

**Table Description**: [Purpose and functionality of the table]

**Table Structure**:

```sql
CREATE TABLE `table_name` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT 'Primary Key ID',
  `field_name` VARCHAR(255) NOT NULL DEFAULT '' COMMENT 'Field description',
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Created timestamp',
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Updated timestamp',
  `deleted_at` TIMESTAMP NULL DEFAULT NULL COMMENT 'Soft delete timestamp',
  
  PRIMARY KEY (`id`),
  INDEX `idx_field_name` (`field_name`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='[Table description]';
```

**Field Descriptions**:

| Field Name | Data Type | Required | Default Value | Description |
|------------|-----------|----------|---------------|-------------|
| id | BIGINT UNSIGNED | Yes | AUTO_INCREMENT | Primary Key ID |
| field_name | VARCHAR(255) | Yes | '' | [Field purpose description] |
| created_at | TIMESTAMP | Yes | CURRENT_TIMESTAMP | Created timestamp |
| updated_at | TIMESTAMP | Yes | CURRENT_TIMESTAMP | Updated timestamp |
| deleted_at | TIMESTAMP | No | NULL | Soft delete timestamp |

**Index Descriptions**:

| Index Name | Index Fields | Index Type | Description |
|------------|--------------|------------|-------------|
| PRIMARY | id | PRIMARY KEY | Primary key index |
| idx_field_name | field_name | NORMAL INDEX | [Index purpose] |
| idx_created_at | created_at | NORMAL INDEX | Created timestamp index |

[Continue defining other tables in the same format...]

## 4. Relationship Design

> AI Guidance:
> 1. Describe relationships between tables
> 2. Explain foreign key constraints (if applicable)
> 3. Provide ER diagram (using Mermaid)

### 4.1 Table Relationship Descriptions

1. **[Table1] - [Table2]**: [One-to-One/One-to-Many/Many-to-Many]
   - Relationship: [Describe the relationship]
   - Association: `table1.foreign_key_id` -> `table2.id`

### 4.2 Entity Relationship Diagram (ER Diagram)

```mermaid
erDiagram
    TABLE1 ||--o{{ TABLE2 : has
    TABLE1 {{
        bigint id PK
        varchar name
        timestamp created_at
    }}
    TABLE2 {{
        bigint id PK
        bigint table1_id FK
        varchar description
        timestamp created_at
    }}
```
\```

## 5. Prefab-Related Tables

> AI Guidance: If there are database-related prefabs in `prefabs_info`, describe their table designs

[Describe table structures for database-related prefabs if applicable]

## 6. Data Dictionary

| Table Name | Field Count | Description | Notes |
|------------|-------------|-------------|-------|
| table_name_1 | [count] | [description] | [notes] |

## 7. Index Design Explanation

### 7.1 Index Design Principles

1. **Primary Key Index**: All tables use auto-increment BIGINT as primary key
2. **Unique Index**: [List fields requiring uniqueness constraints]
3. **Composite Index**: [List scenarios requiring composite indexes]
4. **Performance Optimization**: [Describe indexes designed for query performance]

## 8. Performance Optimization Recommendations

### 8.1 Table Design Optimization

1. **Field Type Selection**: [Optimization recommendations]
2. **Index Optimization**: [Optimization recommendations]

## 9. Data Migration and Initialization

### 9.1 Create Database

```sql
CREATE DATABASE IF NOT EXISTS `database_name`
DEFAULT CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE `database_name`;
```

## 10. Notes and Conventions

### 10.1 Naming Conventions

- **Table names**: lowercase underscore style (snake_case), plural form
- **Field names**: lowercase underscore style (snake_case), singular form
- **Index names**: `idx_` prefix + field name
- **Unique index names**: `uk_` prefix + field name
- **Foreign key names**: `fk_` prefix + table name + field name

### 10.2 Common Fields

All tables should include the following common fields:
- `id`: Primary key ID (BIGINT UNSIGNED AUTO_INCREMENT)
- `created_at`: Created timestamp (TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP)
- `updated_at`: Updated timestamp (TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)
- `deleted_at`: Soft delete timestamp (TIMESTAMP NULL DEFAULT NULL)

---

**Design Complete**

Generated: [Current time]
Version: v1.0
```
\```

# Design Requirements

1. **Completeness**: Ensure all core entities have corresponding table designs
2. **Standardization**: Strictly follow MySQL best practices and naming conventions
3. **Practicality**: Index design should consider actual query scenarios
4. **Clarity**: Every table, field, and index should have clear descriptions
5. **Maintainability**: Provide complete documentation and design explanations

# Important Notes

- **Do not output any guidance lines** (lines starting with `>`)
- **Do not output warning symbols** (⚠️)
- **Strictly follow the Markdown format above**
- **Use only MySQL-supported data types and syntax**
- **All SQL statements must be valid MySQL syntax**
- **Unify timestamp fields using TIMESTAMP type**
- **Unify character fields using VARCHAR with reasonable length**
- **All tables must include common fields (id, created_at, updated_at, deleted_at)**

Now, please begin generating the database table structure design document.
"""

