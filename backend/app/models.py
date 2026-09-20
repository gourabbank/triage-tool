import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy import ForeignKey
from .database import Base
from sqlalchemy.orm import relationship

def gen_id() -> str:
    return uuid.uuid4().hex[:12]

class Request(Base):
    __tablename__ = "requests"

    id = Column(String, primary_key=True, default=gen_id)
    raw_text = Column(Text, nullable=False)
    submitted_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="new", nullable=False)
    brief = relationship("Brief", back_populates="request", uselist=False)
    
from datetime import datetime  # add this import if not already there

class Brief(Base):
    __tablename__ = "briefs"

    id = Column(String, primary_key=True, default=gen_id)
    request_id = Column(String, ForeignKey("requests.id"), nullable=False, unique=True)
    problem_summary = Column(Text, nullable=False)
    likely_users = Column(Text, nullable=False)
    recommended_solution_type = Column(String, nullable=False)
    clarifying_questions = Column(Text, nullable=False)
    risks = Column(Text, nullable=False)
    suggested_next_action = Column(Text, nullable=False)
    model_used = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)   # ← added

    request = relationship("Request", back_populates="brief")