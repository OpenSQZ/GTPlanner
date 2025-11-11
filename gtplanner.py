#!/usr/bin/env python3
"""
GTPlanner 启动脚本

快速启动GTPlanner CLI的便捷脚本。

使用方式:
    python gtplanner.py                    # 启动交互式CLI
    python gtplanner.py "设计用户管理系统"   # 直接处理需求
    python gtplanner.py --verbose "需求"    # 详细模式
    python gtplanner.py --load <session_id> # 加载指定会话
    python gtplanner.py --language en "需求" # 使用英文界面
    python gtplanner.py -l ja "需求"        # 使用日文界面
"""

import sys
import subprocess
from pathlib import Path

def main():
    """主函数"""
    # 获取脚本所在目录
    script_dir = Path(__file__).parent
    
    # 使用模块方式运行，避免相对导入问题
    cmd = [sys.executable, "-m", "gtplanner.agent.cli.gtplanner_cli"] + sys.argv[1:]
    
    # 执行CLI
    try:
        subprocess.run(cmd, check=True, cwd=str(script_dir))
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n👋 User interrupted, goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
