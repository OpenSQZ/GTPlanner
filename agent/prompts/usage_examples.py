"""
多语言提示词系统使用示例

展示如何使用新的多语言提示词管理系统，包括直接指定语言和自动检测。
"""

from agent.prompts import get_prompt, PromptTypes
from agent.prompts.text_manager import get_text, build_dynamic_content
from utils.language_detection import SupportedLanguage


def example_direct_language_specification():
    """示例：直接指定语言（推荐方式，性能更好）"""
    
    # 方式1：使用枚举指定语言
    system_prompt_zh = get_prompt(
        PromptTypes.System.ORCHESTRATOR_FUNCTION_CALLING,
        language=SupportedLanguage.CHINESE
    )
    
    system_prompt_en = get_prompt(
        PromptTypes.System.ORCHESTRATOR_FUNCTION_CALLING,
        language=SupportedLanguage.ENGLISH
    )
    
    # 方式2：使用字符串指定语言（更简洁）
    system_prompt_zh_str = get_prompt(
        PromptTypes.System.ORCHESTRATOR_FUNCTION_CALLING,
        language="zh"  # 直接使用字符串，不需要语言检测
    )
    
    system_prompt_en_str = get_prompt(
        PromptTypes.System.ORCHESTRATOR_FUNCTION_CALLING,
        language="en"  # 直接使用字符串，不需要语言检测
    )
    
    print("✅ 直接指定语言方式完成")


def example_formatted_prompts():
    """示例：带参数格式化的提示词"""
    
    # 短规划提示词，中文版本
    planning_prompt_zh = get_prompt(
        PromptTypes.Agent.SHORT_PLANNING_GENERATION,
        language="zh",
        req_content="创建一个YouTube视频总结器",
        tools_content="youtube_audio_fetch: 获取YouTube视频的音频\nASR_MCP: 将音频转换为文本",
        research_content="技术调研显示ASR技术已经成熟"
    )
    
    # 短规划提示词，英文版本
    planning_prompt_en = get_prompt(
        PromptTypes.Agent.SHORT_PLANNING_GENERATION,
        language="en",
        req_content="Create a YouTube video summarizer",
        tools_content="youtube_audio_fetch: Get YouTube video audio\nASR_MCP: Convert audio to text",
        research_content="Technical research shows ASR technology is mature"
    )
    
    print("✅ 格式化提示词完成")


def example_text_fragments():
    """示例：动态文本片段"""
    
    # 获取中文文本片段
    header_zh = get_text(
        PromptTypes.Common.PREVIOUS_PLANNING_HEADER,
        language="zh"
    )
    
    # 获取英文文本片段
    header_en = get_text(
        PromptTypes.Common.PREVIOUS_PLANNING_HEADER,
        language="en"
    )
    
    # 带参数的文本片段
    bullet_point_zh = get_text(
        PromptTypes.Common.BULLET_POINT,
        language="zh",
        content="这是一个改进点"
    )
    
    print(f"中文标题: {header_zh}")
    print(f"英文标题: {header_en}")
    print(f"中文列表项: {bullet_point_zh}")
    print("✅ 文本片段获取完成")


def example_dynamic_content_building():
    """示例：动态内容构建"""
    
    # 构建中文动态内容
    dynamic_content_zh = build_dynamic_content(
        user_requirements="创建一个AI助手",
        previous_planning="之前的规划内容",
        improvement_points=["提高响应速度", "增强准确性"],
        language="zh"
    )
    
    # 构建英文动态内容
    dynamic_content_en = build_dynamic_content(
        user_requirements="Create an AI assistant",
        previous_planning="Previous planning content",
        improvement_points=["Improve response speed", "Enhance accuracy"],
        language="en"
    )
    
    print("中文动态内容:")
    print(dynamic_content_zh)
    print("\n英文动态内容:")
    print(dynamic_content_en)
    print("✅ 动态内容构建完成")


def example_auto_detection():
    """示例：自动语言检测（仅在未指定语言时使用）"""
    
    # 当没有指定语言时，会根据用户输入自动检测
    prompt_auto_zh = get_prompt(
        PromptTypes.System.ORCHESTRATOR_FUNCTION_CALLING,
        user_input="我需要创建一个项目规划工具"  # 中文输入，会检测为中文
    )
    
    prompt_auto_en = get_prompt(
        PromptTypes.System.ORCHESTRATOR_FUNCTION_CALLING,
        user_input="I need to create a project planning tool"  # 英文输入，会检测为英文
    )
    
    print("✅ 自动语言检测完成")


def example_performance_comparison():
    """示例：性能对比"""
    import time
    
    # 直接指定语言（推荐）- 不需要语言检测
    start_time = time.time()
    for _ in range(100):
        get_prompt(
            PromptTypes.System.ORCHESTRATOR_FUNCTION_CALLING,
            language="zh"  # 直接指定，无需检测
        )
    direct_time = time.time() - start_time
    
    # 自动检测语言 - 需要语言检测
    start_time = time.time()
    for _ in range(100):
        get_prompt(
            PromptTypes.System.ORCHESTRATOR_FUNCTION_CALLING,
            user_input="我需要帮助"  # 需要检测语言
        )
    auto_time = time.time() - start_time
    
    print(f"直接指定语言耗时: {direct_time:.4f}秒")
    print(f"自动检测语言耗时: {auto_time:.4f}秒")
    print(f"性能提升: {((auto_time - direct_time) / auto_time * 100):.1f}%")
    print("✅ 性能对比完成")


if __name__ == "__main__":
    print("🚀 多语言提示词系统使用示例")
    print("=" * 50)
    
    example_direct_language_specification()
    print()
    
    example_formatted_prompts()
    print()
    
    example_text_fragments()
    print()
    
    example_dynamic_content_building()
    print()
    
    example_auto_detection()
    print()
    
    example_performance_comparison()
    print()
    
    print("🎉 所有示例执行完成！")
    print("\n💡 推荐使用方式：")
    print("1. 直接指定语言字符串（如 'zh', 'en'）- 性能最佳")
    print("2. 使用 SupportedLanguage 枚举 - 类型安全")
    print("3. 仅在必要时使用自动检测 - 适用于用户输入场景")
