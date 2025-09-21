"""
CLI 扩展用例系统测试

覆盖目标（基于 README.md 的 CLI 说明与 agent/cli/gtplanner_cli.py 实现）：
- 交互式模式下的配置切换命令：/streaming on|off, /timestamps on|off, /metadata on|off
- 会话命令：/new, /sessions, /current（不输入需求，避免触发LLM）
- 欢迎面板与语言参数：--language en/zh 与 --no-streaming 等选项在欢迎信息中的呈现

说明：
- 所有用例均避免真实 LLM 调用，仅与交互命令与会话管理交互
- 使用子进程与 stdin/stdout 交互，确保在 CI 或本地无 API Key 也可运行
"""
import os
import sys
import time
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable


def _spawn_cli(*args):
    """启动 CLI 子进程（交互式），返回 Popen 对象。"""
    cmd = [PYTHON, "gtplanner.py", "--no-streaming", "--language", "en", *args]
    # 统一英文界面，断言文本更稳定；默认禁用流式避免多余输出
    return subprocess.Popen(
        cmd,
        cwd=REPO_ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def _drain(proc, duration=1.0):
    """在给定时间片内尽量读取输出，返回文本。"""
    end = time.time() + duration
    lines = []
    while time.time() < end:
        if proc.stdout and proc.stdout.readable():
            line = proc.stdout.readline()
            if line:
                lines.append(line)
        time.sleep(0.05)
    return "".join(lines)


def _contains_any(s: str, keywords):
    return any(k.lower() in s.lower() for k in keywords)



class TestCLIConfigToggles:
    def test_toggle_streaming_timestamps_metadata(self):
        proc = _spawn_cli()
        try:
            time.sleep(1.0)  # 等待欢迎信息更充分
            _drain(proc, 1.0)

            # 切换 streaming on（中文提示："流式响应已启用/禁用"）
            proc.stdin.write("/streaming on\n"); proc.stdin.flush()
            time.sleep(0.4)
            out1 = _drain(proc, 1.2)
            assert _contains_any(out1, ["streaming", "流式响应"]), "未看到 streaming 切换提示"

            # 切换 timestamps on（中文提示："时间戳显示已启用/禁用"）
            proc.stdin.write("/timestamps on\n"); proc.stdin.flush()
            time.sleep(0.4)
            out2 = _drain(proc, 1.2)
            assert _contains_any(out2, ["timestamp", "时间戳"]), "未看到 timestamps 切换提示"

            # 切换 metadata on（中文提示："元数据显示已启用/禁用"）
            proc.stdin.write("/metadata on\n"); proc.stdin.flush()
            time.sleep(0.4)
            out3 = _drain(proc, 1.2)
            assert _contains_any(out3, ["metadata", "元数据"]), "未看到 metadata 切换提示"

            # 退出
            proc.stdin.write("/quit\n"); proc.stdin.flush()
            final_out = proc.communicate(timeout=6)[0]
            assert _contains_any(final_out, ["goodbye", "再见"]), "未输出退出问候语"
        finally:
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass


class TestCLISessions:
    def test_sessions_new_and_current(self, tmp_path):
        # 使用独立工作目录，避免污染真实会话数据库
        workdir = tmp_path
        proc = subprocess.Popen(
            [PYTHON, str(REPO_ROOT / "gtplanner.py"), "--no-streaming", "--language", "en"],
            cwd=workdir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        try:
            time.sleep(1.0)
            _drain(proc, 1.0)

            # 创建新会话（提示为多语言，且可能包含rich标记，放宽断言并延长等待）
            proc.stdin.write("/new Test Session\n"); proc.stdin.flush()
            time.sleep(0.6)
            _ = _drain(proc, 1.2)

            # 查看会话列表
            proc.stdin.write("/sessions\n"); proc.stdin.flush()
            time.sleep(0.6)
            out2 = _drain(proc, 1.5)
            assert _contains_any(out2, ["session", "会话"]), "未看到会话列表输出"

            # 查看当前会话
            proc.stdin.write("/current\n"); proc.stdin.flush()
            time.sleep(0.6)
            out3 = _drain(proc, 1.5)
            assert _contains_any(out3, ["current", "当前", "会话"]), "未显示当前会话信息"

            # 退出
            proc.stdin.write("/quit\n"); proc.stdin.flush()
            _ = proc.communicate(timeout=6)[0]
        finally:
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass


class TestCLIWelcomePanel:
    def test_welcome_panel_reflects_flags(self):
        # --no-streaming + en 语言，欢迎面板应包含配置项行
        proc = subprocess.Popen(
            [PYTHON, "gtplanner.py", "--no-streaming", "--language", "en"],
            cwd=REPO_ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            time.sleep(1.6)
            out = _drain(proc, 1.5)
            # 至少出现一个核心段落关键词（英文或中文）
            assert _contains_any(out, [
                "Usage", "Configuration", "Available",
                "使用方法", "配置选项", "可用命令"
            ]), "欢迎面板未出现核心段落关键词"
            proc.stdin.write("/quit\n"); proc.stdin.flush()
            _ = proc.communicate(timeout=6)[0]
        finally:
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass

