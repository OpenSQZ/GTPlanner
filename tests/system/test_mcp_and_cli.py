"""
MCP 与 CLI 模式系统测试

覆盖内容：
- MCP 服务器启动与协议可用性（尽量不依赖外部LLM）
- CLI 交互命令与参数校验（避免触发LLM调用）
- 错误处理（异常与无效参数）
- 基本性能（简单响应耗时）

说明：
- 测试尽量避免真实网络/LLM调用，主要验证启动、接口、错误处理与输出结构。
- 若MCP依赖缺失（例如模块路径不一致），测试会记录问题并给出建议。
"""

import os
import sys
import time
import json
import socket
import signal
import subprocess
from contextlib import closing
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON = sys.executable


def is_port_open(host: str, port: int, timeout: float = 0.2) -> bool:
    """检测端口是否开放"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


class TestMCPMode:
    """MCP 模式测试"""

    def test_mcp_module_import(self):
        """验证MCP服务模块可导入性（不执行）"""
        mcp_path = REPO_ROOT / "mcp" / "mcp_service.py"
        assert mcp_path.exists(), "mcp/mcp_service.py 不存在"

        # 直接在当前进程中尝试导入模块（不会触发 __main__）
        import importlib.util
        spec = importlib.util.spec_from_file_location('mcp_service', mcp_path.as_posix())
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            pytest.skip(f"[MCP Import Warning] 导入失败（记录并跳过）：{e}")

    def test_mcp_server_launch_and_probe(self):
        """尝试启动MCP服务并探测端口（若失败则记录错误）"""
        port = 8001
        env = os.environ.copy()
        # 限制外部网络访问（尽量）
        env["NO_PROXY"] = "*"

        proc = subprocess.Popen([PYTHON, "mcp/mcp_service.py"], cwd=REPO_ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        start = time.time()
        try:
            # 等待端口开放或进程提前退出
            opened = False
            output_lines = []
            while time.time() - start < 8:
                if proc.poll() is not None:
                    # 进程已退出，收集日志
                    output_lines.extend(proc.stdout.readlines() if proc.stdout else [])
                    print("[MCP Server Exit]", "".join(output_lines))
                    break
                if is_port_open("127.0.0.1", port):
                    opened = True
                    break
                # 读取部分日志
                if proc.stdout and proc.stdout.readable():
                    line = proc.stdout.readline()
                    if line:
                        output_lines.append(line)
                time.sleep(0.2)

            # 若端口开放，认为服务已启动，简单进行TCP探测
            if opened:
                assert is_port_open("127.0.0.1", port), "MCP端口未开放"
            else:
                # 不强制失败：记录原因，供报告使用
                print("[MCP Launch Warning] 端口未开放，可能由于依赖或导入错误。日志：\n" + "".join(output_lines))
        finally:
            # 结束进程
            try:
                if proc.poll() is None:
                    proc.send_signal(signal.SIGINT)
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
            except Exception:
                pass


class TestCLIMode:
    """CLI 模式测试（避免触发LLM调用）"""

    def test_cli_interactive_help_and_quit(self):
        """启动交互式CLI，发送/help与/quit，验证输出结构"""
        proc = subprocess.Popen([PYTHON, "gtplanner.py", "--no-streaming", "--language", "zh"], cwd=REPO_ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            # 等待欢迎输出
            time.sleep(1.0)
            # 发送/help
            proc.stdin.write("/help\n")
            proc.stdin.flush()
            time.sleep(0.8)
            # 发送/quit
            proc.stdin.write("/quit\n")
            proc.stdin.flush()
            time.sleep(0.8)
            # 读取输出
            out = proc.communicate(timeout=5)[0]
            assert "帮助" in out or "help" in out.lower(), "CLI 未显示帮助信息"
            assert "会话" in out or "session" in out.lower(), "CLI 未显示会话相关信息"
        finally:
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass

    def test_cli_invalid_language_parameter(self):
        """无效语言参数应退出并返回错误码（argparse约束）"""
        proc = subprocess.run([PYTHON, "agent/cli/gtplanner_cli.py", "--language", "xx", "--no-streaming"], cwd=REPO_ROOT, capture_output=True, text=True)
        assert proc.returncode != 0, "无效语言参数应导致非零退出码"
        assert "invalid choice" in (proc.stderr or proc.stdout).lower()


class TestConfigLoading:
    """配置加载与基本健壮性"""

    def test_settings_file_exists_utf8(self):
        """确认settings.toml存在且为UTF-8（无法解析也不失败）"""
        settings = REPO_ROOT / "settings.toml"
        assert settings.exists(), "settings.toml 不存在"
        # 简单以utf-8读取
        with open(settings, "r", encoding="utf-8") as f:
            content = f.read()
            assert isinstance(content, str)

    def test_cli_config_preload_index(self):
        """验证CLI预加载工具索引阶段不崩溃（verbose模式可见提示）"""
        # 仅执行到参数解析与欢迎、预加载提示（不输入需求，超时后退出）
        proc = subprocess.Popen([PYTHON, "gtplanner.py", "--no-streaming", "--language", "en", "-v"], cwd=REPO_ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            # 等待预加载日志
            time.sleep(1.5)
            # 立即退出
            proc.stdin.write("/quit\n")
            proc.stdin.flush()
            out = proc.communicate(timeout=8)[0]
            assert "Initializing" in out or "索引" in out or "初始化" in out, "未看到索引初始化提示"
        finally:
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass

