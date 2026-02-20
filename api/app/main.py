from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from . import models, schemas
from .db import ENGINE, Base, SessionLocal
from .rag import retrieve
from .trust import predict_trust

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
    v = (
        db.query(models.KnowledgeVersion)
        .filter(models.KnowledgeVersion.id == payload.version_id)
        .first()
    )
    if not v:
        return {"error": "version not found"}

    v.status = "approved"

    item = (
        db.query(models.KnowledgeItem)
        .filter(models.KnowledgeItem.id == v.knowledge_item_id)
        .first()
    )
    if item:
        item.status = "approved"

    db.commit()
    return {"approved": True, "version_id": v.id}


@app.get("/items")
def list_items(db: Session = Depends(get_db)):
    return db.query(models.KnowledgeItem).all()


@app.post("/ask")
def ask(payload: schemas.AskRequest, db: Session = Depends(get_db)):
    results = retrieve(payload.question, top_k=payload.top_k, domain=payload.domain)

    top_idx = None
    top_dist = None
    answer = "I couldn't find approved knowledge for this domain yet."
    citations = []

    if results:
        top = results[0]
        top_idx = top["idx"]
        top_dist = top["distance"]
        answer = top["text"]
        citations = [{
            "source": "approved_knowledge",
            "domain": top.get("domain"),
            "knowledge_item_id": top.get("knowledge_item_id"),
            "version_id": top.get("version_id"),
            "chunk_idx": top["idx"],
            "distance": top["distance"],
        }]

    # Log usage (this becomes ML training data later)
    usage = models.UsageEvent(
        question=payload.question,
        domain=payload.domain or "general",
        top_chunk_idx=top_idx,
        top_distance=top_dist,
    )
    db.add(usage)
    db.commit()
    db.refresh(usage)

    # Predict trust score (may be None if model file doesn't exist yet)
    trust_score = predict_trust(
        question=payload.question,
        top_distance=top_dist,
        has_retrieval=(top_idx is not None),
        comment=None,
    )

    # Label + pretty formatting
    trust_label = None
    trust_score_out = None
    if trust_score is not None:
        trust_score_out = round(trust_score, 4)
        if trust_score >= 0.8:
            trust_label = "high"
        elif trust_score >= 0.5:
            trust_label = "medium"
        else:
            trust_label = "low"

    return {
        "usage_event_id": usage.id,
        "question": payload.question,
        "domain": payload.domain,
        "answer": answer,
        "citations": citations,
        "retrieved": results,
        "trust_score": trust_score_out,
        "trust_label": trust_label,
    }


@app.post("/feedback")
def feedback(payload: schemas.FeedbackRequest, db: Session = Depends(get_db)):
    fb = models.FeedbackEvent(
        usage_event_id=payload.usage_event_id,
        is_helpful=payload.is_helpful,
        comment=payload.comment,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return {"ok": True, "feedback_id": fb.id}