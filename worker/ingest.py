import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from api.app.db import SessionLocal
from api.app import models

INDEX_PATH = "data/index/faiss.index"

model = SentenceTransformer("all-MiniLM-L6-v2")

def get_approved_versions(db):
    return db.query(models.KnowledgeVersion)\
        .filter(models.KnowledgeVersion.status == "approved")\
        .all()

def chunk_text(text, size=200):
    words = text.split()
    for i in range(0, len(words), size):
        yield " ".join(words[i:i+size])

def main():
    db = SessionLocal()

    versions = get_approved_versions(db)

    documents = []
    for v in versions:
        chunks = list(chunk_text(v.content))
        documents.extend(chunks)

    if not documents:
        print("No approved content found.")
        return

    embeddings = model.encode(documents)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))

    os.makedirs("data/index", exist_ok=True)
    faiss.write_index(index, INDEX_PATH)

    print(f"Indexed {len(documents)} chunks.")

if __name__ == "__main__":
    main()