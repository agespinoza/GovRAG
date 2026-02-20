import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_PATH = "data/index/faiss.index"
META_PATH = "data/index/chunks.jsonl"

_model = SentenceTransformer("all-MiniLM-L6-v2")


def _load_chunks():
    """
    Returns a dict: idx -> chunk object
    chunk object includes: text, domain, knowledge_item_id, version_id
    """
    chunks = {}
    with open(META_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            chunks[int(obj["idx"])] = obj
    return chunks


def retrieve(question: str, top_k: int = 5, domain: str | None = None):
    index = faiss.read_index(INDEX_PATH)
    if index.ntotal == 0:
        return []

    chunks = _load_chunks()

    q_emb = _model.encode([question])
    q_emb = np.array(q_emb).astype("float32")

    k = min(top_k, index.ntotal)
    D, I = index.search(q_emb, k=k)

    results = []
    for idx, dist in zip(I[0], D[0]):
        idx = int(idx)
        if idx < 0:
            continue

        chunk_obj = chunks.get(idx)
        if not chunk_obj:
            continue

        if domain and chunk_obj.get("domain") != domain:
            continue

        results.append({
            "idx": idx,
            "distance": float(dist),
            "text": chunk_obj.get("text", ""),
            "domain": chunk_obj.get("domain"),
            "knowledge_item_id": chunk_obj.get("knowledge_item_id"),
            "version_id": chunk_obj.get("version_id"),
        })

    return results