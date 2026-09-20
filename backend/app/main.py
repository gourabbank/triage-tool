from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

import json
from .brief_generator import generate_mock_brief

def _request_to_out(req: models.Request) -> schemas.RequestOut:
    brief_out = None
    if req.brief:
        b = req.brief
        brief_out = schemas.BriefOut(
            id=b.id,
            created_at=b.created_at,
            problem_summary=b.problem_summary,
            likely_users=json.loads(b.likely_users),
            recommended_solution_type=b.recommended_solution_type,
            clarifying_questions=json.loads(b.clarifying_questions),
            risks=json.loads(b.risks),
            suggested_next_action=b.suggested_next_action,
            model_used=b.model_used,
        )
    return schemas.RequestOut(
        id=req.id,
        raw_text=req.raw_text,
        submitted_by=req.submitted_by,
        created_at=req.created_at,
        status=req.status,
        brief=brief_out,
    )

@app.post("/requests", response_model=schemas.RequestOut, status_code=201)
def create_request(payload: schemas.RequestCreate, db: Session = Depends(get_db)):
    req = models.Request(raw_text=payload.raw_text, submitted_by=payload.submitted_by)
    db.add(req)
    db.flush()

    brief_data = generate_mock_brief(payload.raw_text)
    brief = models.Brief(
        request_id=req.id,
        problem_summary=brief_data.problem_summary,
        likely_users=json.dumps(brief_data.likely_users),
        recommended_solution_type=brief_data.recommended_solution_type,
        clarifying_questions=json.dumps(brief_data.clarifying_questions),
        risks=json.dumps(brief_data.risks),
        suggested_next_action=brief_data.suggested_next_action,
        model_used=brief_data.model_used,
    )
    db.add(brief)
    db.commit()
    db.refresh(req)
    return _request_to_out(req)

@app.get("/requests", response_model=list[schemas.RequestOut])
def list_requests(db: Session = Depends(get_db)):
    return [_request_to_out(r) for r in db.query(models.Request).all()]

@app.get("/requests", response_model=list[schemas.RequestOut])
def list_requests(db: Session = Depends(get_db)):
    return db.query(models.Request).all()