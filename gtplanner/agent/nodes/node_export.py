"""
文档导出节点 (NodeExportDocument)

将已生成的文档导出为多种格式（PDF、Word、HTML、TXT等）。
支持单格式或批量导出。

功能描述：
- 从 generated_documents 读取文档内容
- 支持多种格式转换（PDF、DOCX、HTML、TXT、MD）
- 保存转换后的文件到指定目录
- 发送导出完成事件
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from pocketflow import AsyncNode
from gtplanner.agent.streaming import (
    emit_processing_status,
    emit_error
)
from gtplanner.utils.file_generator import FileGenerator


class NodeExportDocument(AsyncNode):
    """文档导出节点 - 支持多格式导出"""
    
    def __init__(self, max_retries: int = 2, wait: float = 0.5):
        """
        初始化文档导出节点
        
        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)
        self.name = "NodeExportDocument"
        
        # 支持的导出格式
        self.supported_formats = ["md", "html", "txt", "pdf", "docx"]
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备阶段：验证参数并获取文档内容
        
        Args:
            shared: pocketflow 字典共享变量
            
        Returns:
            准备结果字典
        """
        try:
            # 获取参数
            document_type = shared.get("document_type")
            export_formats = shared.get("export_formats", [])
            output_dir = shared.get("output_dir", "output")
            
            # 验证必需参数
            if not document_type:
                error_msg = "document_type is required"
                await emit_error(
                    shared=shared,
                    error_message=error_msg,
                    error_details={"error_code": "MISSING_PARAMETER"}
                )
                return {
                    "success": False,
                    "error": error_msg
                }
            
            if not export_formats:
                error_msg = "export_formats is required and cannot be empty"
                await emit_error(
                    shared=shared,
                    error_message=error_msg,
                    error_details={"error_code": "MISSING_PARAMETER"}
                )
                return {
                    "success": False,
                    "error": error_msg
                }
            
            # 验证文档类型
            if document_type not in ["design", "database_design", "all"]:
                error_msg = f"Invalid document_type: {document_type}. Must be 'design', 'database_design', or 'all'"
                await emit_error(
                    shared=shared,
                    error_message=error_msg,
                    error_details={"error_code": "INVALID_PARAMETER"}
                )
                return {
                    "success": False,
                    "error": error_msg
                }
            
            # 验证导出格式
            invalid_formats = [fmt for fmt in export_formats if fmt not in self.supported_formats]
            if invalid_formats:
                error_msg = f"Unsupported export formats: {invalid_formats}. Supported formats: {self.supported_formats}"
                await emit_error(
                    shared=shared,
                    error_message=error_msg,
                    error_details={"error_code": "INVALID_FORMAT"}
                )
                return {
                    "success": False,
                    "error": error_msg
                }
            
            # 获取已生成的文档
            generated_documents = shared.get("generated_documents", [])
            
            if not generated_documents:
                error_msg = "没有找到已生成的文档，请先使用 design 或 database_design 工具生成文档"
                await emit_error(
                    shared=shared,
                    error_message=error_msg,
                    error_details={"error_code": "NO_DOCUMENTS"}
                )
                return {
                    "success": False,
                    "error": error_msg
                }
            
            # 根据 document_type 筛选文档
            target_documents = []
            if document_type == "all":
                target_documents = generated_documents
            else:
                for doc in generated_documents:
                    if doc.get("type") == document_type:
                        target_documents.append(doc)
            
            if not target_documents:
                available_types = [doc.get("type") for doc in generated_documents]
                error_msg = f"没有找到类型为 '{document_type}' 的文档。可用文档类型: {available_types}"
                await emit_error(
                    shared=shared,
                    error_message=error_msg,
                    error_details={"error_code": "DOCUMENT_NOT_FOUND"}
                )
                return {
                    "success": False,
                    "error": error_msg,
                    "available_documents": available_types
                }
            
            # 发送处理状态
            await emit_processing_status(
                shared=shared,
                message=f"准备导出 {len(target_documents)} 个文档为 {len(export_formats)} 种格式..."
            )
            
            return {
                "success": True,
                "document_type": document_type,
                "export_formats": export_formats,
                "output_dir": output_dir,
                "target_documents": target_documents
            }
            
        except Exception as e:
            error_msg = f"Preparation failed: {str(e)}"
            await emit_error(
                shared=shared,
                error_message=error_msg,
                error_details={"error_code": "PREP_ERROR"}
            )
            return {
                "success": False,
                "error": error_msg
            }
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：格式转换
        
        Args:
            prep_result: 准备阶段的结果
            
        Returns:
            执行结果字典
        """
        try:
            # 检查准备阶段是否成功
            if not prep_result.get("success"):
                return prep_result
            
            target_documents = prep_result["target_documents"]
            export_formats = prep_result["export_formats"]
            
            # 执行格式转换
            export_results = []
            
            for doc in target_documents:
                doc_type = doc.get("type")
                original_filename = doc.get("filename", f"{doc_type}.md")
                content = doc.get("content", "")
                
                if not content:
                    export_results.append({
                        "success": False,
                        "document_type": doc_type,
                        "filename": original_filename,
                        "error": "文档内容为空"
                    })
                    continue
                
                # 为每个格式生成导出文件
                doc_results = []
                for fmt in export_formats:
                    try:
                        # 转换格式
                        converted_content = self._convert_format(content, fmt)
                        
                        # 生成文件名（添加时间戳以区分不同导出的文件）
                        base_name = Path(original_filename).stem
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        export_filename = f"{base_name}_{fmt}_{timestamp}.{fmt}"
                        
                        doc_results.append({
                            "format": fmt,
                            "filename": export_filename,
                            "content": converted_content,
                            "content_type": "text" if fmt in ["md", "html", "txt"] else "binary"
                        })
                    except Exception as e:
                        doc_results.append({
                            "format": fmt,
                            "success": False,
                            "error": f"格式转换失败: {str(e)}"
                        })
                
                export_results.append({
                    "document_type": doc_type,
                    "original_filename": original_filename,
                    "exports": doc_results
                })
            
            return {
                "success": True,
                "export_results": export_results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}"
            }
    
    async def post_async(
        self,
        shared: Dict[str, Any],
        prep_res: Dict[str, Any],
        exec_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        后处理阶段：保存文件并发送完成事件
        
        Args:
            shared: pocketflow 字典共享变量
            prep_res: 准备阶段的结果
            exec_res: 执行阶段的结果
            
        Returns:
            最终结果字典
        """
        try:
            if not exec_res.get("success"):
                error_msg = exec_res.get("error", "Unknown error")
                await emit_error(
                    shared=shared,
                    error_message=f"❌ 文档导出失败: {error_msg}",
                    error_details={"error_code": "EXPORT_ERROR"}
                )
                return exec_res
            
            export_results = exec_res.get("export_results", [])
            output_dir = prep_res.get("output_dir", "output")
            
            # 创建文件生成器
            file_generator = FileGenerator(output_dir=output_dir)
            
            # 保存所有导出的文件
            saved_files = []
            failed_exports = []
            
            for doc_result in export_results:
                doc_type = doc_result.get("document_type")
                original_filename = doc_result.get("original_filename")
                exports = doc_result.get("exports", [])
                
                for export in exports:
                    if "error" in export:
                        failed_exports.append({
                            "document_type": doc_type,
                            "format": export.get("format"),
                            "error": export.get("error")
                        })
                        continue
                    
                    try:
                        filename = export.get("filename")
                        content = export.get("content")
                        content_type = export.get("content_type", "text")
                        
                        if content_type == "text":
                            # 文本文件：使用 FileGenerator
                            file_info = file_generator.write_file(filename, content)
                            saved_files.append({
                                "document_type": doc_type,
                                "format": export.get("format"),
                                "filename": filename,
                                "path": file_info.get("path"),
                                "size": file_info.get("size")
                            })
                        else:
                            # 二进制文件（PDF、DOCX）：需要特殊处理
                            # TODO: 实现二进制文件保存
                            failed_exports.append({
                                "document_type": doc_type,
                                "format": export.get("format"),
                                "error": f"格式 {export.get('format')} 暂未实现"
                            })
                    except Exception as e:
                        failed_exports.append({
                            "document_type": doc_type,
                            "format": export.get("format"),
                            "error": f"保存失败: {str(e)}"
                        })
            
            # 发送完成状态
            if saved_files:
                success_msg = f"✅ 成功导出 {len(saved_files)} 个文件"
                if failed_exports:
                    success_msg += f"，{len(failed_exports)} 个失败"
                await emit_processing_status(shared=shared, message=success_msg)
            else:
                await emit_error(
                    shared=shared,
                    error_message="❌ 所有格式导出均失败",
                    error_details={"failed_exports": failed_exports}
                )
            
            # 返回最终结果
            return {
                "success": len(saved_files) > 0,
                "saved_files": saved_files,
                "failed_exports": failed_exports,
                "total_exported": len(saved_files),
                "total_failed": len(failed_exports)
            }
            
        except Exception as e:
            error_msg = f"Post-processing failed: {str(e)}"
            await emit_error(
                shared=shared,
                error_message=error_msg,
                error_details={"error_code": "POST_ERROR"}
            )
            return {
                "success": False,
                "error": error_msg
            }
    
    def _convert_format(self, markdown_content: str, target_format: str) -> str:
        """
        将 Markdown 内容转换为目标格式
        
        Args:
            markdown_content: Markdown 格式的内容
            target_format: 目标格式（md, html, txt, pdf, docx）
            
        Returns:
            转换后的内容（字符串或字节）
        """
        if target_format == "md":
            # Markdown：直接返回
            return markdown_content
        
        elif target_format == "html":
            # HTML：简单转换（后续可以使用 markdown 库增强）
            return self._markdown_to_html(markdown_content)
        
        elif target_format == "txt":
            # TXT：去除 Markdown 语法
            return self._markdown_to_txt(markdown_content)
        
        elif target_format == "pdf":
            # PDF：暂未实现，返回错误提示
            raise NotImplementedError("PDF 导出功能暂未实现，请使用 HTML 或 TXT 格式")
        
        elif target_format == "docx":
            # DOCX：暂未实现，返回错误提示
            raise NotImplementedError("DOCX 导出功能暂未实现，请使用 HTML 或 TXT 格式")
        
        else:
            raise ValueError(f"Unsupported format: {target_format}")
    
    def _markdown_to_html(self, markdown_content: str) -> str:
        """
        将 Markdown 转换为 HTML（支持 Mermaid 渲染和现代设计）
        
        Args:
            markdown_content: Markdown 内容
            
        Returns:
            HTML 内容
        """
        import re
        
        # 基本转换规则
        lines = markdown_content.split('\n')
        html_lines = []
        in_code_block = False
        code_block_lang = ""
        in_list = False
        list_type = None  # 'ul' 或 'ol'
        mermaid_content = []  # 用于收集 Mermaid 代码块内容
        mermaid_block_count = 0  # Mermaid 代码块计数器
        
        def close_list_if_open():
            """关闭当前打开的列表"""
            nonlocal in_list, list_type
            if in_list:
                html_lines.append(f'</{list_type}>')
                in_list = False
                list_type = None
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 代码块处理（改进：支持 Mermaid 特殊处理）
            if line.strip().startswith('```'):
                lang_match = re.match(r'^```(\w+)?', line.strip())
                if lang_match:
                    detected_lang = lang_match.group(1) or ""
                    
                    if not in_code_block:
                        # 开始代码块
                        code_block_lang = detected_lang
                        close_list_if_open()
                        
                        if code_block_lang == "mermaid":
                            # Mermaid 代码块：收集内容，稍后渲染
                            mermaid_content = []
                            in_code_block = True
                            i += 1
                            continue
                        else:
                            # 普通代码块
                            html_lines.append(f'<pre><code class="language-{code_block_lang}">')
                            in_code_block = True
                            i += 1
                            continue
                    else:
                        # 结束代码块
                        if code_block_lang == "mermaid":
                            # 生成 Mermaid 渲染容器
                            mermaid_id = f"mermaid-{mermaid_block_count}"
                            mermaid_code = '\n'.join(mermaid_content)
                            html_lines.append('<div class="mermaid-container">')
                            html_lines.append(f'<div class="mermaid" id="{mermaid_id}">')
                            html_lines.append(self._escape_html(mermaid_code))
                            html_lines.append('</div>')
                            html_lines.append('</div>')
                            mermaid_block_count += 1
                        else:
                            html_lines.append('</code></pre>')
                        
                        in_code_block = False
                        code_block_lang = ""
                        i += 1
                        continue
            
            # 处理代码块内容
            if in_code_block:
                if code_block_lang == "mermaid":
                    mermaid_content.append(line)
                else:
                    html_lines.append(self._escape_html(line))
                i += 1
                continue
            
            # 标题转换
            if line.startswith('# '):
                close_list_if_open()
                html_lines.append(f'<h1>{self._process_inline_markdown(line[2:])}</h1>')
            elif line.startswith('## '):
                close_list_if_open()
                html_lines.append(f'<h2>{self._process_inline_markdown(line[3:])}</h2>')
            elif line.startswith('### '):
                close_list_if_open()
                html_lines.append(f'<h3>{self._process_inline_markdown(line[4:])}</h3>')
            elif line.startswith('#### '):
                close_list_if_open()
                html_lines.append(f'<h4>{self._process_inline_markdown(line[5:])}</h4>')
            elif line.startswith('##### '):
                close_list_if_open()
                html_lines.append(f'<h5>{self._process_inline_markdown(line[6:])}</h5>')
            elif line.startswith('###### '):
                close_list_if_open()
                html_lines.append(f'<h6>{self._process_inline_markdown(line[7:])}</h6>')
            # 无序列表转换
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                    list_type = 'ul'
                elif list_type != 'ul':
                    # 从有序列表切换到无序列表
                    html_lines.append('</ol>')
                    html_lines.append('<ul>')
                    list_type = 'ul'
                content = line.strip()[2:]
                html_lines.append(f'<li>{self._process_inline_markdown(content)}</li>')
            # 有序列表
            elif re.match(r'^\s*\d+\.\s+', line):
                if not in_list:
                    html_lines.append('<ol>')
                    in_list = True
                    list_type = 'ol'
                elif list_type != 'ol':
                    # 从无序列表切换到有序列表
                    html_lines.append('</ul>')
                    html_lines.append('<ol>')
                    list_type = 'ol'
                content = re.sub(r'^\s*\d+\.\s+', '', line)
                html_lines.append(f'<li>{self._process_inline_markdown(content)}</li>')
            # 普通段落
            elif line.strip():
                close_list_if_open()
                html_lines.append(f'<p>{self._process_inline_markdown(line)}</p>')
            else:
                close_list_if_open()
                html_lines.append('<br>')
            
            i += 1
        
        # 关闭未关闭的列表
        close_list_if_open()
        
        html_body = '\n'.join(html_lines)
        
        # 获取当前时间用于标题
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # 包装完整的 HTML 文档（改进版：集成 Mermaid.js 和现代样式）
        html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>导出文档 - {current_time}</title>
    
    <!-- Mermaid.js 用于渲染流程图 -->
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                primaryColor: '#4a90e2',
                primaryTextColor: '#fff',
                primaryBorderColor: '#357abd',
                lineColor: '#333',
                secondaryColor: '#f0f0f0',
                tertiaryColor: '#fff'
            }}
        }});
    </script>
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
            line-height: 1.7;
            color: #2c3e50;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            padding: 40px;
            margin-top: 20px;
            margin-bottom: 20px;
        }}
        
        h1 {{
            font-size: 2.5em;
            color: #1a1a1a;
            margin-bottom: 10px;
            padding-bottom: 15px;
            border-bottom: 3px solid #4a90e2;
        }}
        
        h2 {{
            font-size: 1.8em;
            color: #2c3e50;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        h3 {{
            font-size: 1.4em;
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        h4, h5, h6 {{
            margin-top: 25px;
            margin-bottom: 12px;
            color: #34495e;
        }}
        
        p {{
            margin: 15px 0;
            text-align: justify;
        }}
        
        code {{
            background: #f4f4f4;
            padding: 3px 6px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            color: #e83e8c;
            border: 1px solid #e0e0e0;
        }}
        
        pre {{
            background: #282c34;
            color: #abb2bf;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 20px 0;
            border-left: 4px solid #4a90e2;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        pre code {{
            background: transparent;
            padding: 0;
            color: inherit;
            border: none;
        }}
        
        /* Mermaid 容器样式 */
        .mermaid-container {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        
        .mermaid {{
            text-align: center;
            background: white;
            padding: 20px;
            border-radius: 6px;
        }}
        
        ul, ol {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        
        li {{
            margin: 8px 0;
            line-height: 1.6;
        }}
        
        a {{
            color: #4a90e2;
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: all 0.3s;
        }}
        
        a:hover {{
            color: #357abd;
            border-bottom-color: #357abd;
        }}
        
        /* 响应式设计 */
        @media (max-width: 768px) {{
            .container {{
                padding: 20px;
                margin: 10px;
            }}
            
            h1 {{
                font-size: 2em;
            }}
            
            h2 {{
                font-size: 1.5em;
            }}
        }}
        
        /* 打印样式 */
        @media print {{
            body {{
                background: white;
            }}
            
            .container {{
                box-shadow: none;
                padding: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_body}
    </div>
</body>
</html>"""
        
        return html_doc
    
    def _markdown_to_txt(self, markdown_content: str) -> str:
        """
        将 Markdown 转换为纯文本（去除 Markdown 语法）
        
        Args:
            markdown_content: Markdown 内容
            
        Returns:
            纯文本内容
        """
        import re
        
        txt_content = markdown_content
        
        # 移除代码块
        txt_content = re.sub(r'```[\s\S]*?```', '', txt_content)
        
        # 移除行内代码
        txt_content = re.sub(r'`([^`]+)`', r'\1', txt_content)
        
        # 移除标题标记
        txt_content = re.sub(r'^#{1,6}\s+(.+)$', r'\1', txt_content, flags=re.MULTILINE)
        
        # 移除粗体和斜体
        txt_content = re.sub(r'\*\*([^*]+)\*\*', r'\1', txt_content)
        txt_content = re.sub(r'\*([^*]+)\*', r'\1', txt_content)
        txt_content = re.sub(r'__([^_]+)__', r'\1', txt_content)
        txt_content = re.sub(r'_([^_]+)_', r'\1', txt_content)
        
        # 移除链接，保留文本
        txt_content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', txt_content)
        
        # 移除图片
        txt_content = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', txt_content)
        
        # 移除列表标记
        txt_content = re.sub(r'^\s*[-*+]\s+', '', txt_content, flags=re.MULTILINE)
        txt_content = re.sub(r'^\s*\d+\.\s+', '', txt_content, flags=re.MULTILINE)
        
        # 移除引用标记
        txt_content = re.sub(r'^>\s+', '', txt_content, flags=re.MULTILINE)
        
        # 移除水平线
        txt_content = re.sub(r'^---+$', '', txt_content, flags=re.MULTILINE)
        
        # 清理多余空行
        txt_content = re.sub(r'\n{3,}', '\n\n', txt_content)
        
        return txt_content.strip()
    
    def _process_inline_markdown(self, text: str) -> str:
        """
        处理行内 Markdown 语法（粗体、斜体、链接等）
        
        Args:
            text: 要处理的文本
            
        Returns:
            处理后的 HTML
        """
        import re
        
        # 转义 HTML 特殊字符
        text = self._escape_html(text)
        
        # 粗体 **text**
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        
        # 斜体 *text* 或 _text_
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
        text = re.sub(r'(?<!_)_([^_]+)_(?!_)', r'<em>\1</em>', text)
        
        # 行内代码 `code`
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        
        # 链接 [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)
        
        return text
    
    def _escape_html(self, text: str) -> str:
        """
        HTML 转义
        
        Args:
            text: 要转义的文本
            
        Returns:
            转义后的文本
        """
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

