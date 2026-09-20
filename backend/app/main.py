from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models, schemas
from .database import Base, engine, get_db
from fastapi import FastAPI, Depends, HTTPException

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
        owner=req.owner,
        priority=req.priority,
        notes=req.notes,
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

from .schemas import TriageUpdate, AuditEntryOut

@app.patch("/requests/{request_id}", response_model=schemas.RequestOut)
def update_triage(request_id: str, payload: schemas.TriageUpdate, db: Session = Depends(get_db)):
    req = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    for field, new_value in updates.items():
        old_value = getattr(req, field)
        if old_value != new_value:
            db.add(models.AuditEntry(
                request_id=req.id,
                field=field,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else None,
            ))
            setattr(req, field, new_value)

    db.commit()
    db.refresh(req)
    return _request_to_out(req)


@app.get("/requests/{request_id}/audit", response_model=list[schemas.AuditEntryOut])
def get_audit_log(request_id: str, db: Session = Depends(get_db)):
    req = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return db.query(models.AuditEntry).filter(models.AuditEntry.request_id == request_id).all()

@app.get("/requests/{request_id}", response_model=schemas.RequestOut)
def get_request(request_id: str, db: Session = Depends(get_db)):
    req = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return _request_to_out(req)