from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .db import ENGINE, Base, SessionLocal
from . import models, schemas

app = FastAPI(title="GovRAG API")
Base.metadata.create_all(bind=ENGINE)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/items")
def create_item(payload: schemas.CreateItem, db: Session = Depends(get_db)):
    item = models.KnowledgeItem(title=payload.title, domain=payload.domain)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.post("/versions")
def create_version(payload: schemas.CreateVersion, db: Session = Depends(get_db)):
    v = models.KnowledgeVersion(
        knowledge_item_id=payload.knowledge_item_id,
        content=payload.content,
        status="draft",
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v

@app.post("/approve")
def approve_version(payload: schemas.ApproveVersion, db: Session = Depends(get_db)):
    v = db.query(models.KnowledgeVersion).filter(models.KnowledgeVersion.id == payload.version_id).first()
    if not v:
        return {"error": "version not found"}
    v.status = "approved"
    # también marca el item como approved (simple)
    item = db.query(models.KnowledgeItem).filter(models.KnowledgeItem.id == v.knowledge_item_id).first()
    if item:
        item.status = "approved"
    db.commit()
    return {"approved": True, "version_id": v.id}

@app.get("/items")
def list_items(db: Session = Depends(get_db)):
    return db.query(models.KnowledgeItem).all()

