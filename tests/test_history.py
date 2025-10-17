#!/usr/bin/env python3
"""
测试 prompt_toolkit 历史记录功能的简单脚本
"""
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.formatted_text import HTML

# 创建带历史记录的 session
history_file = Path.home() / ".gtplanner_history_test"
session = PromptSession(history=FileHistory(str(history_file)))

print("🧪 GTPlanner 历史记录功能测试")
print("=" * 50)
print("✨ 请输入一些命令来测试历史记录功能：")
print("   - 使用 ⬆️ ⬇️ 键来浏览历史命令")
print("   - 输入 'quit' 退出")
print("=" * 50)
print()

while True:
    try:
        # 带彩色的提示符
        prompt_text = HTML('<ansiblue><b>Test</b></ansiblue> &gt; ')
        user_input = session.prompt(prompt_text).strip()

        if not user_input:
            continue

        if user_input.lower() == 'quit':
            print("👋 再见！")
            break

        print(f"📝 你输入了: {user_input}")

    except KeyboardInterrupt:
        print("\n⚠️  按 Ctrl+C 中断，输入 'quit' 退出")
    except EOFError:
        print("\n👋 再见！")
        break

print(f"\n✅ 历史记录已保存到: {history_file}")
print("💡 下次运行时可以用 ⬆️ ⬇️ 键查看历史命令")
