"""
预制件推荐系统测试

测试双模式检索功能：
1. 本地模糊搜索（降级模式）
2. 向量语义检索（主模式）
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_local_search():
    """测试本地模糊搜索功能"""
    print("=" * 60)
    print("测试 1: 本地模糊搜索 (降级模式)")
    print("=" * 60)
    
    from gtplanner.agent.utils.local_prefab_searcher import LocalPrefabSearcher
    
    searcher = LocalPrefabSearcher()
    
    # 测试场景
    test_cases = [
        {"query": "hello", "limit": 5},
        {"tags": ["example"], "limit": 5},
        {"query": "demo", "tags": ["example"], "limit": 3},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {test_case}")
        try:
            results = searcher.search(**test_case)
            print(f"✅ 找到 {len(results)} 个结果:")
            for j, prefab in enumerate(results, 1):
                print(f"  {j}. {prefab['name']} (ID: {prefab['id']})")
                print(f"     Tags: {prefab.get('tags', [])}")
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
    
    print("\n" + "=" * 60)


async def test_search_prefabs_tool():
    """测试 search_prefabs agent 工具"""
    print("=" * 60)
    print("测试 2: search_prefabs Agent 工具")
    print("=" * 60)
    
    from gtplanner.agent.function_calling.agent_tools import execute_agent_tool
    
    # 测试用例
    test_args = [
        {"query": "hello world"},
        {"tags": ["example", "demo"]},
        {"query": "test", "limit": 3},
    ]
    
    for i, args in enumerate(test_args, 1):
        print(f"\n测试用例 {i}: {args}")
        try:
            result = await execute_agent_tool("search_prefabs", args)
            if result.get("success"):
                prefabs = result["result"]["prefabs"]
                print(f"✅ 成功! 找到 {len(prefabs)} 个预制件:")
                for j, prefab in enumerate(prefabs[:3], 1):
                    print(f"  {j}. {prefab['name']} - {prefab['description'][:50]}...")
            else:
                print(f"❌ 失败: {result.get('error')}")
        except Exception as e:
            print(f"❌ 异常: {str(e)}")
    
    print("\n" + "=" * 60)


async def test_prefab_recommend_tool():
    """测试 prefab_recommend agent 工具（需要向量服务）"""
    print("=" * 60)
    print("测试 3: prefab_recommend Agent 工具 (需要向量服务)")
    print("=" * 60)
    
    from gtplanner.agent.function_calling.agent_tools import execute_agent_tool
    
    # 先检查向量服务是否可用
    from gtplanner.utils.config_manager import get_vector_service_config
    import requests
    
    vector_config = get_vector_service_config()
    vector_service_url = vector_config.get("base_url")
    
    if not vector_service_url:
        print("⚠️ 未配置向量服务，跳过此测试")
        print("   请设置 VECTOR_SERVICE_BASE_URL 环境变量或在 settings.toml 中配置")
        return
    
    try:
        response = requests.get(f"{vector_service_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"⚠️ 向量服务不可用 ({vector_service_url})")
            print("   此测试需要向量服务，将测试降级提示")
            
            # 测试降级提示
            test_args = {"query": "hello world example"}
            result = await execute_agent_tool("prefab_recommend", test_args)
            if not result.get("success"):
                print(f"✅ 正确返回降级提示: {result.get('error')}")
                if "suggestion" in result:
                    print(f"   建议: {result['suggestion']}")
            return
    except Exception as e:
        print(f"⚠️ 无法连接到向量服务: {str(e)}")
        return
    
    # 向量服务可用，执行真实测试
    print(f"✅ 向量服务可用: {vector_service_url}")
    
    test_args = {
        "query": "hello world example prefab",
        "top_k": 3,
        "use_llm_filter": False  # 先不使用LLM筛选以加快测试
    }
    
    print(f"\n测试用例: {test_args}")
    try:
        result = await execute_agent_tool("prefab_recommend", test_args)
        if result.get("success"):
            prefabs = result["result"]["recommended_prefabs"]
            search_mode = result["result"]["search_mode"]
            search_time = result["result"]["search_time_ms"]
            
            print(f"✅ 成功! 找到 {len(prefabs)} 个预制件 (模式: {search_mode}, 耗时: {search_time}ms):")
            for i, prefab in enumerate(prefabs, 1):
                score = prefab.get("score", 0)
                print(f"  {i}. {prefab['summary']} (相关性: {score:.3f})")
                print(f"     {prefab['description'][:80]}...")
        else:
            print(f"❌ 失败: {result.get('error')}")
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)


async def test_prefab_indexer():
    """测试预制件索引构建"""
    print("=" * 60)
    print("测试 4: 预制件索引构建")
    print("=" * 60)
    
    from gtplanner.agent.utils.prefab_indexer import PrefabIndexer
    
    indexer = PrefabIndexer()
    
    # 检查向量服务
    available = indexer.check_vector_service_available()
    print(f"向量服务状态: {'✅ 可用' if available else '❌ 不可用'}")
    
    if not available:
        print("⚠️ 向量服务不可用，跳过索引构建测试")
        return
    
    # 加载预制件
    try:
        prefabs = indexer.load_prefabs_from_json()
        print(f"✅ 加载了 {len(prefabs)} 个预制件")
        
        # 转换第一个预制件为文档格式
        if prefabs:
            doc = indexer.convert_prefab_to_document(prefabs[0])
            print(f"\n示例文档格式:")
            print(f"  ID: {doc['id']}")
            print(f"  名称: {doc['summary']}")
            print(f"  类型: {doc['type']}")
            print(f"  下载链接: {doc['artifact_url']}")
            
        # 可选：实际构建索引（需要向量服务）
        # 注意：这会实际调用向量服务，如果不需要可以注释掉
        # print("\n开始构建索引...")
        # result = indexer.build_index(force_reindex=True)
        # if result["success"]:
        #     print(f"✅ 索引构建成功:")
        #     print(f"   索引名: {result['index_name']}")
        #     print(f"   文档数: {result['indexed_count']}")
        #     print(f"   耗时: {result['elapsed_time']}秒")
        # else:
        #     print(f"❌ 索引构建失败: {result['error']}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)


async def main():
    """运行所有测试"""
    print("\n" + "🧪 预制件推荐系统测试套件" + "\n")
    
    # 测试 1: 本地模糊搜索
    await test_local_search()
    
    # 测试 2: search_prefabs 工具
    await test_search_prefabs_tool()
    
    # 测试 3: prefab_recommend 工具
    await test_prefab_recommend_tool()
    
    # 测试 4: 索引构建
    await test_prefab_indexer()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

