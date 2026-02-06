"""
GTPlanner Skill E2E 测试

测试 skill 的工具调用和工作流程。
"""
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSkillToolDefinitions:
    """测试工具定义"""

    def test_get_agent_function_definitions(self):
        """测试获取工具定义列表"""
        from agent.function_calling.agent_tools import get_agent_function_definitions

        tools = get_agent_function_definitions()
        assert isinstance(tools, list), "应返回工具列表"
        assert len(tools) >= 3, "至少应有 3 个工具 (short_planning, tool_recommend, design)"

    def test_tool_names(self):
        """测试工具名称"""
        from agent.function_calling.agent_tools import get_agent_function_definitions

        tools = get_agent_function_definitions()
        tool_names = [t["function"]["name"] for t in tools]

        # 必需工具
        assert "short_planning" in tool_names, "应包含 short_planning 工具"
        assert "tool_recommend" in tool_names, "应包含 tool_recommend 工具"
        assert "design" in tool_names, "应包含 design 工具"

    def test_short_planning_definition(self):
        """测试 short_planning 工具定义"""
        from agent.function_calling.agent_tools import get_tool_by_name

        tool = get_tool_by_name("short_planning")
        assert tool is not None, "应能获取 short_planning 工具定义"

        params = tool["function"]["parameters"]
        assert "user_requirements" in params["properties"], "应有 user_requirements 参数"
        assert "planning_stage" in params["properties"], "应有 planning_stage 参数"
        assert "improvement_points" in params["properties"], "应有 improvement_points 参数"

    def test_design_definition(self):
        """测试 design 工具定义"""
        from agent.function_calling.agent_tools import get_tool_by_name

        tool = get_tool_by_name("design")
        assert tool is not None, "应能获取 design 工具定义"

        params = tool["function"]["parameters"]
        assert "user_requirements" in params["properties"], "应有 user_requirements 参数"
        assert "design_mode" in params["properties"], "应有 design_mode 参数"

        # 验证 design_mode 枚举值
        design_mode_enum = params["properties"]["design_mode"].get("enum", [])
        assert "quick" in design_mode_enum, "design_mode 应支持 quick"
        assert "deep" in design_mode_enum, "design_mode 应支持 deep"

    def test_tool_recommend_definition(self):
        """测试 tool_recommend 工具定义"""
        from agent.function_calling.agent_tools import get_tool_by_name

        tool = get_tool_by_name("tool_recommend")
        assert tool is not None, "应能获取 tool_recommend 工具定义"

        params = tool["function"]["parameters"]
        assert "query" in params["properties"], "应有 query 参数"
        assert "top_k" in params["properties"], "应有 top_k 参数"


class TestSkillArgumentValidation:
    """测试参数验证"""

    def test_validate_short_planning_arguments(self):
        """测试 short_planning 参数验证"""
        from agent.function_calling.agent_tools import validate_tool_arguments

        # 缺少必需参数
        result = validate_tool_arguments("short_planning", {})
        assert not result["valid"], "缺少 user_requirements 应验证失败"
        assert any("user_requirements" in e for e in result["errors"])

        # 完整参数
        result = validate_tool_arguments(
            "short_planning", {"user_requirements": "测试需求"}
        )
        assert result["valid"], "完整参数应验证通过"

    def test_validate_design_arguments(self):
        """测试 design 参数验证"""
        from agent.function_calling.agent_tools import validate_tool_arguments

        # 缺少必需参数
        result = validate_tool_arguments("design", {})
        assert not result["valid"], "缺少必需参数应验证失败"

        # 完整参数
        result = validate_tool_arguments(
            "design", {"user_requirements": "测试需求", "design_mode": "quick"}
        )
        assert result["valid"], "完整参数应验证通过"

    def test_validate_unknown_tool(self):
        """测试未知工具验证"""
        from agent.function_calling.agent_tools import validate_tool_arguments

        result = validate_tool_arguments("unknown_tool", {})
        assert not result["valid"], "未知工具应验证失败"
        assert any("Unknown tool" in e for e in result["errors"])


