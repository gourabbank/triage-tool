from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class RequestCreate(BaseModel):
    raw_text: str = Field(min_length=10)
    submitted_by: Optional[str] = None

class RequestOut(BaseModel):
    id: str
    raw_text: str
    submitted_by: Optional[str]
    created_at: datetime
    status: str

    class Config:
        from_attributes = True
        
from typing import List

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class BriefSchema(BaseModel):
    problem_summary: str = Field(min_length=1)
    likely_users: List[str] = Field(default_factory=list)
    recommended_solution_type: str
    clarifying_questions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    suggested_next_action: str
    model_used: str = "mock-llm"

class BriefOut(BriefSchema):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime

class RequestCreate(BaseModel):
    raw_text: str = Field(min_length=10)
    submitted_by: Optional[str] = None

class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    raw_text: str
    submitted_by: Optional[str]
    created_at: datetime
    status: str
    brief: Optional[BriefOut] = None