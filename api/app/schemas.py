from pydantic import BaseModel

class CreateItem(BaseModel):
    title: str
    domain: str = "general"

class CreateVersion(BaseModel):
    knowledge_item_id: int
    content: str

class ApproveVersion(BaseModel):
    version_id: int

class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    domain: str | None = None

class FeedbackRequest(BaseModel):
    usage_event_id: int | None = None
    is_helpful: bool
    comment: str | None = None