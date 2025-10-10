#!/usr/bin/env python3
"""
GTPlanner Configuration Validation Tool

A command-line utility to validate and diagnose GTPlanner configuration issues.
This tool helps users quickly identify configuration problems before running
the main application.

Usage:
    python check_config.py                  # Full configuration check
    python check_config.py --verbose        # Detailed output
    python check_config.py --json           # JSON output for automation
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.config_manager import MultilingualConfig
    from utils.language_detection import get_supported_languages
except ImportError as e:
    print(f"Error: Failed to import required modules: {e}")
    print("Please ensure you are running this script from the project root directory.")
    sys.exit(1)


class ConfigValidator:
    """Configuration validator and diagnostic tool."""
    
    # Color codes for terminal output
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'
    
    def __init__(self, verbose: bool = False):
        """Initialize the validator.
        
        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.config = MultilingualConfig()
    
    def print_header(self, text: str) -> None:
        """Print a section header."""
        print(f"\n{self.BOLD}{self.BLUE}{'=' * 60}{self.END}")
        print(f"{self.BOLD}{self.BLUE}{text}{self.END}")
        print(f"{self.BOLD}{self.BLUE}{'=' * 60}{self.END}")
    
    def print_success(self, text: str) -> None:
        """Print a success message."""
        print(f"{self.GREEN}✓{self.END} {text}")
    
    def print_warning(self, text: str) -> None:
        """Print a warning message."""
        print(f"{self.YELLOW}⚠{self.END} {text}")
    
    def print_error(self, text: str) -> None:
        """Print an error message."""
        print(f"{self.RED}✗{self.END} {text}")
    
    def print_info(self, text: str) -> None:
        """Print an info message."""
        print(f"  {text}")
    
    def check_environment_variables(self) -> Dict[str, Any]:
        """Check required environment variables.
        
        Returns:
            Dictionary with check results
        """
        required_vars = ["LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"]
        optional_vars = ["JINA_API_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY"]
        
        results = {
            "required": {},
            "optional": {},
            "issues": []
        }
        
        # Check required variables
        for var in required_vars:
            value = os.getenv(var)
            is_set = bool(value and value.strip())
            results["required"][var] = {
                "set": is_set,
                "value": value if is_set and self.verbose else ("***" if is_set else None)
            }
            
            if not is_set:
                results["issues"].append(f"Required variable {var} is not set")
        
        # Check optional variables
        for var in optional_vars:
            value = os.getenv(var)
            is_set = bool(value and value.strip())
            results["optional"][var] = {
                "set": is_set,
                "value": value if is_set and self.verbose else ("***" if is_set else None)
            }
        
        return results
    
    def check_configuration_files(self) -> Dict[str, Any]:
        """Check for configuration files.
        
        Returns:
            Dictionary with check results
        """
        results = {
            "files": {},
            "issues": []
        }
        
        config_files = ["settings.toml", ".env", "pyproject.toml"]
        
        for file in config_files:
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                     "GTPlanner-main" if os.path.exists("GTPlanner-main") else ".",
                                     file)
            exists = os.path.exists(file_path)
            results["files"][file] = {
                "exists": exists,
                "path": file_path if exists else None
            }
            
            if file == "settings.toml" and not exists:
                results["issues"].append(f"Configuration file {file} not found")
        
        return results
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Run full configuration validation.
        
        Returns:
            Dictionary with validation results
        """
        self.print_header("GTPlanner Configuration Validation")
        
        all_results = {
            "healthy": True,
            "environment": {},
            "files": {},
            "config": {},
            "health_status": {},
            "summary": {
                "total_issues": 0,
                "critical_issues": 0,
                "warnings": 0
            }
        }
        
        # Check environment variables
        print(f"\n{self.BOLD}1. Checking Environment Variables...{self.END}")
        env_results = self.check_environment_variables()
        all_results["environment"] = env_results
        
        for var, info in env_results["required"].items():
            if info["set"]:
                self.print_success(f"{var} is set")
                if self.verbose and info["value"] != "***":
                    self.print_info(f"Value: {info['value']}")
            else:
                self.print_error(f"{var} is NOT set (required)")
                all_results["summary"]["critical_issues"] += 1
                all_results["healthy"] = False
        
        for var, info in env_results["optional"].items():
            if info["set"]:
                self.print_success(f"{var} is set")
            else:
                self.print_info(f"{var} is not set (optional)")
        
        # Check configuration files
        print(f"\n{self.BOLD}2. Checking Configuration Files...{self.END}")
        file_results = self.check_configuration_files()
        all_results["files"] = file_results
        
        for file, info in file_results["files"].items():
            if info["exists"]:
                self.print_success(f"{file} found")
                if self.verbose:
                    self.print_info(f"Path: {info['path']}")
            else:
                if file == "settings.toml":
                    self.print_warning(f"{file} not found")
                    all_results["summary"]["warnings"] += 1
                else:
                    self.print_info(f"{file} not found (optional)")
        
        # Run config validation
        print(f"\n{self.BOLD}3. Validating Configuration...{self.END}")
        config_warnings = self.config.validate_config()
        all_results["config"]["warnings"] = config_warnings
        
        if config_warnings:
            for warning in config_warnings:
                self.print_warning(warning)
                all_results["summary"]["warnings"] += 1
        else:
            self.print_success("No configuration warnings")
        
        # Get health status
        print(f"\n{self.BOLD}4. Checking System Health...{self.END}")
        health_status = self.config.get_health_status()
        all_results["health_status"] = health_status
        
        for component_name, component_info in health_status["components"].items():
            status = component_info["status"]
            if status == "ok":
                self.print_success(f"{component_name.title()} component: OK")
            elif status == "warning":
                self.print_warning(f"{component_name.title()} component: Warning")
                all_results["summary"]["warnings"] += 1
            elif status == "info":
                self.print_info(f"{component_name.title()} component: Info")
            else:
                self.print_error(f"{component_name.title()} component: Error")
                all_results["summary"]["critical_issues"] += 1
            
            if self.verbose and isinstance(component_info, dict):
                for key, value in component_info.items():
                    if key != "status":
                        self.print_info(f"  {key}: {value}")
        
        # Print summary
        print(f"\n{self.BOLD}{'=' * 60}{self.END}")
        print(f"{self.BOLD}Summary{self.END}")
        print(f"{self.BOLD}{'=' * 60}{self.END}")
        
        all_results["summary"]["total_issues"] = (
            all_results["summary"]["critical_issues"] + 
            all_results["summary"]["warnings"]
        )
        
        if all_results["healthy"] and all_results["summary"]["total_issues"] == 0:
            self.print_success("Configuration is valid and healthy!")
        elif all_results["summary"]["critical_issues"] > 0:
            self.print_error(
                f"Found {all_results['summary']['critical_issues']} critical issue(s) "
                f"and {all_results['summary']['warnings']} warning(s)"
            )
            print(f"\n{self.YELLOW}Please fix critical issues before running GTPlanner.{self.END}")
        else:
            self.print_warning(f"Found {all_results['summary']['warnings']} warning(s)")
            print(f"\n{self.YELLOW}GTPlanner may run with reduced functionality.{self.END}")
        
        return all_results
    
    def print_recommendations(self) -> None:
        """Print configuration recommendations."""
        self.print_header("Configuration Recommendations")
        
        print("\n1. Required Environment Variables:")
        print("   Set the following in your environment or .env file:")
        print("   - LLM_API_KEY: Your LLM API key")
        print("   - LLM_BASE_URL: Your LLM API endpoint (e.g., https://api.openai.com/v1)")
        print("   - LLM_MODEL: Model name (e.g., gpt-4)")
        
        print("\n2. Optional but Recommended:")
        print("   - JINA_API_KEY: Enable research tool functionality")
        print("   - LANGFUSE_SECRET_KEY & LANGFUSE_PUBLIC_KEY: Enable execution tracing")
        
        print("\n3. Configuration File:")
        print("   - Copy .env.example to .env and fill in your values")
        print("   - Customize settings.toml for advanced configuration")
        
        print(f"\n{self.BLUE}For more information, see the README.md file.{self.END}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate GTPlanner configuration and diagnose issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python check_config.py                  # Basic validation
  python check_config.py --verbose        # Detailed output
  python check_config.py --json           # JSON output
  python check_config.py --help-config    # Show configuration help
        """
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed configuration information"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    parser.add_argument(
        "--help-config",
        action="store_true",
        help="Show configuration recommendations"
    )
    
    args = parser.parse_args()
    
    validator = ConfigValidator(verbose=args.verbose)
    
    if args.help_config:
        validator.print_recommendations()
        return 0
    
    results = validator.validate_configuration()
    
    if args.json:
        print("\n" + json.dumps(results, indent=2))
    
    # Return exit code based on health
    if results["summary"]["critical_issues"] > 0:
        return 1
    elif results["summary"]["warnings"] > 0:
        return 0  # Warnings don't cause failure
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
