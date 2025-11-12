import logging
from .evaluator_core import BenchmarkEvaluator
from .test_case import TestCase

# 初始化日志（示例专用，避免与核心逻辑冲突）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    # 1. 初始化评估器
    evaluator = BenchmarkEvaluator()

    # 2. 创建并保存示例用例
    ecommerce_case = TestCase(
        case_id="sample_ecommerce",
        requirements="创建一个电子商务网站，支持用户注册、商品浏览、购物车和支付功能。需要考虑安全性和性能。",
        expected_features=["用户认证系统", "商品管理模块", "购物车功能", "支付集成", "安全措施", "性能优化"]
    )
    evaluator.save_test_case(ecommerce_case)

    # 3. 模拟旧版本规划函数（v1.0）
    def planner_v1(requirements: str) -> str:
        return f"""# 电子商务网站规划
## 1. 项目概述
根据需求，构建全功能电子商务平台。
## 2. 核心功能
- 用户认证：注册、登录、权限管理
- 商品管理：展示、分类、搜索
- 购物车：添加、修改、删除
- 支付：支持多种方式
## 3. 技术考虑
- 安全：数据加密、防SQL注入
- 性能：数据库索引、缓存
## 4. 实施步骤
1. 搭架构 2. 做认证 3. 开发商品 4. 集成支付 5. 测试
"""

    # 4. 运行旧版本基准测试
    evaluator.run_benchmark(planner_v1, "v1.0")

    # 5. 模拟新版本规划函数（v1.1，优化后）
    def planner_v2(requirements: str) -> str:
        return f"""# 电子商务网站规划
## 1. 项目概述
构建注重用户体验和安全性的全功能电子商务平台。
## 2. 核心功能
- 用户认证：注册、登录、密码重置、权限管理
- 商品管理：展示、分类、搜索、评价系统
- 购物车：添加/修改/删除/保存
- 支付：多方式支持+发票生成
## 3. 技术考虑
- 安全：加密、防SQL注入、XSS/CSRF防护
- 性能：索引、缓存、CDN集成
- 可扩展：模块化设计
## 4. 实施步骤
1. 搭架构+开发环境 2. 实现认证 3. 开发商品 4. 集成支付 5. 全面测试 6. 部署监控
"""

    # 6. 运行新版本基准测试
    evaluator.run_benchmark(planner_v2, "v1.1")

    # 7. 对比两个版本并生成报告
    comparison = evaluator.compare_versions("v1.0", "v1.1")
    if comparison:
        report = evaluator.generate_evaluation_report(comparison)
        print("="*50)
        print(report)
        print("="*50)


if __name__ == "__main__":
    main()