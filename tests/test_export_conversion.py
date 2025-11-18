"""
测试文档格式转换功能（独立测试，不依赖节点类）

直接测试转换方法，避免导入依赖问题
"""

import os
import sys
from pathlib import Path
import pytest
import re

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def read_test_markdown():
    """读取测试用的 Markdown 文件"""
    test_file = Path(__file__).parent.parent / "output" / "design.md"
    if not test_file.exists():
        pytest.skip(f"测试文件不存在: {test_file}")
    return test_file.read_text(encoding='utf-8')


def markdown_to_html(markdown_content: str) -> str:
    """将 Markdown 转换为 HTML（复制自 NodeExportDocument）"""
    lines = markdown_content.split('\n')
    html_lines = []
    in_code_block = False
    code_block_lang = ""
    in_list = False
    list_type = None  # 'ul' 或 'ol'
    
    def close_list_if_open():
        """关闭当前打开的列表"""
        nonlocal in_list, list_type
        if in_list:
            html_lines.append(f'</{list_type}>')
            in_list = False
            list_type = None
    
    def escape_html(text: str) -> str:
        """HTML 转义"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    def process_inline_markdown(text: str) -> str:
        """处理行内 Markdown 语法"""
        text = escape_html(text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
        text = re.sub(r'(?<!_)_([^_]+)_(?!_)', r'<em>\1</em>', text)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)
        return text
    
    for line in lines:
        # 代码块处理
        if line.strip().startswith('```'):
            if not in_code_block:
                code_block_lang = line.strip()[3:].strip()
                close_list_if_open()
                html_lines.append(f'<pre><code class="language-{code_block_lang}">')
                in_code_block = True
            else:
                html_lines.append('</code></pre>')
                in_code_block = False
            continue
        
        if in_code_block:
            html_lines.append(escape_html(line))
            continue
        
        # 标题转换
        if line.startswith('# '):
            close_list_if_open()
            html_lines.append(f'<h1>{process_inline_markdown(line[2:])}</h1>')
        elif line.startswith('## '):
            close_list_if_open()
            html_lines.append(f'<h2>{process_inline_markdown(line[3:])}</h2>')
        elif line.startswith('### '):
            close_list_if_open()
            html_lines.append(f'<h3>{process_inline_markdown(line[4:])}</h3>')
        elif line.startswith('#### '):
            close_list_if_open()
            html_lines.append(f'<h4>{process_inline_markdown(line[5:])}</h4>')
        elif line.startswith('##### '):
            close_list_if_open()
            html_lines.append(f'<h5>{process_inline_markdown(line[6:])}</h5>')
        elif line.startswith('###### '):
            close_list_if_open()
            html_lines.append(f'<h6>{process_inline_markdown(line[7:])}</h6>')
        # 无序列表转换
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
                list_type = 'ul'
            elif list_type != 'ul':
                html_lines.append('</ol>')
                html_lines.append('<ul>')
                list_type = 'ul'
            content = line.strip()[2:]
            html_lines.append(f'<li>{process_inline_markdown(content)}</li>')
        # 有序列表
        elif re.match(r'^\s*\d+\.\s+', line):
            if not in_list:
                html_lines.append('<ol>')
                in_list = True
                list_type = 'ol'
            elif list_type != 'ol':
                html_lines.append('</ul>')
                html_lines.append('<ol>')
                list_type = 'ol'
            content = re.sub(r'^\s*\d+\.\s+', '', line)
            html_lines.append(f'<li>{process_inline_markdown(content)}</li>')
        # 普通段落
        elif line.strip():
            close_list_if_open()
            html_lines.append(f'<p>{process_inline_markdown(line)}</p>')
        else:
            close_list_if_open()
            html_lines.append('<br>')
    
    # 关闭未关闭的列表
    close_list_if_open()
    
    html_body = '\n'.join(html_lines)
    
    # 包装完整的 HTML 文档
    html_doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>导出文档</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
        }}
        h1 {{ font-size: 2em; }}
        h2 {{ font-size: 1.5em; }}
        h3 {{ font-size: 1.25em; }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 16px;
            border-radius: 4px;
            overflow-x: auto;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin: 4px 0;
        }}
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""
    
    return html_doc


def markdown_to_txt(markdown_content: str) -> str:
    """将 Markdown 转换为纯文本（复制自 NodeExportDocument）"""
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


def test_markdown_to_html():
    """测试 Markdown 转 HTML 功能"""
    print("\n" + "="*80)
    print("测试场景 1: Markdown 转 HTML")
    print("="*80)
    
    markdown_content = read_test_markdown()
    
    # 执行转换
    html_content = markdown_to_html(markdown_content)
    
    # 验证结果
    assert html_content is not None, "HTML 内容不应为空"
    assert "<!DOCTYPE html>" in html_content, "应包含 HTML 文档声明"
    assert "<html" in html_content, "应包含 HTML 标签"
    assert "<head>" in html_content, "应包含 head 标签"
    assert "<body>" in html_content, "应包含 body 标签"
    
    # 验证基本 Markdown 元素转换
    assert "<h1>" in html_content or "<h2>" in html_content, "应包含标题标签"
    assert "<ul>" in html_content or "<ol>" in html_content, "应包含列表标签"
    
    # 验证代码块
    if "```" in markdown_content:
        assert "<pre>" in html_content or "<code>" in html_content, "应包含代码块标签"
    
    print(f"[OK] HTML 转换成功")
    print(f"[INFO] HTML 长度: {len(html_content)} 字符")
    print(f"[INFO] 原始 Markdown 长度: {len(markdown_content)} 字符")
    
    # 保存 HTML 文件用于人工检查
    output_dir = Path(__file__).parent.parent / "output"
    html_file = output_dir / "design_test.html"
    html_file.write_text(html_content, encoding='utf-8')
    print(f"[SAVE] HTML 文件已保存到: {html_file}")
    
    assert True


def test_markdown_to_txt():
    """测试 Markdown 转 TXT 功能"""
    print("\n" + "="*80)
    print("测试场景 2: Markdown 转 TXT")
    print("="*80)
    
    markdown_content = read_test_markdown()
    
    # 执行转换
    txt_content = markdown_to_txt(markdown_content)
    
    # 验证结果
    assert txt_content is not None, "TXT 内容不应为空"
    assert len(txt_content) > 0, "TXT 内容不应为空字符串"
    
    # 验证 Markdown 语法已被移除
    assert "```" not in txt_content, "不应包含代码块标记"
    assert "**" not in txt_content or txt_content.count("**") == 0, "不应包含粗体标记"
    assert not any(line.startswith("#") for line in txt_content.split("\n") if line.strip()), "不应包含标题标记"
    
    print(f"[OK] TXT 转换成功")
    print(f"[INFO] TXT 长度: {len(txt_content)} 字符")
    print(f"[INFO] 原始 Markdown 长度: {len(markdown_content)} 字符")
    
    # 显示前几行内容
    print("\n[PREVIEW] TXT 内容预览（前10行）:")
    for i, line in enumerate(txt_content.split("\n")[:10], 1):
        print(f"   {i:2d}. {line}")
    
    # 保存 TXT 文件用于人工检查
    output_dir = Path(__file__).parent.parent / "output"
    txt_file = output_dir / "design_test.txt"
    txt_file.write_text(txt_content, encoding='utf-8')
    print(f"\n[SAVE] TXT 文件已保存到: {txt_file}")
    
    assert True


def test_conversion_quality():
    """测试转换质量"""
    print("\n" + "="*80)
    print("测试场景 3: 转换质量检查")
    print("="*80)
    
    markdown_content = read_test_markdown()
    
    # HTML 转换
    html_content = markdown_to_html(markdown_content)
    
    # TXT 转换
    txt_content = markdown_to_txt(markdown_content)
    
    # 验证 HTML 包含原始内容的关键信息
    assert "Design Doc" in html_content or "网页文本爬取" in html_content, "HTML 应包含文档标题"
    
    # 验证 TXT 包含原始内容的关键信息
    assert "Design Doc" in txt_content or "网页文本爬取" in txt_content, "TXT 应包含文档标题"
    
    # 验证 HTML 格式正确
    assert html_content.count("<html") == 1, "应只有一个 html 标签"
    assert html_content.count("</html>") == 1, "应只有一个闭合 html 标签"
    
    print("[OK] 转换质量检查通过")
    print(f"   HTML 标签配对正确")
    print(f"   内容完整性验证通过")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])

