from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/requests", response_model=schemas.RequestOut, status_code=201)
def create_request(payload: schemas.RequestCreate, db: Session = Depends(get_db)):
    req = models.Request(raw_text=payload.raw_text, submitted_by=payload.submitted_by)
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

@app.get("/requests", response_model=list[schemas.RequestOut])
def list_requests(db: Session = Depends(get_db)):
    return db.query(models.Request).all()