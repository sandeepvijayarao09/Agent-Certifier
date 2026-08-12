import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
import json


class TestStatus(str, enum.Enum):
    pass_ = "pass"
    fail = "fail"
    warning = "warning"
    skip = "skip"


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False)
    category = Column(String(100), nullable=False)
    test_name = Column(String(255), nullable=False)
    status = Column(SAEnum(TestStatus), nullable=False)
    score = Column(Float, default=0.0, nullable=False)
    details_json = Column(Text, default="{}", nullable=False)
    duration_ms = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    agent = relationship("Agent", back_populates="test_results")

    @property
    def details(self):
        try:
            return json.loads(self.details_json)
        except Exception:
            return {}

    @details.setter
    def details(self, value):
        self.details_json = json.dumps(value)
