#!/usr/bin/env python3
"""
预制件索引构建脚本（用于 CI/CD）

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
from pathlib import Path


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

    with open(input_json) as f:
        prefabs = json.load(f)

    print(f"📦 Loaded {len(prefabs)} prefabs from {input_json.name}")

    # 2. 添加 GTPlanner 到 Python path（以便导入模块）
    gtplanner_root = input_json.parent.parent.parent
    sys.path.insert(0, str(gtplanner_root))

    try:
        from gtplanner.agent.utils.prefab_indexer import PrefabIndexer
    except ImportError as e:
        print(f"❌ Failed to import PrefabIndexer: {e}")
        print(f"   Make sure gtplanner package is installed or accessible")
        sys.exit(1)

    # 3. 构建索引
    try:
        indexer = PrefabIndexer(vector_service_url=vector_service_url)

        # 检查向量服务是否可用
        if not indexer.check_vector_service_available():
            print(f"❌ Vector service is not available at {vector_service_url}")
            print(f"   Please check the service URL and network connectivity")
            sys.exit(1)

        print(f"✅ Vector service is available")

        # 构建索引（强制重建）
        print(f"🔨 Building index...")
        result = indexer.build_index(
            json_path=str(input_json),
            force_reindex=True
        )

        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            print(f"❌ Index build failed: {error_msg}")
            sys.exit(1)

        # 4. 输出结果
        print(f"\n✅ Index build completed successfully!")
        print(f"   Index Name: {result['index_name']}")
        print(f"   Indexed Count: {result['indexed_count']}")
        print(f"   Elapsed Time: {result['elapsed_time']}s")

        # 输出详细结果（JSON 格式，便于 CI/CD 解析）
        print(f"\n📊 Build Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

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
