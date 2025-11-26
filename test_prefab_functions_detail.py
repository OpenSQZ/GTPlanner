#!/usr/bin/env python3
"""
测试预制件函数详情查询后置流程

测试场景：
1. 设计流程生成设计文档
2. 自动查询推荐预制件的函数详情
3. 生成预制件函数详情文档
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gtplanner.agent.subflows.design.flows.design_flow import DesignFlow


async def test_prefab_functions_detail_flow():
    """测试预制件函数详情查询流程"""

    print("=" * 80)
    print("测试：设计流程 + 预制件函数详情查询")
    print("=" * 80)

    # 构造测试数据
    shared = {
        "user_requirements": """
        我需要一个浏览器自动化系统，能够：
        1. 打开网页并自动填写表单
        2. 截图保存
        3. 提取页面数据
        """,
        "recommended_prefabs": [
            {
                "id": "browser-automation-agent",
                "version": "0.2.0",
                "name": "浏览器自动化代理",
                "description": "提供浏览器自动化能力，支持网页操作、数据提取等功能",
                "functions": [
                    {
                        "name": "navigate_and_extract",
                        "description": "导航到指定URL并提取数据"
                    },
                    {
                        "name": "fill_form",
                        "description": "填写网页表单"
                    }
                ]
            }
        ],
        "language": "zh"
    }

    # 创建设计流程
    design_flow = DesignFlow()

    print("\n📋 输入数据:")
    print(f"  - 用户需求: {shared['user_requirements'][:50]}...")
    print(f"  - 推荐预制件数量: {len(shared['recommended_prefabs'])}")
    print(f"  - 预制件函数数量: {len(shared['recommended_prefabs'][0]['functions'])}")

    try:
        print("\n🚀 开始执行设计流程...")
        result = await design_flow.run_async(shared)

        print("\n✅ 流程执行完成")
        print(f"  - 返回值: {result}")

        # 检查生成的文档
        if "agent_design_document" in shared:
            print(f"\n📄 设计文档已生成:")
            design_doc = shared["agent_design_document"]
            print(f"  - 长度: {len(design_doc)} 字符")
            print(f"  - 前100字符: {design_doc[:100]}...")

        # 检查预制件函数详情
        if "prefab_functions_details" in shared:
            print(f"\n📦 预制件函数详情已查询:")
            details = shared["prefab_functions_details"]
            print(f"  - 预制件数量: {len(details)}")
            for prefab in details:
                print(f"  - {prefab['name']} ({prefab['id']}@{prefab['version']})")
                print(f"    函数数量: {len(prefab['functions'])}")
                for func in prefab['functions']:
                    if 'error' in func:
                        print(f"      ❌ {func['name']}: {func['error']}")
                    else:
                        print(f"      ✅ {func['name']}: 查询成功")

        # 检查函数详情文档
        if "prefab_functions_document" in shared:
            print(f"\n📝 预制件函数详情文档已生成:")
            doc = shared["prefab_functions_document"]
            print(f"  - 长度: {len(doc)} 字符")
            print(f"  - 前200字符:")
            print("  " + "\n  ".join(doc[:200].split("\n")))

        # 检查系统消息
        if "system_messages" in shared:
            print(f"\n📬 系统消息:")
            for msg in shared["system_messages"]:
                print(f"  - [{msg['stage']}] {msg['status']}: {msg['message']}")

        print("\n" + "=" * 80)
        print("✅ 测试完成！")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_without_prefabs():
    """测试没有推荐预制件的场景"""

    print("\n" + "=" * 80)
    print("测试：设计流程（无推荐预制件）")
    print("=" * 80)

    shared = {
        "user_requirements": "构建一个简单的待办事项管理系统",
        "recommended_prefabs": [],  # 没有推荐预制件
        "language": "zh"
    }

    design_flow = DesignFlow()

    try:
        print("\n🚀 开始执行设计流程...")
        result = await design_flow.run_async(shared)

        print("\n✅ 流程执行完成")
        print(f"  - 返回值: {result}")

        # 应该跳过预制件函数详情查询
        if "prefab_functions_details" not in shared:
            print("  ✅ 正确跳过了预制件函数详情查询")
        else:
            print("  ⚠️  预制件函数详情查询未被跳过（不符合预期）")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_prefabs_without_functions():
    """测试推荐预制件没有函数列表的场景"""

    print("\n" + "=" * 80)
    print("测试：设计流程（推荐预制件无函数列表）")
    print("=" * 80)

    shared = {
        "user_requirements": "构建一个数据分析系统",
        "recommended_prefabs": [
            {
                "id": "data-analyzer",
                "version": "1.0.0",
                "name": "数据分析器",
                "description": "数据分析工具",
                # 没有 functions 字段
            }
        ],
        "language": "zh"
    }

    design_flow = DesignFlow()

    try:
        print("\n🚀 开始执行设计流程...")
        result = await design_flow.run_async(shared)

        print("\n✅ 流程执行完成")
        print(f"  - 返回值: {result}")

        # 应该跳过预制件函数详情查询
        if "prefab_functions_details" not in shared:
            print("  ✅ 正确跳过了预制件函数详情查询（无函数列表）")
        else:
            print("  ⚠️  预制件函数详情查询未被跳过（不符合预期）")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""

    print("\n" + "=" * 80)
    print("🧪 预制件函数详情查询流程测试套件")
    print("=" * 80)

    results = []

    # 测试1：正常流程（有推荐预制件和函数）
    print("\n[测试 1/3] 正常流程（有推荐预制件和函数）")
    results.append(await test_prefab_functions_detail_flow())

    # 测试2：没有推荐预制件
    print("\n[测试 2/3] 没有推荐预制件")
    results.append(await test_without_prefabs())

    # 测试3：推荐预制件没有函数列表
    print("\n[测试 3/3] 推荐预制件没有函数列表")
    results.append(await test_prefabs_without_functions())

    # 测试总结
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"  总计: {total} 个测试")
    print(f"  通过: {passed} 个")
    print(f"  失败: {failed} 个")

    if failed == 0:
        print("\n✅ 所有测试通过！")
        return 0
    else:
        print(f"\n❌ {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
