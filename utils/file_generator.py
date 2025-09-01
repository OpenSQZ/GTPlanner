"""
文件生成工具

提供简洁的文件生成功能，不依赖共享状态，专注于文件操作。
"""

import os
import time
from typing import Optional, Dict, Any
from pathlib import Path


class FileGenerator:
    """文件生成器类"""
    
    def __init__(self, output_dir: str = "output"):
        """
        初始化文件生成器
        
        Args:
            output_dir: 输出目录，默认为 "output"
        """
        self.output_dir = Path(output_dir)
        self.ensure_output_dir()
    
    def ensure_output_dir(self) -> None:
        """确保输出目录存在"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def write_file(self, filename: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        写入文件
        
        Args:
            filename: 文件名
            content: 文件内容
            encoding: 文件编码，默认 utf-8
            
        Returns:
            Dict: 包含文件信息的字典
        """
        if not content or not content.strip():
            raise ValueError(f"文件内容不能为空: {filename}")
        
        file_path = self.output_dir / filename
        
        # 写入文件
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content.strip())
        
        # 返回文件信息
        file_info = {
            "filename": filename,
            "path": str(file_path),
            "absolute_path": str(file_path.absolute()),
            "size": len(content.strip().encode(encoding)),
            "encoding": encoding,
            "created_at": time.time(),
            "exists": file_path.exists()
        }
        
        return file_info
    
    def write_multiple_files(self, files: list[Dict[str, str]]) -> list[Dict[str, Any]]:
        """
        批量写入多个文件
        
        Args:
            files: 文件列表，每个元素包含 filename 和 content
            
        Returns:
            List[Dict]: 文件信息列表
        """
        results = []
        for file_data in files:
            filename = file_data.get("filename")
            content = file_data.get("content")
            encoding = file_data.get("encoding", "utf-8")
            
            if not filename or not content:
                continue
                
            try:
                file_info = self.write_file(filename, content, encoding)
                results.append(file_info)
            except Exception as e:
                results.append({
                    "filename": filename,
                    "error": str(e),
                    "success": False
                })
        
        return results
    
    def read_file(self, filename: str, encoding: str = "utf-8") -> str:
        """
        读取文件内容
        
        Args:
            filename: 文件名
            encoding: 文件编码
            
        Returns:
            str: 文件内容
        """
        file_path = self.output_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    
    def file_exists(self, filename: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 文件是否存在
        """
        file_path = self.output_dir / filename
        return file_path.exists()
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            filename: 文件名
            
        Returns:
            Dict: 文件信息，如果文件不存在返回 None
        """
        file_path = self.output_dir / filename
        
        if not file_path.exists():
            return None
        
        stat = file_path.stat()
        return {
            "filename": filename,
            "path": str(file_path),
            "absolute_path": str(file_path.absolute()),
            "size": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
            "exists": True
        }
    
    def list_files(self, pattern: str = "*") -> list[Dict[str, Any]]:
        """
        列出输出目录中的文件
        
        Args:
            pattern: 文件名模式，默认为 "*"（所有文件）
            
        Returns:
            List[Dict]: 文件信息列表
        """
        files = []
        for file_path in self.output_dir.glob(pattern):
            if file_path.is_file():
                file_info = self.get_file_info(file_path.name)
                if file_info:
                    files.append(file_info)
        
        return files
    
    def delete_file(self, filename: str) -> bool:
        """
        删除文件
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否成功删除
        """
        file_path = self.output_dir / filename
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            return True
        except Exception:
            return False
    
    def clear_output_dir(self) -> int:
        """
        清空输出目录
        
        Returns:
            int: 删除的文件数量
        """
        count = 0
        for file_path in self.output_dir.iterdir():
            if file_path.is_file():
                try:
                    file_path.unlink()
                    count += 1
                except Exception:
                    pass
        
        return count


# 便捷函数
def write_file(filename: str, content: str, output_dir: str = "output", encoding: str = "utf-8") -> Dict[str, Any]:
    """
    便捷的文件写入函数
    
    Args:
        filename: 文件名
        content: 文件内容
        output_dir: 输出目录
        encoding: 文件编码
        
    Returns:
        Dict: 文件信息
    """
    generator = FileGenerator(output_dir)
    return generator.write_file(filename, content, encoding)


def write_multiple_files(files: list[Dict[str, str]], output_dir: str = "output") -> list[Dict[str, Any]]:
    """
    便捷的批量文件写入函数
    
    Args:
        files: 文件列表
        output_dir: 输出目录
        
    Returns:
        List[Dict]: 文件信息列表
    """
    generator = FileGenerator(output_dir)
    return generator.write_multiple_files(files)


def read_file(filename: str, output_dir: str = "output", encoding: str = "utf-8") -> str:
    """
    便捷的文件读取函数
    
    Args:
        filename: 文件名
        output_dir: 输出目录
        encoding: 文件编码
        
    Returns:
        str: 文件内容
    """
    generator = FileGenerator(output_dir)
    return generator.read_file(filename, encoding)
