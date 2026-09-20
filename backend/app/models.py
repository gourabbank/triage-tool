import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from .database import Base

def gen_id() -> str:
    return uuid.uuid4().hex[:12]

class Request(Base):
    __tablename__ = "requests"

    id = Column(String, primary_key=True, default=gen_id)
    raw_text = Column(Text, nullable=False)
    submitted_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="new", nullable=False)