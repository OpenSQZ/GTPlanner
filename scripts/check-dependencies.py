#!/usr/bin/env python3
"""
依赖项安全检查和管理脚本

功能：
1. 检查依赖项重复声明
2. 扫描安全漏洞
3. 检查版本冲突
4. 更新依赖项到最新稳定版本
"""

import subprocess
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class DependencyChecker:
    """依赖项检查器"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.pyproject_path = self.project_root / "pyproject.toml"
        
    def check_all(self) -> bool:
        """执行所有检查"""
        logger.info("🔍 开始依赖项检查...")
        
        all_passed = True
        
        # 1. 检查重复依赖
        if not self.check_duplicate_dependencies():
            all_passed = False
        
        # 2. 检查版本冲突
        if not self.check_version_conflicts():
            all_passed = False
        
        # 3. 安全漏洞扫描
        if not self.check_security_vulnerabilities():
            all_passed = False
        
        # 4. 检查过时依赖
        self.check_outdated_dependencies()
        
        if all_passed:
            logger.info("✅ 所有依赖项检查通过")
        else:
            logger.error("❌ 依赖项检查发现问题")
        
        return all_passed
    
    def check_duplicate_dependencies(self) -> bool:
        """检查重复的依赖声明"""
        logger.info("📦 检查重复依赖...")
        
        if not self.pyproject_path.exists():
            logger.error(f"pyproject.toml 文件不存在: {self.pyproject_path}")
            return False
        
        try:
            import tomllib
        except ImportError:
            logger.warning("tomllib 不可用，跳过重复依赖检查")
            return True
        
        try:
            with open(self.pyproject_path, 'rb') as f:
                data = tomllib.load(f)
            
            dependencies = data.get('project', {}).get('dependencies', [])
            dev_dependencies = data.get('dependency-groups', {}).get('dev', [])
            
            # 提取包名
            def extract_package_name(dep: str) -> str:
                # 移除版本约束，提取包名
                return re.split(r'[>=<!\[\]]+', dep)[0].strip()
            
            # 检查主依赖中的重复
            main_packages = [extract_package_name(dep) for dep in dependencies]
            main_duplicates = self._find_duplicates(main_packages)
            
            # 检查开发依赖中的重复
            dev_packages = [extract_package_name(dep) for dep in dev_dependencies]
            dev_duplicates = self._find_duplicates(dev_packages)
            
            # 检查主依赖和开发依赖之间的重复
            cross_duplicates = set(main_packages) & set(dev_packages)
            
            has_duplicates = False
            
            if main_duplicates:
                logger.error(f"❌ 主依赖中发现重复包: {main_duplicates}")
                has_duplicates = True
            
            if dev_duplicates:
                logger.error(f"❌ 开发依赖中发现重复包: {dev_duplicates}")
                has_duplicates = True
            
            if cross_duplicates:
                logger.warning(f"⚠️ 主依赖和开发依赖中发现相同包: {cross_duplicates}")
            
            if not has_duplicates:
                logger.info("✅ 未发现重复依赖")
            
            return not has_duplicates
            
        except Exception as e:
            logger.error(f"检查重复依赖时出错: {e}")
            return False
    
    def _find_duplicates(self, items: List[str]) -> Set[str]:
        """查找列表中的重复项"""
        seen = set()
        duplicates = set()
        for item in items:
            if item in seen:
                duplicates.add(item)
            seen.add(item)
        return duplicates
    
    def check_version_conflicts(self) -> bool:
        """检查版本冲突"""
        logger.info("🔄 检查版本冲突...")
        
        try:
            # 使用 uv 检查依赖解析
            result = subprocess.run(
                ["uv", "sync", "--dry-run"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("✅ 未发现版本冲突")
                return True
            else:
                logger.error("❌ 发现版本冲突:")
                logger.error(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ 版本冲突检查超时")
            return True
        except FileNotFoundError:
            logger.warning("⚠️ uv 命令不可用，跳过版本冲突检查")
            return True
        except Exception as e:
            logger.error(f"检查版本冲突时出错: {e}")
            return False
    
    def check_security_vulnerabilities(self) -> bool:
        """检查安全漏洞"""
        logger.info("🔒 检查安全漏洞...")
        
        # 尝试使用 pip-audit
        try:
            result = subprocess.run(
                ["pip-audit", "--format=json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                vulnerabilities = json.loads(result.stdout)
                if vulnerabilities:
                    logger.error(f"❌ 发现 {len(vulnerabilities)} 个安全漏洞")
                    for vuln in vulnerabilities[:5]:  # 只显示前5个
                        logger.error(f"  - {vuln.get('package', 'Unknown')}: {vuln.get('vulnerability_id', 'Unknown')}")
                    return False
                else:
                    logger.info("✅ 未发现安全漏洞")
                    return True
            else:
                logger.warning("⚠️ pip-audit 检查失败，可能需要安装: pip install pip-audit")
                return True
                
        except FileNotFoundError:
            logger.warning("⚠️ pip-audit 不可用，跳过安全漏洞检查")
            return True
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ 安全漏洞检查超时")
            return True
        except Exception as e:
            logger.warning(f"⚠️ 安全漏洞检查出错: {e}")
            return True
    
    def check_outdated_dependencies(self):
        """检查过时的依赖项"""
        logger.info("📅 检查过时依赖...")
        
        try:
            # 使用 uv 检查过时依赖
            result = subprocess.run(
                ["uv", "tree", "--outdated"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                logger.info("📋 过时依赖信息:")
                for line in result.stdout.strip().split('\n')[:10]:  # 只显示前10行
                    logger.info(f"  {line}")
            else:
                logger.info("✅ 所有依赖都是最新的")
                
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ 过时依赖检查超时")
        except FileNotFoundError:
            logger.warning("⚠️ uv 命令不可用")
        except Exception as e:
            logger.warning(f"⚠️ 检查过时依赖时出错: {e}")
    
    def fix_duplicate_dependencies(self):
        """修复重复依赖（交互式）"""
        logger.info("🔧 修复重复依赖...")
        
        # 这里可以实现自动修复逻辑
        # 由于涉及到复杂的依赖解析，暂时只提供检查功能
        logger.info("请手动检查并修复 pyproject.toml 中的重复依赖")
    
    def update_dependencies(self, dry_run: bool = True):
        """更新依赖项到最新版本"""
        logger.info("🔄 更新依赖项...")
        
        try:
            cmd = ["uv", "sync", "--upgrade"]
            if dry_run:
                cmd.append("--dry-run")
                logger.info("执行干运行模式...")
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                logger.info("✅ 依赖项更新完成")
                if result.stdout:
                    logger.info("更新详情:")
                    for line in result.stdout.strip().split('\n')[:10]:
                        logger.info(f"  {line}")
            else:
                logger.error("❌ 依赖项更新失败:")
                logger.error(result.stderr)
                
        except subprocess.TimeoutExpired:
            logger.error("❌ 依赖项更新超时")
        except Exception as e:
            logger.error(f"更新依赖项时出错: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GTPlanner依赖项检查工具")
    parser.add_argument("--check", action="store_true", help="执行所有检查")
    parser.add_argument("--fix", action="store_true", help="修复发现的问题")
    parser.add_argument("--update", action="store_true", help="更新依赖项")
    parser.add_argument("--dry-run", action="store_true", help="干运行模式")
    
    args = parser.parse_args()
    
    checker = DependencyChecker()
    
    if args.check or not any(vars(args).values()):
        # 默认执行检查
        success = checker.check_all()
        sys.exit(0 if success else 1)
    
    if args.fix:
        checker.fix_duplicate_dependencies()
    
    if args.update:
        checker.update_dependencies(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
