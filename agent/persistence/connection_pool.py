"""
数据库连接池优化

为GTPlanner提供高性能的数据库连接池管理，包括：
- 连接池管理
- 连接复用
- 自动重连
- 连接健康检查
- 性能监控
"""

import asyncio
import sqlite3
import threading
import time
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from contextlib import contextmanager
from queue import Queue, Empty
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ConnectionStats:
    """连接统计信息"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    created_connections: int = 0
    closed_connections: int = 0
    failed_connections: int = 0
    avg_connection_time: float = 0.0
    max_connection_time: float = 0.0


class OptimizedConnectionPool:
    """优化的连接池"""
    
    def __init__(
        self,
        db_path: str,
        min_connections: int = 2,
        max_connections: int = 10,
        connection_timeout: int = 30,
        idle_timeout: int = 300,
        health_check_interval: int = 60
    ):
        """
        初始化连接池
        
        Args:
            db_path: 数据库文件路径
            min_connections: 最小连接数
            max_connections: 最大连接数
            connection_timeout: 连接超时时间（秒）
            idle_timeout: 空闲超时时间（秒）
            health_check_interval: 健康检查间隔（秒）
        """
        self.db_path = db_path
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.idle_timeout = idle_timeout
        self.health_check_interval = health_check_interval
        
        # 连接池
        self._pool: Queue = Queue(maxsize=max_connections)
        self._active_connections: Dict[int, sqlite3.Connection] = {}
        self._connection_times: Dict[int, float] = {}
        self._connection_last_used: Dict[int, float] = {}
        
        # 统计信息
        self.stats = ConnectionStats()
        
        # 线程安全
        self._lock = threading.RLock()
        self._connection_counter = 0
        
        # 健康检查
        self._health_check_thread: Optional[threading.Thread] = None
        self._stop_health_check = threading.Event()
        
        # 初始化连接池
        self._initialize_pool()
        self._start_health_check()
        
        logger.info(f"连接池初始化完成: {db_path}, 连接数: {min_connections}-{max_connections}")
    
    def _initialize_pool(self):
        """初始化连接池"""
        with self._lock:
            for _ in range(self.min_connections):
                conn = self._create_connection()
                if conn:
                    self._pool.put(conn)
                    self.stats.idle_connections += 1
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """创建新连接"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=self.connection_timeout,
                check_same_thread=False
            )
            
            # 优化设置
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA cache_size = -64000;")  # 64MB cache
            conn.execute("PRAGMA temp_store = MEMORY;")
            conn.execute("PRAGMA mmap_size = 268435456;")  # 256MB mmap
            
            # 设置行工厂
            conn.row_factory = sqlite3.Row
            
            self.stats.created_connections += 1
            self.stats.total_connections += 1
            
            logger.debug(f"创建新数据库连接: {id(conn)}")
            return conn
            
        except Exception as e:
            logger.error(f"创建数据库连接失败: {e}")
            self.stats.failed_connections += 1
            return None
    
    def _is_connection_healthy(self, conn: sqlite3.Connection) -> bool:
        """检查连接健康状态"""
        try:
            conn.execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False
    
    def _start_health_check(self):
        """启动健康检查"""
        if self._health_check_thread and self._health_check_thread.is_alive():
            return
        
        self._stop_health_check.clear()
        self._health_check_thread = threading.Thread(
            target=self._health_check_loop,
            daemon=True
        )
        self._health_check_thread.start()
        logger.info("数据库连接健康检查已启动")
    
    def _health_check_loop(self):
        """健康检查循环"""
        while not self._stop_health_check.is_set():
            try:
                self._perform_health_check()
                self._stop_health_check.wait(self.health_check_interval)
            except Exception as e:
                logger.error(f"健康检查出错: {e}")
                time.sleep(5)
    
    def _perform_health_check(self):
        """执行健康检查"""
        with self._lock:
            # 检查空闲连接
            idle_connections = []
            while not self._pool.empty():
                try:
                    conn = self._pool.get_nowait()
                    if self._is_connection_healthy(conn):
                        idle_connections.append(conn)
                    else:
                        conn.close()
                        self.stats.closed_connections += 1
                        self.stats.total_connections -= 1
                except Empty:
                    break
            
            # 重新放回健康的空闲连接
            for conn in idle_connections:
                self._pool.put(conn)
            
            # 检查活跃连接
            unhealthy_connections = []
            for conn_id, conn in self._active_connections.items():
                if not self._is_connection_healthy(conn):
                    unhealthy_connections.append(conn_id)
            
            # 移除不健康的连接
            for conn_id in unhealthy_connections:
                conn = self._active_connections.pop(conn_id, None)
                if conn:
                    conn.close()
                    self.stats.closed_connections += 1
                    self.stats.total_connections -= 1
                    self.stats.active_connections -= 1
    
    def get_connection(self) -> Optional[sqlite3.Connection]:
        """获取连接"""
        with self._lock:
            # 尝试从池中获取空闲连接
            try:
                conn = self._pool.get_nowait()
                self.stats.idle_connections -= 1
            except Empty:
                # 池中没有空闲连接，创建新连接
                if self.stats.total_connections < self.max_connections:
                    conn = self._create_connection()
                    if not conn:
                        return None
                else:
                    # 等待连接可用
                    try:
                        conn = self._pool.get(timeout=self.connection_timeout)
                        self.stats.idle_connections -= 1
                    except Empty:
                        logger.error("获取数据库连接超时")
                        return None
            
            # 记录连接使用
            conn_id = id(conn)
            self._active_connections[conn_id] = conn
            self._connection_times[conn_id] = time.time()
            self._connection_last_used[conn_id] = time.time()
            
            self.stats.active_connections += 1
            
            logger.debug(f"获取数据库连接: {conn_id}")
            return conn
    
    def return_connection(self, conn: sqlite3.Connection):
        """归还连接"""
        if not conn:
            return
        
        conn_id = id(conn)
        
        with self._lock:
            if conn_id in self._active_connections:
                # 更新连接时间统计
                if conn_id in self._connection_times:
                    connection_time = time.time() - self._connection_times[conn_id]
                    self.stats.avg_connection_time = (
                        (self.stats.avg_connection_time * (self.stats.active_connections - 1) + connection_time) /
                        self.stats.active_connections
                    )
                    self.stats.max_connection_time = max(
                        self.stats.max_connection_time, connection_time
                    )
                
                # 移除活跃连接记录
                self._active_connections.pop(conn_id, None)
                self._connection_times.pop(conn_id, None)
                self._connection_last_used.pop(conn_id, None)
                
                self.stats.active_connections -= 1
                
                # 检查连接健康状态
                if self._is_connection_healthy(conn):
                    # 连接健康，放回池中
                    try:
                        self._pool.put_nowait(conn)
                        self.stats.idle_connections += 1
                        logger.debug(f"归还数据库连接: {conn_id}")
                    except Exception:
                        # 池已满，关闭连接
                        conn.close()
                        self.stats.closed_connections += 1
                        self.stats.total_connections -= 1
                else:
                    # 连接不健康，关闭连接
                    conn.close()
                    self.stats.closed_connections += 1
                    self.stats.total_connections -= 1
    
    def close_all_connections(self):
        """关闭所有连接"""
        with self._lock:
            # 关闭空闲连接
            while not self._pool.empty():
                try:
                    conn = self._pool.get_nowait()
                    conn.close()
                    self.stats.closed_connections += 1
                except Empty:
                    break
            
            # 关闭活跃连接
            for conn in self._active_connections.values():
                conn.close()
                self.stats.closed_connections += 1
            
            self._active_connections.clear()
            self._connection_times.clear()
            self._connection_last_used.clear()
            
            self.stats.active_connections = 0
            self.stats.idle_connections = 0
            self.stats.total_connections = 0
        
        # 停止健康检查
        self._stop_health_check.set()
        if self._health_check_thread:
            self._health_check_thread.join(timeout=5.0)
        
        logger.info("所有数据库连接已关闭")
    
    def get_stats(self) -> ConnectionStats:
        """获取连接统计信息"""
        with self._lock:
            return ConnectionStats(
                total_connections=self.stats.total_connections,
                active_connections=self.stats.active_connections,
                idle_connections=self.stats.idle_connections,
                created_connections=self.stats.created_connections,
                closed_connections=self.stats.closed_connections,
                failed_connections=self.stats.failed_connections,
                avg_connection_time=self.stats.avg_connection_time,
                max_connection_time=self.stats.max_connection_time
            )
    
    def optimize_database(self):
        """优化数据库"""
        conn = self.get_connection()
        if not conn:
            return
        
        try:
            # 执行优化操作
            conn.execute("PRAGMA optimize;")
            conn.execute("VACUUM;")
            conn.commit()
            logger.info("数据库优化完成")
        except Exception as e:
            logger.error(f"数据库优化失败: {e}")
        finally:
            self.return_connection(conn)


@contextmanager
def get_db_connection(pool: OptimizedConnectionPool):
    """获取数据库连接的上下文管理器"""
    conn = pool.get_connection()
    if not conn:
        raise Exception("无法获取数据库连接")
    
    try:
        yield conn
    finally:
        pool.return_connection(conn)


# 全局连接池实例
_global_pool: Optional[OptimizedConnectionPool] = None


def get_global_connection_pool(db_path: str = "gtplanner_conversations.db") -> OptimizedConnectionPool:
    """获取全局连接池实例"""
    global _global_pool
    if _global_pool is None:
        _global_pool = OptimizedConnectionPool(db_path)
    return _global_pool


def close_global_connection_pool():
    """关闭全局连接池"""
    global _global_pool
    if _global_pool:
        _global_pool.close_all_connections()
        _global_pool = None
