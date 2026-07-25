from typing import Literal

from pydantic import BaseModel, Field


class SyncRequest(BaseModel): idempotency_key: str = Field(min_length=1, max_length=100)
class AnalyzeRequest(BaseModel): query: str = Field(min_length=3, max_length=500)
class ReviewRequest(BaseModel):
    draft_id: str
    decision: Literal["approved", "rejected"]
    reason: str = Field(min_length=1, max_length=500)
