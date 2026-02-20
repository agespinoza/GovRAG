import os
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression

MODEL_PATH = "data/ml/trust_model.joblib"

def main():
    df = pd.read_csv("data/ml/feedback_dataset.csv")

    # Basic features (numeric only for MVP)
    X = df[["question_len", "top_distance", "has_retrieval", "comment_len"]].copy()
    y = df["is_helpful"].astype(int)

    model = LogisticRegression(max_iter=1000)
    model.fit(X, y)

    os.makedirs("data/ml", exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")

    probs = model.predict_proba(X)[:, 1]
    out = df.copy()
    out["trust_score"] = probs
    print(out[["usage_event_id", "is_helpful", "top_distance", "has_retrieval", "trust_score"]].head(20))

if __name__ == "__main__":
    main()