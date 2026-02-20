import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from api.app.db import SessionLocal
from api.app import models

INDEX_PATH = "data/index/faiss.index"
META_PATH = "data/index/chunks.jsonl"

model = SentenceTransformer("all-MiniLM-L6-v2")


def get_approved_versions(db):
    return (
        db.query(models.KnowledgeVersion)
        .filter(models.KnowledgeVersion.status == "approved")
        .all()
    )


def chunk_text(text, size=200):
    words = text.split()
    for i in range(0, len(words), size):
        yield " ".join(words[i:i + size])


def main():
    db = SessionLocal()

    versions = get_approved_versions(db)

    # Build docs with metadata (this becomes our idx->chunk mapping)
    docs = []  # each: {text, domain, knowledge_item_id, version_id}

    for v in versions:
        item = (
            db.query(models.KnowledgeItem)
            .filter(models.KnowledgeItem.id == v.knowledge_item_id)
            .first()
        )
        domain = item.domain if item else "general"

        for ch in chunk_text(v.content):
            docs.append({
                "text": ch,
                "domain": domain,
                "knowledge_item_id": v.knowledge_item_id,
                "version_id": v.id,
            })

    os.makedirs("data/index", exist_ok=True)

    if not docs:
        print("No approved content found.")
        # Write empty meta for clarity
        with open(META_PATH, "w", encoding="utf-8") as f:
            pass
        return

    # Create the plain list of texts in the same order as docs
    documents = [d["text"] for d in docs]

    # 1) Save idx -> chunk metadata mapping (includes text)
    with open(META_PATH, "w", encoding="utf-8") as f:
        for i, d in enumerate(docs):
            out = {"idx": i, **d}
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    # 2) Build FAISS index from embeddings
    embeddings = model.encode(documents)
    embeddings = np.array(embeddings).astype("float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)

    print(f"Indexed {len(documents)} chunks.")
    print(f"Wrote: {INDEX_PATH}")
    print(f"Wrote: {META_PATH}")


if __name__ == "__main__":
    main()