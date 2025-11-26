#!/usr/bin/env python3
"""
预制件索引构建脚本（用于 CI/CD）

独立脚本，不依赖 gtplanner 或 pocketflow 包。
当 community-prefabs.json 更新时，通过 GitHub Actions 调用此脚本
将预制件数据推送到向量服务建立索引。

用法:
    python build_index.py --vector-service-url <URL> [--input <JSON_PATH>]

环境变量:
    VECTOR_SERVICE_URL: 向量服务地址（可选，优先级低于命令行参数）
"""

import argparse
import json
import sys
import os
import time
import requests
from pathlib import Path
from typing import List, Dict, Any


# 默认配置
DEFAULT_INDEX_NAME = "document_gtplanner_prefabs"
DEFAULT_VECTOR_FIELD = "combined_text"
DEFAULT_VECTOR_DIMENSION = 1024
DEFAULT_TIMEOUT = 30


def check_vector_service_available(vector_service_url: str) -> bool:
    """检查向量服务是否可用"""
    try:
        response = requests.get(f"{vector_service_url}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def convert_prefab_to_document(prefab: Dict) -> Dict[str, Any]:
    """
    将预制件转换为向量服务的文档格式

    Args:
        prefab: 预制件对象（从 community-prefabs.json）

    Returns:
        文档对象
    """
    # 构建标签字符串
    tags = prefab.get("tags", [])
    tags_str = ", ".join(tags) if tags else ""

    # 构建组合文本（用于 embedding）
    combined_text = f"{prefab['name']} {prefab['description']}"
    if tags_str:
        combined_text += f" {tags_str}"

    # 构建 artifact URL
    repo_url = prefab["repo_url"].rstrip('/')
    version = prefab["version"]
    prefab_id = prefab["id"]
    artifact_url = f"{repo_url}/releases/download/v{version}/{prefab_id}-{version}.whl"

    # 返回文档对象
    document = {
        "id": prefab["id"],
        "type": "PREFAB",
        "summary": prefab["name"],
        "description": prefab["description"],
        "tags": tags_str,
        "combined_text": combined_text,
        # 元数据
        "version": prefab["version"],
        "author": prefab["author"],
        "repo_url": prefab["repo_url"],
        "artifact_url": artifact_url,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    return document


def call_vector_service_index(
    vector_service_url: str,
    index_name: str,
    documents: List[Dict],
    vector_field: str,
    force_reindex: bool,
    timeout: int
) -> Dict[str, Any]:
    """
    调用向量服务建立索引

    步骤：
    1. 创建索引（如果需要）
    2. 添加文档

    Args:
        vector_service_url: 向量服务地址
        index_name: 索引名称
        documents: 文档列表
        vector_field: 向量字段名
        force_reindex: 是否强制重建
        timeout: 请求超时时间

    Returns:
        索引结果
    """
    # 1. 如果强制重建，先清空索引
    if force_reindex:
        try:
            requests.delete(
                f"{vector_service_url}/index/{index_name}/clear",
                timeout=timeout
            )
            print(f"🗑️  已清空旧索引")
        except Exception as e:
            print(f"⚠️  清空索引失败（可能索引不存在）: {e}")

    # 2. 创建/确保索引存在
    create_index_request = {
        "vector_field": vector_field,
        "vector_dimension": DEFAULT_VECTOR_DIMENSION,
        "description": f"预制件索引: {index_name}"
    }

    response = requests.put(
        f"{vector_service_url}/index/{index_name}",
        json=create_index_request,
        timeout=timeout,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code != 200:
        error_msg = f"创建索引失败: {response.status_code}, {response.text}"
        raise RuntimeError(error_msg)

    print(f"✅ 索引已就绪: {index_name}")

    # 3. 添加文档
    create_docs_request = {
        "documents": documents,
        "vector_field": vector_field,
        "index": index_name
    }

    response = requests.post(
        f"{vector_service_url}/documents",
        json=create_docs_request,
        timeout=timeout,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 已添加 {result.get('count', 0)} 个文档到索引: {index_name}")
        return result
    else:
        error_msg = f"添加文档失败: {response.status_code}, {response.text}"
        raise RuntimeError(error_msg)


def build_index(vector_service_url: str, input_json: Path):
    """
    构建预制件索引

    Args:
        vector_service_url: 向量服务地址
        input_json: community-prefabs.json 路径
    """
    print(f"🚀 Starting prefab index build")
    print(f"   Vector Service: {vector_service_url}")
    print(f"   Input JSON: {input_json}")

    # 1. 验证输入文件
    if not input_json.exists():
        print(f"❌ Input file not found: {input_json}")
        sys.exit(1)

    with open(input_json, 'r', encoding='utf-8') as f:
        prefabs = json.load(f)

    print(f"📦 Loaded {len(prefabs)} prefabs from {input_json.name}")

    # 2. 检查向量服务是否可用
    if not check_vector_service_available(vector_service_url):
        print(f"❌ Vector service is not available at {vector_service_url}")
        print(f"   Please check the service URL and network connectivity")
        sys.exit(1)

    print(f"✅ Vector service is available")

    # 3. 转换为文档格式
    print(f"🔨 Converting prefabs to documents...")
    start_time = time.time()

    documents = []
    for prefab in prefabs:
        try:
            doc = convert_prefab_to_document(prefab)
            documents.append(doc)
        except Exception as e:
            print(f"⚠️  Failed to convert prefab {prefab.get('id')}: {e}")
            continue

    print(f"📝 Converted {len(documents)} documents")

    # 4. 构建索引
    try:
        print(f"🔨 Building index...")
        result = call_vector_service_index(
            vector_service_url=vector_service_url,
            index_name=DEFAULT_INDEX_NAME,
            documents=documents,
            vector_field=DEFAULT_VECTOR_FIELD,
            force_reindex=True,
            timeout=DEFAULT_TIMEOUT
        )

        elapsed_time = time.time() - start_time

        # 5. 输出结果
        print(f"\n✅ Index build completed successfully!")
        print(f"   Index Name: {DEFAULT_INDEX_NAME}")
        print(f"   Indexed Count: {len(documents)}")
        print(f"   Elapsed Time: {round(elapsed_time, 2)}s")

        # 输出详细结果（JSON 格式，便于 CI/CD 解析）
        print(f"\n📊 Build Result:")
        build_result = {
            "success": True,
            "index_name": DEFAULT_INDEX_NAME,
            "indexed_count": len(documents),
            "elapsed_time": round(elapsed_time, 2),
            "vector_service_url": vector_service_url,
            **result
        }
        print(json.dumps(build_result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Failed to build index: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Build prefab index for GTPlanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build index with vector service URL
  python build_index.py --vector-service-url http://localhost:8000

  # Build index with custom input file
  python build_index.py --vector-service-url http://localhost:8000 \\
    --input /path/to/community-prefabs.json

  # Use environment variable for vector service URL
  export VECTOR_SERVICE_URL=http://localhost:8000
  python build_index.py
        """
    )

    parser.add_argument(
        "--vector-service-url",
        help="Vector service URL (e.g., http://localhost:8000)",
        default=os.getenv("VECTOR_SERVICE_URL")
    )

    parser.add_argument(
        "--input",
        help="Path to community-prefabs.json (default: auto-detect)",
        default=None
    )

    args = parser.parse_args()

    # 验证参数
    if not args.vector_service_url:
        print("❌ Error: --vector-service-url is required")
        print("   Either provide it via command line or set VECTOR_SERVICE_URL environment variable")
        parser.print_help()
        sys.exit(1)

    # 确定输入文件路径
    if args.input:
        input_json = Path(args.input)
    else:
        # 自动定位：假设脚本在 prefabs/releases/scripts/ 目录下
        script_dir = Path(__file__).parent
        input_json = script_dir.parent / "community-prefabs.json"

    # 构建索引
    build_index(args.vector_service_url, input_json)


if __name__ == "__main__":
    main()
