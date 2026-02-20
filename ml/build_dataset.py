import os
import pandas as pd
from api.app.db import SessionLocal
from api.app import models

def main():
    os.makedirs("data/ml", exist_ok=True)
    db = SessionLocal()

    # Pull all feedback, newest last
    feedback_rows = (
        db.query(models.FeedbackEvent)
        .order_by(models.FeedbackEvent.created_at.asc(), models.FeedbackEvent.id.asc())
        .all()
    )

    # Keep ONLY the latest feedback per usage_event_id (or per feedback_id if None)
    latest_by_usage = {}
    for fb in feedback_rows:
        key = fb.usage_event_id if fb.usage_event_id is not None else f"no_usage_{fb.id}"
        latest_by_usage[key] = fb

    rows = []
    for key, fb in latest_by_usage.items():
        usage = None
        if fb.usage_event_id is not None:
            usage = (
                db.query(models.UsageEvent)
                .filter(models.UsageEvent.id == fb.usage_event_id)
                .first()
            )

        rows.append({
            "feedback_id": fb.id,
            "usage_event_id": fb.usage_event_id,
            "is_helpful": int(fb.is_helpful),
            "comment_len": len(fb.comment or ""),
            "domain": (usage.domain if usage else "unknown"),
            "question_len": (len(usage.question) if usage and usage.question else 0),
            "top_distance": (usage.top_distance if usage and usage.top_distance is not None else 9999.0),
            "has_retrieval": int(1 if usage and usage.top_chunk_idx is not None else 0),
        })

    df = pd.DataFrame(rows).sort_values(["usage_event_id"], na_position="last")
    out_path = "data/ml/feedback_dataset.csv"
    df.to_csv(out_path, index=False)

    print(f"Wrote {out_path}")
    print(df)

if __name__ == "__main__":
    main()