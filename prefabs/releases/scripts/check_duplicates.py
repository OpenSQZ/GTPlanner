#!/usr/bin/env python3
"""
检查是否存在重复的 (id, version) 组合
"""
import json
import sys
from pathlib import Path
from collections import Counter


def main():
    """主函数"""
    try:
        # 读取完整的索引文件
        data_path = Path('community-prefabs.json')
        data = json.loads(data_path.read_text())

        # 统计 (id, version) 组合
        entries = [(item['id'], item['version']) for item in data]
        counter = Counter(entries)

        # 查找重复项
        duplicates = [(key, count) for key, count in counter.items() if count > 1]

        if duplicates:
            print("::error::Found duplicate (id, version) combinations:")
            for (id_val, version), count in duplicates:
                print(f"  - {id_val}@{version} appears {count} times")
            sys.exit(1)

        print(f"✅ No duplicates found (total {len(entries)} entries)")

        # 读取变更条目，确认它是唯一的
        changed_entry_path = Path('changed_entry.json')
        changed_entry = json.loads(changed_entry_path.read_text())

        changed_key = (changed_entry['id'], changed_entry['version'])
        count = counter[changed_key]

        if count != 1:
            print(f"::error::The submitted entry {changed_key[0]}@{changed_key[1]} appears {count} times")
            sys.exit(1)

        print(f"✅ Changed entry is unique: {changed_key[0]}@{changed_key[1]}")

    except FileNotFoundError as e:
        print(f"::error::File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"::error::Invalid JSON format: {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"::error::Missing required field in entry: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"::error::Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

