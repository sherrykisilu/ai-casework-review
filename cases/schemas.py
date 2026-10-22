from typing import Literal

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    quote: str = Field(min_length=1, max_length=500)
    rationale: str = Field(min_length=1, max_length=500)


class Finding(BaseModel):
    category: Literal["customer_risk", "compliance", "support_quality", "urgency"]
    severity: Literal["low", "medium", "high"]
    summary: str = Field(min_length=1, max_length=300)
    evidence: list[Evidence] = Field(min_length=1, max_length=5)


class AnalysisResult(BaseModel):
    summary: str = Field(min_length=1, max_length=600)
    findings: list[Finding] = Field(max_length=12)
    recommended_actions: list[str] = Field(max_length=8)
    limitations: list[str] = Field(max_length=8)
    confidence: float = Field(ge=0, le=1)
