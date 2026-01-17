#!/usr/bin/env python3
"""
预制件索引构建脚本（用于 CI/CD）

适配 FAISS 向量服务的 API 接口。

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
# 注意：预制件使用 gtplanner_prefabs，设计文档使用 gtplanner_designs
DEFAULT_BUSINESS_TYPE = "gtplanner_prefabs"
DEFAULT_TIMEOUT = 30


def check_vector_service_available(vector_service_url: str) -> bool:
    """检查向量服务是否可用"""
    try:
        response = requests.get(f"{vector_service_url}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def convert_prefabs_to_documents(prefabs: List[Dict]) -> List[str]:
    """
    将预制件列表转换为向量服务的文档内容格式

    Args:
        prefabs: 预制件对象列表

    Returns:
        文档内容字符串列表（每个预制件一个文档）
    """
    documents = []
    for prefab in prefabs:
        # 构建标签字符串
        tags = prefab.get("tags", [])
        tags_str = ", ".join(tags) if tags else ""

        # 构建预制件信息
        prefab_info = {
            "id": prefab["id"],
            "name": prefab["name"],
            "description": prefab["description"],
            "tags": tags_str,
            "version": prefab["version"],
            "author": prefab["author"],
            "repo_url": prefab["repo_url"]
        }

        # 转换为JSON字符串（每个预制件独立）
        documents.append(json.dumps(prefab_info, ensure_ascii=False))

    return documents


def call_vector_service_add(
    vector_service_url: str,
    business_type: str,
    documents: List[str],
    timeout: int
) -> Dict[str, Any]:
    """
    调用向量服务的 /add 接口添加文档

    Args:
        vector_service_url: 向量服务地址
        business_type: 业务类型标识符
        documents: 文档内容列表
        timeout: 请求超时时间

    Returns:
        添加结果
    """
    # 将所有文档合并为一个字符串，使用预制件专用分隔符
    content = "\n\n>>>PREFAB<<<\n\n".join(documents)

    add_request = {
        "content": content,
        "businesstype": business_type,
        "chunk_size": 2000,   # Maximum allowed by vector service
        "chunk_overlap": 200   # 10% overlap for context
    }

    response = requests.post(
        f"{vector_service_url}/add",
        json=add_request,
        timeout=timeout,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        result = response.json()
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
    print(f"🔨 Converting prefabs to document format...")
    start_time = time.time()

    documents = convert_prefabs_to_documents(prefabs)
    print(f"📝 Converted {len(documents)} prefab documents")

    # 计算总字符数
    total_chars = sum(len(doc) for doc in documents)
    print(f"📝 Total content length: {total_chars} characters")

    # 4. 添加到向量服务
    try:
        print(f"🔨 Adding documents to vector service...")
        result = call_vector_service_add(
            vector_service_url=vector_service_url,
            business_type=DEFAULT_BUSINESS_TYPE,
            documents=documents,
            timeout=DEFAULT_TIMEOUT
        )

        elapsed_time = time.time() - start_time

        # 5. 输出结果
        print(f"\n✅ Index build completed successfully!")
        print(f"   Business Type: {DEFAULT_BUSINESS_TYPE}")
        print(f"   Prefab Count: {len(prefabs)}")
        print(f"   Elapsed Time: {round(elapsed_time, 2)}s")

        # 输出详细结果（JSON 格式，便于 CI/CD 解析）
        print(f"\n📊 Build Result:")
        build_result = {
            "success": True,
            "business_type": DEFAULT_BUSINESS_TYPE,
            "prefab_count": len(prefabs),
            "document_count": len(documents),
            "content_length": total_chars,
            "elapsed_time": round(elapsed_time, 2),
            "vector_service_url": vector_service_url,
            "result": result
        }
        print(json.dumps(build_result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"❌ Failed to build index: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Build prefab index for GTPlanner (FAISS Vector Service)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build index with vector service URL
  python build_index.py --vector-service-url http://192.168.136.224:8003

  # Build index with custom input file
  python build_index.py --vector-service-url http://192.168.136.224:8003 \\
    --input /path/to/community-prefabs.json

  # Use environment variable for vector service URL
  export VECTOR_SERVICE_URL=http://192.168.136.224:8003
  python build_index.py
        """
    )

    parser.add_argument(
        "--vector-service-url",
        help="Vector service URL (e.g., http://192.168.136.224:8003)",
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
