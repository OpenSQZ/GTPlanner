#!/usr/bin/env python3
"""
检查 artifact_url 的可达性（URL 自动构造）
"""
import json
import sys
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

        # 构造 artifact URL
        artifact_url = construct_artifact_url(changed_entry)
        print(f"构造的 artifact_url: {artifact_url}")
        print(f"  规则: {{repo_url}}/releases/download/v{{version}}/{{id}}-{{version}}.whl")

        # 发送 HEAD 请求检查 URL 可达性
        try:
            response = requests.head(artifact_url, allow_redirects=True, timeout=30)

            if response.status_code < 200 or response.status_code >= 300:
                print(f"::error::artifact_url returned status code {response.status_code}")
                print(f"::error::请确保 GitHub Release 存在且文件名符合规范")
                print(f"URL: {artifact_url}")
                sys.exit(1)

            # 检查 Content-Type (可选但推荐)
            content_type = response.headers.get('Content-Type', '')
            if 'application/zip' not in content_type and 'application/octet-stream' not in content_type and 'binary' not in content_type:
                print(f"::warning::artifact_url Content-Type is '{content_type}', expected binary/zip format")

            # 检查 Content-Length
            content_length = response.headers.get('Content-Length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                print(f"Artifact size: {size_mb:.2f} MB")

                # 警告过大的文件
                if size_mb > 100:
                    print(f"::warning::Artifact size is {size_mb:.2f} MB, which is quite large")

            print(f"✅ artifact_url is accessible (HTTP {response.status_code})")

        except requests.RequestException as e:
            print(f"::error::Failed to access artifact_url: {e}")
            print(f"URL: {artifact_url}")
            sys.exit(1)

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
