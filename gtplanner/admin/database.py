"""
GTPlanner Admin - MySQL Database Configuration
使用SQLAlchemy管理MySQL数据库连接
"""

import os
from typing import AsyncGenerator
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, Boolean, Index
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import QueuePool
from datetime import datetime
from contextlib import contextmanager

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库连接URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:4813494d137e1631bba301d5acab6e7bb7aa74ce1185d456565ef51d737677b2@172.24.140.110:3306/GTPlanner"
)

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", 5)),
    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", 10)),
    pool_timeout=int(os.getenv("DATABASE_POOL_TIMEOUT", 30)),
    pool_recycle=int(os.getenv("DATABASE_POOL_RECYCLE", 3600)),
    pool_pre_ping=True,  # 自动检测连接有效性
    echo=False,  # 设置为True可以查看SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


# ==================== 数据库模型 ====================

class DBSession(Base):
    """会话表模型（重命名为DBSession避免与Session类冲突）"""
    __tablename__ = "sessions"

    session_id = Column(String(64), primary_key=True, comment="会话ID")
    title = Column(String(255), nullable=False, comment="会话标题")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    project_stage = Column(String(50), default="requirements", nullable=False, comment="项目阶段")
    total_messages = Column(Integer, default=0, nullable=False, comment="消息总数")
    total_tokens = Column(Integer, default=0, nullable=False, comment="token总数")
    session_metadata = Column(Text, nullable=True, comment="元数据（JSON格式）")
    status = Column(String(20), default="active", nullable=False, comment="状态：active, archived, deleted")

    # 索引
    __table_args__ = (
        Index("idx_sessions_created_at", "created_at"),
        Index("idx_sessions_updated_at", "updated_at"),
        Index("idx_sessions_status", "status"),
    )


class Message(Base):
    """消息表模型"""
    __tablename__ = "messages"

    message_id = Column(String(64), primary_key=True, comment="消息ID")
    session_id = Column(String(64), nullable=False, comment="会话ID")
    role = Column(String(20), nullable=False, comment="角色：user, assistant, system, tool")
    content = Column(Text, nullable=False, comment="消息内容")
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment="时间戳")
    token_count = Column(Integer, nullable=True, comment="token数量")
    message_metadata = Column(Text, nullable=True, comment="元数据（JSON格式）")
    tool_calls = Column(Text, nullable=True, comment="工具调用信息（JSON格式）")
    tool_call_id = Column(String(64), nullable=True, comment="工具调用ID")
    parent_message_id = Column(String(64), nullable=True, comment="父消息ID")

    # 索引
    __table_args__ = (
        Index("idx_messages_session_id", "session_id"),
        Index("idx_messages_timestamp", "timestamp"),
        Index("idx_messages_session_timestamp", "session_id", "timestamp"),
    )


# ==================== 数据库操作函数 ====================

def init_db():
    """初始化数据库，创建所有表"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ MySQL数据库表创建成功")
    except Exception as e:
        print(f"❌ MySQL数据库表创建失败: {e}")
        raise


@contextmanager
def get_db_session() -> Session:
    """
    获取数据库会话的上下文管理器

    用法:
        with get_db_session() as db:
            sessions = db.query(DBSession).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session_by_id(db: Session, session_id: str) -> DBSession | None:
    """根据ID获取会话"""
    return db.query(DBSession).filter(DBSession.session_id == session_id).first()


def list_sessions(db: Session, limit: int = 50, offset: int = 0, status: str = "active") -> list[DBSession]:
    """列出会话"""
    query = db.query(DBSession).filter(DBSession.status == status)
    return query.order_by(DBSession.updated_at.desc()).offset(offset).limit(limit).all()


def create_session(db: Session, title: str, project_stage: str = "requirements", metadata: dict = None) -> DBSession:
    """创建新会话"""
    import uuid
    import json

    session = DBSession(
        session_id=str(uuid.uuid4()),
        title=title,
        project_stage=project_stage,
        session_metadata=json.dumps(metadata) if metadata else None,
        status="active"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def update_session(db: Session, session_id: str, **kwargs) -> bool:
    """更新会话"""
    import json

    session = get_session_by_id(db, session_id)
    if not session:
        return False

    if "title" in kwargs:
        session.title = kwargs["title"]
    if "project_stage" in kwargs:
        session.project_stage = kwargs["project_stage"]
    if "status" in kwargs:
        session.status = kwargs["status"]
    if "metadata" in kwargs:
        session.session_metadata = json.dumps(kwargs["metadata"]) if kwargs["metadata"] else None

    db.commit()
    return True


def delete_session(db: Session, session_id: str) -> bool:
    """删除会话（软删除）"""
    session = get_session_by_id(db, session_id)
    if not session:
        return False

    session.status = "deleted"
    db.commit()
    return True


def get_messages(db: Session, session_id: str, limit: int = 100) -> list[Message]:
    """获取会话的消息列表"""
    return db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.timestamp.asc()).limit(limit).all()


def session_to_dict(session: DBSession) -> dict:
    """将DBSession对象转换为字典"""
    import json

    return {
        "session_id": session.session_id,
        "title": session.title,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "project_stage": session.project_stage,
        "total_messages": session.total_messages,
        "total_tokens": session.total_tokens,
        "metadata": json.loads(session.session_metadata) if session.session_metadata else {},
        "status": session.status
    }


def message_to_dict(message: Message) -> dict:
    """将Message对象转换为字典"""
    import json

    return {
        "message_id": message.message_id,
        "session_id": message.session_id,
        "role": message.role,
        "content": message.content,
        "timestamp": message.timestamp.isoformat() if message.timestamp else None,
        "token_count": message.token_count,
        "metadata": json.loads(message.message_metadata) if message.message_metadata else {},
        "tool_calls": json.loads(message.tool_calls) if message.tool_calls else [],
        "parent_message_id": message.parent_message_id
    }


if __name__ == "__main__":
    # 测试数据库连接
    print("🔧 测试MySQL数据库连接")
    print(f"数据库URL: {DATABASE_URL}")

    try:
        # 初始化数据库
        init_db()

        # 测试查询
        with get_db_session() as db:
            sessions = db.query(DBSession).limit(5).all()
            print(f"✅ 数据库连接成功，当前共有 {len(sessions)} 个会话")

            for session in sessions:
                print(f"  - {session.session_id[:8]}... | {session.title}")

    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
