import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_PATH = "data/index/faiss.index"
META_PATH = "data/index/chunks.jsonl"

model = SentenceTransformer("all-MiniLM-L6-v2")

def load_chunks():
    chunks = {}
    with open(META_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            chunks[int(obj["idx"])] = obj["text"]
    return chunks

def main():
    question = input("Question: ").strip()
    if not question:
        print("No question provided.")
        return

    # Load chunk text mapping
    chunks = load_chunks()

    # Load FAISS index
    index = faiss.read_index(INDEX_PATH)

    if index.ntotal == 0:
        print("Index is empty. Run: PYTHONPATH=. python worker/ingest.py")
        return

    # Embed question
    q_emb = model.encode([question])
    q_emb = np.array(q_emb).astype("float32")

    # Search (don't ask for more than we have)
    k = min(5, index.ntotal)
    D, I = index.search(q_emb, k=k)

    print(f"\nTop matches (showing {k}):")
    for rank, (idx, dist) in enumerate(zip(I[0], D[0]), start=1):
        if int(idx) < 0:
            continue
        text = chunks.get(int(idx), "<missing chunk text>")
        print(f"\n{rank}. distance={float(dist):.4f}  idx={int(idx)}")
        print(text)

if __name__ == "__main__":
    main()