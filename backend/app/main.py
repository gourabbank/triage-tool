import json
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from . import models, schemas
from .database import Base, engine, get_db
from .brief_generator import get_generator
from .duplicates import find_duplicate
from .auth import require_reviewer
from .webhooks import send_accepted_webhook

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Internal Request Intake & Triage Tool")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _brief_to_dict(brief: models.Brief) -> dict:
    return {
        "id": brief.id,
        "problem_summary": brief.problem_summary,
        "likely_users": json.loads(brief.likely_users),
        "recommended_solution_type": brief.recommended_solution_type,
        "clarifying_questions": json.loads(brief.clarifying_questions),
        "risks": json.loads(brief.risks),
        "suggested_next_action": brief.suggested_next_action,
        "model_used": brief.model_used,
        "created_at": brief.created_at,
    }


def _request_to_out(req: models.Request) -> schemas.RequestOut:
    return schemas.RequestOut(
        id=req.id,
        raw_text=req.raw_text,
        submitted_by=req.submitted_by,
        created_at=req.created_at,
        status=req.status,
        owner=req.owner,
        priority=req.priority,
        notes=req.notes,
        duplicate_of=req.duplicate_of,
        brief=_brief_to_dict(req.brief) if req.brief else None,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/requests", response_model=schemas.RequestOut, status_code=201)
def create_request(payload: schemas.RequestCreate, db: Session = Depends(get_db)):
    """Submit a messy request; immediately generate a structured brief for it."""
    recent = (
        db.query(models.Request)
        .order_by(models.Request.created_at.desc())
        .limit(200)
        .all()
    )
    duplicate_id = find_duplicate(payload.raw_text, recent)

    req = models.Request(
        raw_text=payload.raw_text,
        submitted_by=payload.submitted_by,
        duplicate_of=duplicate_id,
    )
    db.add(req)
    db.flush()

    try:
        brief_data = get_generator().generate(payload.raw_text)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"Brief generation failed: {exc}")

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


@app.get("/requests", response_model=List[schemas.RequestOut])
def list_requests(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
    _: None = Depends(require_reviewer),
):
    query = db.query(models.Request)
    if status:
        query = query.filter(models.Request.status == status)
    if priority:
        query = query.filter(models.Request.priority == priority)
    reqs = query.order_by(models.Request.created_at.desc()).all()
    return [_request_to_out(r) for r in reqs]


@app.get("/requests/{request_id}", response_model=schemas.RequestOut)
def get_request(
    request_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_reviewer),
):
    req = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return _request_to_out(req)


@app.patch("/requests/{request_id}", response_model=schemas.RequestOut)
def update_triage(
    request_id: str,
    payload: schemas.TriageUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_reviewer),
):
    req = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    became_accepted = (
        updates.get("status") == "accepted" and req.status != "accepted"
    )

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

    if became_accepted:
        send_accepted_webhook({
            "request_id": req.id,
            "raw_text": req.raw_text,
            "owner": req.owner,
            "priority": req.priority,
        })

    return _request_to_out(req)


@app.get("/requests/{request_id}/audit", response_model=List[schemas.AuditEntryOut])
def get_audit_log(
    request_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_reviewer),
):
    req = db.query(models.Request).filter(models.Request.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return db.query(models.AuditEntry).filter(models.AuditEntry.request_id == request_id).all()


@app.get("/requests/export/csv")
def export_csv(db: Session = Depends(get_db)):
    """CSV export left open (not reviewer-gated) since the frontend serves
    it as a plain <a href> link, which can't attach a custom auth header."""
    import csv
    import io

    reqs = db.query(models.Request).order_by(models.Request.created_at.desc()).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "created_at", "status", "priority", "owner", "duplicate_of", "raw_text"])
    for r in reqs:
        writer.writerow([
            r.id, r.created_at, r.status, r.priority, r.owner or "",
            r.duplicate_of or "", r.raw_text.replace("\n", " "),
        ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=triage_queue.csv"},
    )