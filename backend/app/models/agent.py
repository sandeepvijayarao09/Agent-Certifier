import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class AgentStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    language = Column(String(50), nullable=False)
    file_content = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=False)
    status = Column(SAEnum(AgentStatus), default=AgentStatus.pending, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    test_results = relationship("TestResult", back_populates="agent", cascade="all, delete-orphan")
