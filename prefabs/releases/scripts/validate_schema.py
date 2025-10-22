#!/usr/bin/env python3
"""
验证 community-prefabs.json 符合 JSON Schema
"""
import json
import sys
from pathlib import Path

import jsonschema


def main():
    """主函数"""
    try:
        # 读取 schema 和数据
        schema_path = Path('schema.json')
        data_path = Path('community-prefabs.json')
        changed_entry_path = Path('changed_entry.json')

        schema = json.loads(schema_path.read_text())
        full_data = json.loads(data_path.read_text())
        changed_entry = json.loads(changed_entry_path.read_text())

        # 验证整个文件符合 schema
        try:
            jsonschema.validate(instance=full_data, schema=schema)
            print("✅ Full file schema validation passed")
        except jsonschema.ValidationError as e:
            print(f"::error::Schema validation failed for full file: {e.message}")
            print(f"Failed at path: {' -> '.join(str(p) for p in e.path)}")
            sys.exit(1)

        # 验证变更的条目符合 schema item 定义
        try:
            item_schema = schema['items']
            jsonschema.validate(instance=changed_entry, schema=item_schema)
            print(f"✅ Changed entry schema validation passed: {changed_entry['id']}@{changed_entry['version']}")
        except jsonschema.ValidationError as e:
            print(f"::error::Schema validation failed for changed entry: {e.message}")
            print(f"Failed at path: {' -> '.join(str(p) for p in e.path)}")
            sys.exit(1)

        # Schema 验证已经包含了必填字段检查，无需额外验证
        print("✅ All schema validations passed")

    except FileNotFoundError as e:
        print(f"::error::File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"::error::Invalid JSON format: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"::error::Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

