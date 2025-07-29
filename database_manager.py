"""
数据库管理器
支持SQLite数据库，替代JSON文件存储
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "gtplanner.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建知识库文档表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        keywords TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建BadCase表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS badcases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        feedback TEXT NOT NULL,
                        relevant_docs_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建系统配置表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def save_knowledge_document(self, title: str, content: str, keywords: List[str] = None) -> int:
        """保存知识库文档"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                keywords_json = json.dumps(keywords) if keywords else None
                
                cursor.execute('''
                    INSERT INTO knowledge_documents (title, content, keywords)
                    VALUES (?, ?, ?)
                ''', (title, content, keywords_json))
                
                doc_id = cursor.lastrowid
                conn.commit()
                logger.info(f"知识库文档保存成功，ID: {doc_id}")
                return doc_id
                
        except Exception as e:
            logger.error(f"保存知识库文档失败: {e}")
            raise
    
    def get_knowledge_documents(self) -> List[Dict[str, Any]]:
        """获取所有知识库文档"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, title, content, keywords FROM knowledge_documents')
                
                documents = []
                for row in cursor.fetchall():
                    doc = {
                        'id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'keywords': json.loads(row[3]) if row[3] else []
                    }
                    documents.append(doc)
                
                return documents
                
        except Exception as e:
            logger.error(f"获取知识库文档失败: {e}")
            return []
    
    def save_badcase(self, user_id: str, question: str, answer: str, 
                     feedback: str, relevant_docs_count: int = 0) -> int:
        """保存BadCase"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO badcases (user_id, question, answer, feedback, relevant_docs_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, question, answer, feedback, relevant_docs_count))
                
                badcase_id = cursor.lastrowid
                conn.commit()
                logger.info(f"BadCase保存成功，ID: {badcase_id}")
                return badcase_id
                
        except Exception as e:
            logger.error(f"保存BadCase失败: {e}")
            raise
    
    def get_badcases(self, user_id: Optional[str] = None, 
                     feedback: Optional[str] = None, 
                     limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取BadCase列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT id, user_id, question, answer, feedback, relevant_docs_count, created_at FROM badcases"
                params = []
                
                conditions = []
                if user_id:
                    conditions.append("user_id = ?")
                    params.append(user_id)
                if feedback:
                    conditions.append("feedback = ?")
                    params.append(feedback)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC"
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query, params)
                
                badcases = []
                for row in cursor.fetchall():
                    badcase = {
                        'id': row[0],
                        'user_id': row[1],
                        'question': row[2],
                        'answer': row[3],
                        'feedback': row[4],
                        'relevant_docs_count': row[5],
                        'created_at': row[6]
                    }
                    badcases.append(badcase)
                
                return badcases
                
        except Exception as e:
            logger.error(f"获取BadCase失败: {e}")
            return []
    
    def get_badcase_stats(self) -> Dict[str, Any]:
        """获取BadCase统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 总数量
                cursor.execute("SELECT COUNT(*) FROM badcases")
                total_count = cursor.fetchone()[0]
                
                # 按反馈类型统计
                cursor.execute("SELECT feedback, COUNT(*) FROM badcases GROUP BY feedback")
                feedback_stats = dict(cursor.fetchall())
                
                # 按用户统计
                cursor.execute("SELECT user_id, COUNT(*) FROM badcases GROUP BY user_id ORDER BY COUNT(*) DESC")
                user_stats = dict(cursor.fetchall())
                
                return {
                    'total_count': total_count,
                    'feedback_stats': feedback_stats,
                    'user_stats': user_stats
                }
                
        except Exception as e:
            logger.error(f"获取BadCase统计失败: {e}")
            return {'total_count': 0, 'feedback_stats': {}, 'user_stats': {}}
    
    def migrate_from_json(self, knowledge_base_path: str, badcase_path: str):
        """从JSON文件迁移数据到数据库"""
        try:
            # 迁移知识库
            if Path(knowledge_base_path).exists():
                with open(knowledge_base_path, 'r', encoding='utf-8') as f:
                    knowledge_data = json.load(f)
                
                for doc in knowledge_data:
                    self.save_knowledge_document(
                        title=doc.get('title', ''),
                        content=doc.get('content', ''),
                        keywords=doc.get('keywords', [])
                    )
                logger.info(f"知识库迁移完成，共迁移 {len(knowledge_data)} 个文档")
            
            # 迁移BadCase
            if Path(badcase_path).exists():
                with open(badcase_path, 'r', encoding='utf-8') as f:
                    badcase_data = json.load(f)
                
                for badcase in badcase_data:
                    self.save_badcase(
                        user_id=badcase.get('user_id', 'default_user'),
                        question=badcase.get('question', ''),
                        answer=badcase.get('answer', ''),
                        feedback=badcase.get('feedback', ''),
                        relevant_docs_count=badcase.get('relevant_docs_count', 0)
                    )
                logger.info(f"BadCase迁移完成，共迁移 {len(badcase_data)} 个记录")
                
        except Exception as e:
            logger.error(f"数据迁移失败: {e}")
            raise 