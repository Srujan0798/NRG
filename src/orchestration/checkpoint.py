"""Conversation checkpointing for LangGraph with Postgres persistence."""

import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class CheckpointRecord(Base):
    """Stores conversation checkpoints."""
    __tablename__ = 'conversation_checkpoints'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False, index=True)
    thread_id = Column(String(36), nullable=False, index=True)
    checkpoint_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc))


class PostgresSaver:
    """Postgres-based checkpoint saver for LangGraph."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", 
            "postgresql://nrg:nrg_secret@localhost:5432/nrg"
        )
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve checkpoint by session_id."""
        session = self.Session()
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            record = session.query(CheckpointRecord).filter(
                CheckpointRecord.thread_id == thread_id
            ).order_by(CheckpointRecord.updated_at.desc()).first()
            
            if record:
                return json.loads(record.checkpoint_json)
            return None
        finally:
            session.close()
    
    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any]) -> None:
        """Store checkpoint."""
        session = self.Session()
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            session_id = checkpoint.get("session_id", thread_id)
            
            # Update existing or create new
            record = session.query(CheckpointRecord).filter(
                CheckpointRecord.thread_id == thread_id
            ).first()
            
            if record:
                record.checkpoint_json = json.dumps(checkpoint)
                record.updated_at = datetime.now(timezone.utc)
            else:
                record = CheckpointRecord(
                    session_id=session_id,
                    thread_id=thread_id,
                    checkpoint_json=json.dumps(checkpoint)
                )
                session.add(record)
            
            session.commit()
        finally:
            session.close()
    
    def list(self, config: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """List recent checkpoints for a session."""
        session = self.Session()
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            records = session.query(CheckpointRecord).filter(
                CheckpointRecord.thread_id == thread_id
            ).order_by(CheckpointRecord.updated_at.desc()).limit(limit).all()
            
            return [json.loads(r.checkpoint_json) for r in records]
        finally:
            session.close()
    
    def delete(self, config: Dict[str, Any]) -> None:
        """Delete checkpoint."""
        session = self.Session()
        try:
            thread_id = config.get("configurable", {}).get("thread_id")
            session.query(CheckpointRecord).filter(
                CheckpointRecord.thread_id == thread_id
            ).delete()
            session.commit()
        finally:
            session.close()


class SqliteSaver:
    """SQLite-based checkpoint saver for development."""
    
    def __init__(self, db_path: str = "nrg_checkpoints.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                thread_id TEXT NOT NULL,
                checkpoint_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_thread ON checkpoints(thread_id)")
        conn.commit()
        conn.close()
    
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        import sqlite3
        thread_id = config.get("configurable", {}).get("thread_id")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT checkpoint_json FROM checkpoints WHERE thread_id = ? ORDER BY updated_at DESC LIMIT 1",
            (thread_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any]) -> None:
        import sqlite3
        thread_id = config.get("configurable", {}).get("thread_id")
        session_id = checkpoint.get("session_id", thread_id)
        
        conn = sqlite3.connect(self.db_path)
        # Delete old checkpoint for this thread
        conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
        # Insert new
        conn.execute(
            "INSERT INTO checkpoints (session_id, thread_id, checkpoint_json) VALUES (?, ?, ?)",
            (session_id, thread_id, json.dumps(checkpoint))
        )
        conn.commit()
        conn.close()
    
    def list(self, config: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        import sqlite3
        thread_id = config.get("configurable", {}).get("thread_id")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT checkpoint_json FROM checkpoints WHERE thread_id = ? ORDER BY updated_at DESC LIMIT ?",
            (thread_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [json.loads(r[0]) for r in rows]
    
    def delete(self, config: Dict[str, Any]) -> None:
        import sqlite3
        thread_id = config.get("configurable", {}).get("thread_id")
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
        conn.commit()
        conn.close()


def get_checkpointer():
    """Get appropriate checkpointer based on environment."""
    if os.getenv("DATABASE_URL", "").startswith("postgresql"):
        return PostgresSaver()
    return SqliteSaver()