class TestSkillToolExecution:
    """测试工具执行"""

    @pytest.mark.asyncio
    async def test_short_planning_missing_requirements(self):
        """测试 short_planning 缺少需求时的行为"""
        from agent.function_calling.agent_tools import execute_agent_tool

        shared = {}
        result = await execute_agent_tool(
            "short_planning", {"planning_stage": "initial"}, shared
        )

        assert not result["success"], "缺少 user_requirements 应执行失败"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_short_planning_invalid_stage(self):
        """测试 short_planning 无效阶段参数"""
        from agent.function_calling.agent_tools import execute_agent_tool

        shared = {}
        result = await execute_agent_tool(
            "short_planning",
            {"user_requirements": "测试需求", "planning_stage": "invalid"},
            shared,
        )

        assert not result["success"], "无效 planning_stage 应执行失败"
        assert "initial" in result["error"] or "technical" in result["error"]

    @pytest.mark.asyncio
    async def test_design_missing_short_planning(self):
        """测试 design 缺少 short_planning 结果时的行为"""
        from agent.function_calling.agent_tools import execute_agent_tool

        shared = {}  # 空的 shared，没有 short_planning 结果
        result = await execute_agent_tool(
            "design",
            {"user_requirements": "测试需求", "design_mode": "quick"},
            shared,
        )

        assert not result["success"], "缺少 short_planning 结果应执行失败"
        # 错误信息可能是 "shared context is required" 或 "short_planning results are required"
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_design_invalid_mode(self):
        """测试 design 无效设计模式"""
        from agent.function_calling.agent_tools import execute_agent_tool

        shared = {"short_planning": "测试规划结果"}
        result = await execute_agent_tool(
            "design",
            {"user_requirements": "测试需求", "design_mode": "invalid"},
            shared,
        )

        assert not result["success"], "无效 design_mode 应执行失败"
        assert "quick" in result["error"] or "deep" in result["error"]

    @pytest.mark.asyncio
    async def test_tool_recommend_missing_query(self):
        """测试 tool_recommend 缺少查询时的行为"""
        from agent.function_calling.agent_tools import execute_agent_tool

        shared = {}
        result = await execute_agent_tool("tool_recommend", {}, shared)

        assert not result["success"], "缺少 query 应执行失败"
        assert "query" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        """测试执行未知工具"""
        from agent.function_calling.agent_tools import execute_agent_tool

        shared = {}
        result = await execute_agent_tool("unknown_tool", {}, shared)

        assert not result["success"], "未知工具应执行失败"
        assert "Unknown tool" in result["error"]


class TestSkillPluginStructure:
    """测试 Plugin 结构"""

    def test_plugin_json_exists(self):
        """测试 plugin.json 文件存在"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        plugin_json = os.path.join(project_root, ".claude", "plugin.json")
        assert os.path.exists(plugin_json), "plugin.json 文件应存在"

    def test_plugin_json_valid(self):
        """测试 plugin.json 内容有效"""
        import json

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        plugin_json = os.path.join(project_root, ".claude", "plugin.json")

        with open(plugin_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "name" in data, "plugin.json 应包含 name"
        assert "version" in data, "plugin.json 应包含 version"
        assert "description" in data, "plugin.json 应包含 description"
        assert data["name"] == "gtplanner", "plugin name 应为 gtplanner"

    def test_skill_md_exists(self):
        """测试 SKILL.md 文件存在"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        skill_md = os.path.join(project_root, ".claude", "skills", "gtplanner", "SKILL.md")
        assert os.path.exists(skill_md), "SKILL.md 文件应存在"

    def test_skill_md_has_frontmatter(self):
        """测试 SKILL.md 包含 frontmatter"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        skill_md = os.path.join(project_root, ".claude", "skills", "gtplanner", "SKILL.md")

        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()

        assert content.startswith("---"), "SKILL.md 应以 frontmatter 开始"
        assert "description:" in content, "SKILL.md 应包含 description"
        assert "allowed-tools:" in content, "SKILL.md 应包含 allowed-tools"

    def test_references_exist(self):
        """测试 references 文档存在"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        references_dir = os.path.join(project_root, ".claude", "skills", "gtplanner", "references")

        expected_files = ["tools.md", "workflow.md", "examples.md"]
        for filename in expected_files:
            filepath = os.path.join(references_dir, filename)
            assert os.path.exists(filepath), f"references/{filename} 应存在"

    def test_command_exists(self):
        """测试初始化命令存在"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        command_file = os.path.join(project_root, ".claude", "commands", "gtplanner-init.md")
        assert os.path.exists(command_file), "gtplanner-init.md 命令应存在"

    def test_command_has_frontmatter(self):
        """测试命令文件包含 frontmatter"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        command_file = os.path.join(project_root, ".claude", "commands", "gtplanner-init.md")

        with open(command_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert content.startswith("---"), "命令文件应以 frontmatter 开始"
        assert "description:" in content, "命令文件应包含 description"
        assert "allowed-tools:" in content, "命令文件应包含 allowed-tools"


class TestSkillMultilingual:
    """测试多语言支持"""

    def test_skill_trigger_words_chinese(self):
        """测试中文触发词在 SKILL.md 中"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        skill_md = os.path.join(project_root, ".claude", "skills", "gtplanner", "SKILL.md")

        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()

        trigger_words = ["PRD", "项目规划", "架构设计", "技术方案", "设计文档"]
        for word in trigger_words:
            assert word in content, f"触发词 '{word}' 应在 SKILL.md 中"

    def test_skill_language_support(self):
        """测试语言支持说明"""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        skill_md = os.path.join(project_root, ".claude", "skills", "gtplanner", "SKILL.md")

        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()

        languages = ["zh", "en", "ja", "es", "fr"]
        for lang in languages:
            assert lang in content, f"语言代码 '{lang}' 应在 SKILL.md 中提及"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
