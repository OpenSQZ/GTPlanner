#!/usr/bin/env python3
"""
下载并验证 .whl 构件的内容完整性
"""
import json
import shutil
import sys
import zipfile
from pathlib import Path

import requests


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


def main():
    """主函数"""
    try:
        # 读取变更条目
        changed_entry_path = Path('changed_entry.json')
        changed_entry = json.loads(changed_entry_path.read_text())

        artifact_url = construct_artifact_url(changed_entry)
        pr_id = changed_entry['id']
        pr_version = changed_entry['version']

        print(f"Downloading artifact from: {artifact_url}")

        # 下载 .whl 文件
        artifact_path = Path('artifact.whl')
        try:
            response = requests.get(artifact_url, timeout=60)
            response.raise_for_status()
            artifact_path.write_bytes(response.content)
            print(f"✅ Downloaded artifact: {artifact_path} ({len(response.content)} bytes)")
        except requests.RequestException as e:
            print(f"::error::Failed to download artifact: {e}")
            sys.exit(1)

        # 解压 .whl 文件
        temp_dir = Path('temp_whl')
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir()

        try:
            with zipfile.ZipFile(artifact_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            print(f"✅ Extracted artifact to: {temp_dir}")
        except zipfile.BadZipFile as e:
            print(f"::error::Invalid .whl file (not a valid zip): {e}")
            sys.exit(1)

        # 查找 prefab-manifest.json
        manifest_paths = list(temp_dir.rglob('prefab-manifest.json'))

        if not manifest_paths:
            print("::error::prefab-manifest.json not found in the .whl artifact")
            print("Expected structure: <package-name>/prefab-manifest.json")
            sys.exit(1)

        if len(manifest_paths) > 1:
            print(f"::warning::Found multiple prefab-manifest.json files: {manifest_paths}")

        manifest_path = manifest_paths[0]
        print(f"Found manifest at: {manifest_path}")

        # 读取并验证 manifest
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            print(f"::error::Invalid JSON in prefab-manifest.json: {e}")
            sys.exit(1)

        # 验证 ID 和版本一致性
        manifest_id = manifest_data.get('id')
        manifest_version = manifest_data.get('version')

        if not manifest_id or not manifest_version:
            print("::error::prefab-manifest.json missing 'id' or 'version' field")
            sys.exit(1)

        if manifest_id != pr_id:
            print(f"::error::ID mismatch!")
            print(f"  PR entry id: {pr_id}")
            print(f"  Manifest id: {manifest_id}")
            sys.exit(1)

        if manifest_version != pr_version:
            print(f"::error::Version mismatch!")
            print(f"  PR entry version: {pr_version}")
            print(f"  Manifest version: {manifest_version}")
            sys.exit(1)

        print(f"✅ Artifact content verification passed: {manifest_id}@{manifest_version}")

        # 验证 manifest 中有 functions 定义
        functions = manifest_data.get('functions', [])
        if not functions:
            print("::warning::No functions defined in prefab-manifest.json")
        else:
            print(f"Found {len(functions)} function(s) in manifest:")
            for func in functions:
                func_name = func.get('name', 'unknown')
                print(f"  - {func_name}")

        # 清理临时文件
        shutil.rmtree(temp_dir)
        artifact_path.unlink()
        print("✅ Cleaned up temporary files")

    except FileNotFoundError as e:
        print(f"::error::File not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"::error::Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
