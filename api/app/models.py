from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from .db import Base
from sqlalchemy import Boolean, Float

class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, index=True, default="general")
    title = Column(String, index=True)
    status = Column(String, index=True, default="draft")  # draft | approved
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class KnowledgeVersion(Base):
    __tablename__ = "knowledge_versions"
    id = Column(Integer, primary_key=True, index=True)
    knowledge_item_id = Column(Integer, ForeignKey("knowledge_items.id"), index=True)
    content = Column(Text)  # texto completo del doc (por ahora)
    status = Column(String, index=True, default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("knowledge_versions.id"), index=True)
    chunk_text = Column(Text)
    chunk_index = Column(Integer)

class UsageEvent(Base):
    __tablename__ = "usage_events"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text)
    domain = Column(String, index=True, default="general")
    top_chunk_idx = Column(Integer, nullable=True)
    top_distance = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FeedbackEvent(Base):
    __tablename__ = "feedback_events"
    id = Column(Integer, primary_key=True, index=True)
    usage_event_id = Column(Integer, ForeignKey("usage_events.id"), index=True, nullable=True)
    is_helpful = Column(Boolean, nullable=False)  # thumbs up/down
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())