#!/usr/bin/env python3
"""
创建GTPlanner数据库

用于创建完整的GTPlanner对话历史数据库，供可视化工具检查表结构。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from agent.persistence.database_schema import initialize_database, get_database_info


def main():
    """创建数据库并显示信息"""
    db_path = "gtplanner_conversations.db"
    
    print("🚀 创建GTPlanner对话历史数据库")
    print("=" * 60)
    print(f"数据库路径: {db_path}")
    print("=" * 60)
    
    # 初始化数据库
    if initialize_database(db_path):
        print("\n📊 数据库创建成功！")
        
        # 显示数据库信息
        info = get_database_info(db_path)
        print("\n📋 数据库详细信息:")
        print(f"  📁 文件路径: {info['database_path']}")
        print(f"  🔢 架构版本: {info['schema_version']}")
        print(f"  📊 总记录数: {info['total_records']}")
        
        print("\n📋 表结构:")
        for table, count in info['tables'].items():
            print(f"  📄 {table}: {count} 条记录")
        
        print("\n🎯 表结构说明:")
        print("  📄 sessions: 会话元数据（会话ID、标题、阶段、压缩状态等）")
        print("  💬 messages: 完整对话记录（永不删除，支持消息链追踪）")
        print("  🗜️  compressed_context: 压缩上下文（智能压缩后的对话摘要）")
        print("  🔧 tool_executions: 工具执行记录（Function Calling详情）")
        print("  🔍 search_index: 搜索索引（全文搜索优化）")
        print("  ⚙️  database_metadata: 数据库元数据（版本、配置等）")
        
        print("\n🔍 关键特性:")
        print("  ✅ 完整历史记录保存（messages表永不删除数据）")
        print("  ✅ 增量压缩机制（compressed_context表支持版本管理）")
        print("  ✅ 智能索引优化（支持快速查询和全文搜索）")
        print("  ✅ 外键约束和触发器（数据一致性保证）")
        print("  ✅ SQLite FTS5全文搜索（高性能内容检索）")
        
        print(f"\n🎉 数据库已创建: {db_path}")
        print("💡 你现在可以使用可视化工具（如DB Browser for SQLite）检查表结构")
        
    else:
        print("❌ 数据库创建失败")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
