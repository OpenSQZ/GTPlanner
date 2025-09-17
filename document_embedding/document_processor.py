"""
文档处理器 - 智能文档分割和元数据生成

基于canvas.md设计文档实现的智能文档分割器，支持：
1. 基于Markdown结构的分层分割策略
2. 生成富含元数据的文本块
3. 会话级标识和隔离
4. 智能块大小控制和重叠处理
"""

import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """文档块数据结构"""
    chunk_id: str
    document_id: str
    content: str
    metadata: Dict[str, Any]
    start_index: int = 0
    end_index: int = 0


class DocumentProcessor:
    """文档处理器 - 实现智能文档分割"""

    def __init__(self,
                 chunk_size: int = 1000,
                 min_chunk_size: int = 100,
                 chunk_overlap: int = 200):
        """
        初始化文档处理器

        Args:
            chunk_size: 目标块大小（字符数）
            min_chunk_size: 最小块大小（字符数）
            chunk_overlap: 块重叠大小（字符数）
        """
        self.chunk_size = chunk_size
        self.min_chunk_size = min_chunk_size
        self.chunk_overlap = chunk_overlap

        # 定义分隔符优先级（按canvas.md设计）
        self.separators = [
            r'\n# ',      # 一级标题 (H1)
            r'\n## ',     # 二级标题 (H2)
            r'\n### ',    # 三级标题 (H3)
            r'\n#### ',   # 四级标题 (H4)
            r'\n```',     # 代码块
            r'\n\n',      # 段落
            r'[.!?]',     # 句子
            r'\n',        # 换行符
        ]

    def process_documents(self,
                         session_id: str,
                         documents: List[Dict[str, str]]) -> List[DocumentChunk]:
        """
        处理多个文档，生成文档块列表

        Args:
            session_id: 会话ID，用于命名空间隔离
            documents: 文档列表，每个文档包含 documentId 和 content

        Returns:
            文档块列表
        """
        all_chunks = []

        for doc in documents:
            document_id = doc.get("documentId", "")
            content = doc.get("content", "")

            if not document_id or not content:
                logger.warning(f"跳过无效文档: documentId={document_id}, content_length={len(content)}")
                continue

            try:
                chunks = self._split_document(session_id, document_id, content)
                all_chunks.extend(chunks)
                logger.info(f"文档 {document_id} 分割完成，生成 {len(chunks)} 个块")
            except Exception as e:
                logger.error(f"处理文档 {document_id} 失败: {str(e)}")
                continue

        logger.info(f"会话 {session_id} 文档处理完成，总共生成 {len(all_chunks)} 个块")
        return all_chunks

    def _split_document(self,
                       session_id: str,
                       document_id: str,
                       content: str) -> List[DocumentChunk]:
        """
        分割单个文档

        Args:
            session_id: 会话ID
            document_id: 文档ID
            content: 文档内容

        Returns:
            文档块列表
        """
        # 新算法：按行扫描，保持与原文 1:1 的行号映射，优先在“安全边界”处截断
        headings_structure = self._extract_headings_structure(content)
        lines = content.split('\n')
        n = len(lines)

        def is_code_fence(line: str) -> bool:
            return line.strip().startswith('```')
        def is_heading(line: str) -> bool:
            s = line.lstrip()
            return s.startswith('#')
        def is_blank(line: str) -> bool:
            return len(line.strip()) == 0

        chunks: List[DocumentChunk] = []
        chunk_num = 1
        i = 0
        while i < n:
            # 跳过开头的多余空行，但仍能正确计算行号
            start_i = i
            while start_i < n and is_blank(lines[start_i]):
                start_i += 1
            if start_i >= n:
                break
            i = start_i

            in_code = False
            cur_len = 0
            last_safe_i = i
            # 扫描直到超过 chunk_size，再回退到最近的空行/安全边界
            while i < n:
                line = lines[i]
                if is_code_fence(line):
                    in_code = not in_code
                # 若遇到新的标题且当前不是第一行，则在标题前截断
                if not in_code and i > start_i and is_heading(line):
                    break
                # 累计长度（包含换行，近似即可）
                cur_len += len(line) + 1
                if not in_code and is_blank(line):
                    last_safe_i = i
                if not in_code and cur_len >= self.chunk_size:
                    # 优先回退到空行，否则就在当前位置截断
                    if last_safe_i > start_i:
                        i = last_safe_i + 1
                    else:
                        i += 1
                    break
                i += 1
            end_i = i - 1

            # 最小块大小处理：如果过小且后面还有内容，尝试向后扩展直到达到最小值或遇到下一个标题/代码块开始
            if end_i >= start_i:
                piece = '\n'.join(lines[start_i:end_i+1])
                if len(piece.strip()) < self.min_chunk_size and end_i + 1 < n:
                    j = end_i + 1
                    in_code2 = False
                    while j < n and len(piece.strip()) < self.min_chunk_size:
                        if is_code_fence(lines[j]):
                            in_code2 = not in_code2
                        if not in_code2 and is_heading(lines[j]) and j > end_i + 1:
                            break
                        piece = piece + ('\n' if piece else '') + lines[j]
                        j += 1
                    end_i = j - 1 if j - 1 > end_i else end_i

            # 生成 chunk
            start_line = start_i + 1
            end_line = end_i + 1
            content_str = '\n'.join(lines[start_i:end_i+1]).strip()
            if not content_str:
                i = end_i + 1
                continue

            chunk_id = f"{session_id}-{document_id}-{chunk_num}"
            chunk_headings = self._get_chunk_headings(content_str, headings_structure)
            chunk_type = self._detect_chunk_type(content_str)

            # 计算字符下标（可选）
            # 通过前缀长度快速得到 start/end 的字符索引
            # 为避免 O(n^2) 计算成本，这里仅在需要时做一次线性前缀
            prefix_len = 0
            for k in range(0, start_i):
                prefix_len += len(lines[k]) + 1
            start_char = prefix_len
            for k in range(start_i, end_i + 1):
                prefix_len += len(lines[k]) + 1
            end_char = prefix_len - 1  # 指向最后一个字符位置

            metadata = {
                "sessionId": session_id,
                "source": document_id,
                "headings": chunk_headings,
                "chunk_type": chunk_type,
                "chunk_index": chunk_num - 1,
                "total_chunks": 0,
                "start_line": start_line,
                "end_line": end_line,
            }

            chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                content=content_str,
                metadata=metadata,
                start_index=start_char,
                end_index=end_char,
            ))
            chunk_num += 1
            i = end_i + 1

        # 统一修正索引与总数
        final_count = len(chunks)
        for idx, c in enumerate(chunks):
            c.metadata["chunk_index"] = idx
            c.metadata["total_chunks"] = final_count

        # 不再修改内容，避免行号错位（禁用预览重叠）
        # chunks = self._add_overlap(chunks)

        return chunks

    def _hierarchical_split(self, text: str, separator_index: int) -> List[str]:
        """
        递归分层分割

        Args:
            text: 待分割文本
            separator_index: 当前分隔符索引

        Returns:
            分割后的文本段列表
        """
        if separator_index >= len(self.separators):
            return [text] if text.strip() else []

        separator = self.separators[separator_index]

        # 使用当前分隔符分割
        if separator == r'\n```':
            # 特殊处理代码块
            segments = self._split_code_blocks(text)
        else:
            segments = re.split(separator, text)
            # 保留分隔符（除了第一个段落）
            if len(segments) > 1 and separator_index < len(self.separators) - 1:
                for i in range(1, len(segments)):
                    if separator.startswith(r'\n'):
                        segments[i] = separator.replace(r'\n', '\n').replace('\\', '') + segments[i]

        result = []
        for segment in segments:
            if not segment.strip():
                continue

            if len(segment) <= self.chunk_size:
                result.append(segment)
            else:
                # 递归使用下一级分隔符
                sub_segments = self._hierarchical_split(segment, separator_index + 1)
                result.extend(sub_segments)

        return result

    def _split_code_blocks(self, text: str) -> List[str]:
        """特殊处理代码块分割"""
        segments = []
        current_segment = ""
        in_code_block = False

        lines = text.split('\n')
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                current_segment += line + '\n'
                if not in_code_block:
                    # 代码块结束，作为一个完整段落
                    segments.append(current_segment.strip())
                    current_segment = ""
            else:
                current_segment += line + '\n'
                if not in_code_block and len(current_segment) > self.chunk_size:
                    segments.append(current_segment.strip())
                    current_segment = ""

        if current_segment.strip():
            segments.append(current_segment.strip())

        return segments

    def _extract_headings_structure(self, content: str) -> List[Dict[str, Any]]:
        """提取文档的标题结构"""
        headings = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                headings.append({
                    'level': level,
                    'title': title,
                    'line_number': i + 1
                })
        return headings

    def _locate_segment_span(self, content: str, segment: str, start_from: int = 0) -> Tuple[int, int]:
        """
        在原始 content 中定位 segment 的起止字符位置，尽量鲁棒：
        1) 先精确匹配（从 start_from 开始）
        2) 尝试前置一个换行再匹配（处理我们在分割时去掉的领先换行）
        3) 宽松匹配：将 segment 中连续空白折叠为 \s+ 的正则再匹配
        返回: (start_char, end_char)，找不到返回 (-1, -1)
        """
        seg = segment
        # 精确匹配（从给定位置）
        idx = content.find(seg, start_from)
        if idx != -1:
            return idx, idx + len(seg)
        # 退化：从头精确匹配
        idx = content.find(seg)
        if idx != -1:
            return idx, idx + len(seg)
        # 尝试前置换行
        idx = content.find("\n" + seg, start_from)
        if idx != -1:
            return idx + 1, idx + 1 + len(seg)
        idx = content.find("\n" + seg)
        if idx != -1:
            return idx + 1, idx + 1 + len(seg)
        # 宽松匹配：将任意空白折叠
        import re as _re
        def _collapse_ws(text: str) -> str:
            # 将空白序列替换为 \s+
            # 注意：要对普通字符做 re.escape
            parts = []
            buf = []
            for ch in text:
                if ch.isspace():
                    if buf:
                        parts.append(_re.escape(''.join(buf)))
                        buf = []
                    parts.append(r"\s+")
                else:
                    buf.append(ch)
            if buf:
                parts.append(_re.escape(''.join(buf)))
            return ''.join(parts)
        pattern = _collapse_ws(seg)
        try:
            m = _re.search(pattern, content, _re.DOTALL)
            if m:
                return m.start(), m.end()
        except Exception:
            pass
        return -1, -1

    def _get_chunk_headings(self, chunk_content: str, headings_structure: List[Dict[str, Any]]) -> List[str]:
        """获取文档块所属的标题层级结构（面包屑）"""
        chunk_lines = chunk_content.split('\n')
        chunk_headings = []

        # 查找块中的标题
        for line in chunk_lines:
            line = line.strip()
            if line.startswith('#'):
                title = line.lstrip('#').strip()
                chunk_headings.append(title)

        # 如果块中没有标题，尝试从上下文推断
        if not chunk_headings and headings_structure:
            # 简化实现：使用最后一个标题作为上下文
            if headings_structure:
                chunk_headings.append(headings_structure[-1]['title'])

        return chunk_headings

    def _detect_chunk_type(self, content: str) -> str:
        """检测块类型"""
        content = content.strip()
        if content.startswith('```') and content.endswith('```'):
            return "code"
        elif content.startswith('#'):
            return "heading"
        elif content.startswith('|') or '|' in content:
            return "table"
        else:
            return "text"

    def _add_overlap(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """为文档块添加重叠内容"""
        if len(chunks) <= 1:
            return chunks

        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]

            # 获取下一个块的开头部分作为重叠
            next_content_lines = next_chunk.content.split('\n')
            overlap_lines = next_content_lines[:min(5, len(next_content_lines))]
            overlap_content = '\n'.join(overlap_lines)

            # 限制重叠长度
            if len(overlap_content) > self.chunk_overlap:
                overlap_content = overlap_content[:self.chunk_overlap] + "..."

            # 添加重叠内容
            if overlap_content.strip():
                current_chunk.content += f"\n\n[下一部分预览]\n{overlap_content}"

        return chunks
