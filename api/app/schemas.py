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
    domain: str = "general"
