"""
智能上下文压缩系统

简单、高效的压缩系统：
1. 基于token和消息数量的即时阈值判断
2. 每次对话后自动检查并异步压缩
3. 不阻塞对话流程，用户无感知
4. 支持多种数据源（SQLite、Redis、MongoDB等）
"""

import asyncio
import json
import time
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from utils.openai_client import OpenAIClient
from .data_source_interface import DataSourceInterface, SQLiteDataSourceAdapter


class CompressionLevel(Enum):
    """压缩级别"""
    LIGHT = "light"      # 保留80%信息
    MEDIUM = "medium"    # 保留60%信息
    HEAVY = "heavy"      # 保留40%信息


@dataclass
class CompressionConfig:
    """压缩配置"""
    # 触发阈值
    max_tokens: int = 8000           # 最大token数
    max_messages: int = 50           # 最大消息数
    preserve_recent_count: int = 5   # 保留最近消息数
    
    # 压缩设置
    enable_compression: bool = True  # 启用压缩
    default_level: CompressionLevel = CompressionLevel.MEDIUM

    # 重试
    MAX_RETRIES = 3  # 定义最大重试次数
    RETRY_DELAY = 5  # 重试前的等待时间（秒）


class SmartCompressor:
    """智能压缩器"""
    
    def __init__(self, data_source: DataSourceInterface, config: Optional[CompressionConfig] = None):
        """
        初始化智能压缩器
        
        Args:
            data_source: 数据源接口实现
            config: 压缩配置
        """
        self.data_source = data_source
        self.config = config or CompressionConfig()
        self.openai_client = OpenAIClient()
        
        # 异步任务队列
        self.compression_queue = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start(self):
        """启动压缩服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self.worker_task = asyncio.create_task(self._compression_worker())
        print("🗜️ 智能压缩服务已启动")
    
    async def stop(self):
        """停止压缩服务"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        print("🗜️ 智能压缩服务已停止")
    
    async def should_compress(self, session_id: str) -> bool:
        """
        检查会话是否需要压缩（异步方法，快速判断）
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否需要压缩
        """
        if not self.config.enable_compression:
            return False
        
        try:
            # 从数据源获取token统计信息
            compressed_context = await self.data_source.get_active_compressed_context(session_id)

            if not compressed_context:
                # 这是异常情况，说明数据不一致
                print(f"⚠️ 警告：会话 {session_id} 缺少压缩上下文记录，无法检测压缩需求")
                return False

            # 从压缩上下文获取统计信息
            message_count = compressed_context["compressed_message_count"]
            token_count = compressed_context["compressed_token_count"]

            # 超过任一阈值就压缩
            return (token_count > self.config.max_tokens or
                   message_count > self.config.max_messages)
            
        except Exception as e:
            print(f"⚠️ 压缩检查失败: {e}")
            return False
    
    async def compress_if_needed(self, session_id: str):
        """
        如果需要则异步压缩（不阻塞调用方）
        
        Args:
            session_id: 会话ID
        """
        if await self.should_compress(session_id):
            # 异步调度压缩任务
            await self._schedule_compression(session_id)
    
    async def _schedule_compression(self, session_id: str):
        """调度压缩任务"""
        try:
            task = {
                'session_id': session_id,
                'scheduled_at': datetime.now(),
                'retries': 0,
            }
            
            await self.compression_queue.put(task)
            print(f"📋 已调度压缩任务: {session_id}")
            
        except Exception as e:
            print(f"⚠️ 调度压缩失败: {e}")
    
    async def _compression_worker(self):
        """压缩工作线程"""
        while self.is_running:
            try:
                # 等待压缩任务
                task = await asyncio.wait_for(
                    self.compression_queue.get(),
                    timeout=1.0
                )

                # 执行压缩
                await self._execute_compression(task)

                # 标记任务完成
                self.compression_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"任务 {task} 执行失败: {e}")
                if task and task.get("retries", 0) < self.config.MAX_RETRIES:
                    task["retries"] += 1
                    print(
                        f"任务 {task} 准备重试 "
                        f"(第 {task.get('retries')} 次)。"
                        f"等待 {self.config.RETRY_DELAY} 秒后重新入队。"
                    )
                    
                    # 等待一段时间
                    await asyncio.sleep(self.config.RETRY_DELAY) 
                    
                    # 重新将封装后的任务放回队列
                    await self.compression_queue.put(task) 
                else:
                    # 达到最大重试次数或 task_wrapper 无效，放弃任务
                    if task:
                        print(
                            f"任务 {task} 达到最大重试次数 "
                            f"({self.config.MAX_RETRIES})，任务失败并放弃。"
                        )
                    # 标记任务完成 (失败放弃时)
                    ## TODO 增加告警机制，需要感知到这个问题
                    self.compression_queue.task_done()
    
    async def _execute_compression(self, task: Dict[str, Any]):
        """执行压缩"""
        session_id = task['session_id']
        start_time = time.time()

        # 加载目标会话
        if not await self.data_source.load_session(session_id):
            raise Exception(f"无法加载会话进行压缩: {session_id}")

        # 获取消息
        messages = await self.data_source.get_messages(session_id)

        if len(messages) <= self.config.preserve_recent_count:
            print(f"⚠️ 消息数量不足，跳过压缩: {session_id}")
            return

        # 执行压缩
        compressed_data = await self._compress_messages(messages)

        # 保存压缩结果
        await self._save_compression_result(session_id, compressed_data)

        execution_time = time.time() - start_time

        print(f"✅ 压缩完成: {session_id}")
        print(f"   原始消息: {len(messages)}, 压缩后: {len(compressed_data.get('messages', []))}")
        print(f"   耗时: {execution_time:.1f}s")
    
    def _estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """估算token数量"""
        total = 0
        for msg in messages:
            content = msg.get('content', '')
            # 简单估算：中文1字符≈1token，英文1词≈1token
            chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
            english_words = len(content.replace('，', ' ').replace('。', ' ').split())
            total += chinese_chars + english_words
        return total
    
    async def _compress_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """压缩消息 - 生成结构化的压缩消息列表"""
        # 保留最近的消息
        recent_messages = messages[-self.config.preserve_recent_count:]

        # 需要压缩的消息
        messages_to_compress = messages[:-self.config.preserve_recent_count]

        if not messages_to_compress:
            return {
                'messages': messages,
                'summary': '无需压缩',
                'key_decisions': [],
                'compression_method': 'no_compression'
            }

        # 使用LLM进行智能压缩，生成结构化结果
        compression_result = await self._llm_intelligent_compress(messages_to_compress)

        # 构建最终的压缩消息列表
        compressed_messages = []

        # 添加压缩后的结构化消息
        compressed_messages.extend(compression_result.get('compressed_messages', []))

        # 添加最近的完整消息
        compressed_messages.extend(recent_messages)

        return {
            'messages': compressed_messages,
            'summary': compression_result.get('summary', ''),
            'key_decisions': compression_result.get('key_decisions', []),
            'compression_method': 'llm_intelligent',
            'original_count': len(messages),
            'compressed_count': len(compressed_messages)
        }
    
    async def _llm_intelligent_compress(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """使用LLM进行智能压缩，生成结构化结果"""
        # 格式化消息
        formatted = self._format_messages(messages)

        system_prompt = """你是专业的对话压缩助手，擅长将冗长的对话压缩为结构化的精简版本。

压缩要求：
1. 将相似的对话轮次合并为更简洁的消息
2. 保留所有重要决策和结论
3. 保留关键的用户需求和系统回复
4. 维护对话的逻辑流程和上下文关系

请以JSON格式返回：
{
    "compressed_messages": [
        {
            "message_id": "compressed_1",
            "role": "user",
            "content": "合并后的用户需求或问题",
            "metadata": {"compression_note": "合并了3条相似的用户消息"}
        },
        {
            "message_id": "compressed_2",
            "role": "assistant",
            "content": "合并后的助手回复和分析",
            "metadata": {"compression_note": "合并了助手的分析和建议"}
        }
    ],
    "summary": "整体对话摘要，包含主要讨论内容和结论",
    "key_decisions": ["重要决策1", "重要决策2"]
}"""

        prompt = f"请对以下对话历史进行智能压缩：\n\n{formatted}"

        response = await self.openai_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=2000
        )

        # 解析JSON结果
        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)

        # 验证和补充结果
        compressed_messages = result.get('compressed_messages', [])
        for i, msg in enumerate(compressed_messages):
            # 确保必要字段存在，由代码生成
            if 'message_id' not in msg:
                msg['message_id'] = f"compressed_{int(time.time())}_{i}"

            # 由代码自动添加的字段
            msg['timestamp'] = datetime.now().isoformat()
            msg['token_count'] = len(msg.get('content', '')) // 2

            # 确保metadata存在
            if 'metadata' not in msg:
                msg['metadata'] = {}

        return {
            'compressed_messages': compressed_messages,
            'summary': result.get('summary', ''),
            'key_decisions': result.get('key_decisions', [])
        }


    
    def _format_messages(self, messages: List[Dict[str, Any]]) -> str:
        """格式化消息用于LLM处理"""
        formatted = []
        for i, msg in enumerate(messages, 1):
            role = msg['role']
            content = msg['content']
            formatted.append(f"[{i}] {role}: {content}")

        return "\n".join(formatted)
    
    async def _save_compression_result(self, session_id: str, compressed_data: Dict[str, Any]):
        """保存压缩结果"""
        # 获取现有压缩版本
        existing = await self.data_source.get_compressed_contexts(session_id)
        next_version = len(existing) + 1

        # 计算压缩比
        original_count = compressed_data.get('original_count', 0)
        compressed_count = compressed_data.get('compressed_count', 0)
        compression_ratio = compressed_count / original_count if original_count > 0 else 0

        # 保存到数据源
        await self.data_source.save_compressed_context(
            session_id=session_id,
            compressed_data=compressed_data,
            version=next_version,
            compression_ratio=compression_ratio,
            metadata={
                'compression_id': str(uuid.uuid4()),
                'level': self.config.default_level.value,
                'algorithm': 'smart_llm_v2',
                'created_at': datetime.now().isoformat()
            }
        )

        print(f"💾 压缩结果已保存: {session_id} v{next_version}")


# 全局压缩器实例
_compressor: Optional[SmartCompressor] = None


def get_compressor(data_source: DataSourceInterface, config: Optional[CompressionConfig] = None) -> SmartCompressor:
    """获取全局压缩器实例"""
    global _compressor
    if _compressor is None:
        _compressor = SmartCompressor(data_source, config)
    return _compressor


def create_sqlite_compressor(session_manager, config: Optional[CompressionConfig] = None) -> SmartCompressor:
    """
    创建SQLite压缩器的便捷方法
    
    Args:
        session_manager: SQLiteSessionManager实例
        config: 压缩配置
        
    Returns:
        SmartCompressor实例
    """
    data_source = SQLiteDataSourceAdapter(session_manager)
    return SmartCompressor(data_source, config)
