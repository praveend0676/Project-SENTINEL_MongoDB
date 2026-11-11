from pydantic import BaseModel, Field
from typing import Any

class ExplainRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"transaction_id": "TXN0001386"},
                {"transaction_id": "TXN0003642"},
            ]
        }
    }
    transaction_id: str = Field(min_length=1, max_length=128, examples=["TXN0001386"])

class ReasonCode(BaseModel):
    code: str
    description: str

class PolicyCitation(BaseModel):
    document: str
    chunk_number: int
    relevance_score: float | None = None
    supporting_excerpt: str

class ExplainResponse(BaseModel):
    transaction_id: str
    risk_level: str
    risk_summary: str
    reason_codes: list[ReasonCode]
    recommended_action: str
    policy_citations: list[PolicyCitation]
    evidence: dict[str, Any]
    ground_truth_label: int | None = None  # included only in offline evaluation mode
