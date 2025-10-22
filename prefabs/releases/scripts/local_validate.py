#!/usr/bin/env python3
"""
本地验证脚本 - 在提交 PR 前本地验证你的修改
"""
import json
import sys
from pathlib import Path
from collections import Counter

try:
    import jsonschema
    import requests
except ImportError:
    print("❌ Missing required dependencies. Please install:")
    print("   uv add --dev jsonschema requests")
    sys.exit(1)


def construct_artifact_url(entry):
    """根据约定构造 artifact URL

    注意：Python wheel 文件名会将连字符转换为下划线
    例如：hello-world-test → hello_world_test
    """
    repo_url = entry['repo_url'].rstrip('/')
    version = entry['version']
    prefab_id = entry['id']
    # 将 ID 中的连字符转换为下划线（符合 Python wheel 命名规范）
    wheel_name = prefab_id.replace('-', '_')
    return f"{repo_url}/releases/download/v{version}/{wheel_name}-{version}-py3-none-any.whl"


def print_step(step: str, msg: str):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"[{step}] {msg}")
    print('='*60)


def validate_json_syntax():
    """验证 JSON 语法"""
    print_step("STEP 1", "验证 JSON 语法")
    try:
        data_path = Path('community-prefabs.json')
        data = json.loads(data_path.read_text(encoding='utf-8'))
        print(f"✅ JSON 语法正确 (共 {len(data)} 条记录)")
        return data
    except FileNotFoundError:
        print("❌ 找不到 community-prefabs.json 文件")
        print("   请确保在仓库根目录运行此脚本")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 格式错误: {e}")
        print(f"   行 {e.lineno}, 列 {e.colno}")
        sys.exit(1)


def validate_schema(data):
    """验证 Schema"""
    print_step("STEP 2", "验证 JSON Schema")
    try:
        schema_path = Path('schema.json')
        schema = json.loads(schema_path.read_text(encoding='utf-8'))

        jsonschema.validate(instance=data, schema=schema)
        print("✅ Schema 验证通过")

        # 验证每个条目
        for i, item in enumerate(data):
            try:
                jsonschema.validate(instance=item, schema=schema['items'])
            except jsonschema.ValidationError as e:
                print(f"❌ 条目 {i} 验证失败: {item.get('id', 'unknown')}")
                print(f"   错误: {e.message}")
                sys.exit(1)

        print(f"✅ 所有 {len(data)} 条记录验证通过")

    except FileNotFoundError:
        print("❌ 找不到 schema.json 文件")
        sys.exit(1)
    except jsonschema.ValidationError as e:
        print(f"❌ Schema 验证失败: {e.message}")
        print(f"   路径: {' -> '.join(str(p) for p in e.path)}")
        sys.exit(1)


def check_duplicates(data):
    """检查重复条目"""
    print_step("STEP 3", "检查重复条目")

    entries = [(item['id'], item['version']) for item in data]
    counter = Counter(entries)

    duplicates = [(key, count) for key, count in counter.items() if count > 1]

    if duplicates:
        print("❌ 发现重复的 (id, version) 组合:")
        for (id_val, version), count in duplicates:
            print(f"   - {id_val}@{version} 出现了 {count} 次")
        sys.exit(1)

    print(f"✅ 没有重复条目 (共 {len(entries)} 条唯一记录)")


def check_required_fields(data):
    """检查必填字段"""
    print_step("STEP 4", "检查必填字段")

    required_fields = ['id', 'version', 'author', 'repo_url', 'name', 'description']

    for i, item in enumerate(data):
        item_id = item.get('id', f'item-{i}')
        missing = [field for field in required_fields if field not in item]

        if missing:
            print(f"❌ 条目 {item_id} 缺少必填字段:")
            for field in missing:
                print(f"   - {field}")
            sys.exit(1)

    print(f"✅ 所有条目包含必填字段")


def check_url_format(data):
    """检查 URL 格式"""
    print_step("STEP 5", "检查 URL 格式")

    errors = []

    for item in data:
        item_id = item['id']

        # 检查 repo_url
        repo_url = item.get('repo_url', '')
        if not repo_url.startswith('https://github.com/'):
            errors.append(f"   - {item_id}: repo_url 必须是 GitHub URL")

    if errors:
        print("❌ 发现 URL 格式错误:")
        for error in errors:
            print(error)
        sys.exit(1)

    print("✅ 所有 URL 格式正确")


def check_artifact_accessibility(data, check_all=False):
    """检查构件可访问性（可选）"""
    print_step("STEP 6", "检查构件可访问性 (可选)")

    if not check_all:
        print("⏭️  跳过 URL 可达性检查（使用 --check-urls 启用）")
        return

    print("正在检查所有构件 URL 的可达性...")

    for item in data:
        item_id = item['id']
        artifact_url = construct_artifact_url(item)

        print(f"  检查: {item_id} ... ", end='', flush=True)
        print(f"\n    URL: {artifact_url}")

        try:
            response = requests.head(artifact_url, allow_redirects=True, timeout=10)
            if 200 <= response.status_code < 300:
                print("    ✅")
            else:
                print(f"    ❌ (HTTP {response.status_code})")
        except requests.RequestException as e:
            print(f"    ❌ ({e})")


def print_summary(data):
    """打印摘要信息"""
    print_step("SUMMARY", "验证摘要")

    print(f"总计条目数: {len(data)}")
    print(f"作者数: {len(set(item['author'] for item in data))}")

    # 统计标签
    all_tags = []
    for item in data:
        all_tags.extend(item.get('tags', []))

    if all_tags:
        tag_counter = Counter(all_tags)
        print(f"\n最常用的标签:")
        for tag, count in tag_counter.most_common(5):
            print(f"  - {tag}: {count}")

    print("\n" + "="*60)
    print("🎉 所有验证通过！你可以提交 PR 了。")
    print("="*60)
    print("\n提示: artifact_url 将自动构造为:")
    print("  {repo_url}/releases/download/v{version}/{id}-{version}.whl")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='本地验证 community-prefabs.json')
    parser.add_argument('--check-urls', action='store_true',
                       help='检查所有 artifact_url 的可达性（较慢）')
    args = parser.parse_args()

    print("""
╔══════════════════════════════════════════════════════════════╗
║         Prefab Releases - 本地验证工具                       ║
║     在提交 PR 前验证你的 community-prefabs.json              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    try:
        # 执行所有验证步骤
        data = validate_json_syntax()
        validate_schema(data)
        check_duplicates(data)
        check_required_fields(data)
        check_url_format(data)
        check_artifact_accessibility(data, check_all=args.check_urls)

        # 打印摘要
        print_summary(data)

    except KeyboardInterrupt:
        print("\n\n⚠️  验证被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 意外错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
