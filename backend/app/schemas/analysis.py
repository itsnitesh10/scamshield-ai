from pydantic import BaseModel, Field
from typing import Optional, List, Any


class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)


class URLAnalysisRequest(BaseModel):
    url: str = Field(..., min_length=3, max_length=2048)


class CombinedAnalysisRequest(BaseModel):
    text: Optional[str] = Field(None, max_length=8000)
    url: Optional[str] = Field(None, max_length=2048)


class AIExplanation(BaseModel):
    simple_explanation: str
    why_suspicious: List[str]
    attacker_goal: str
    recommended_action: List[str]
    generated_by: str


class AnalysisResponse(BaseModel):
    overall_risk_score: float
    risk_level: str
    scam_category: Optional[str]
    confidence: float
    evidence: List[str]
    signals: dict
    text_analysis: Optional[dict] = None
    url_analysis: Optional[dict] = None
    ocr: Optional[dict] = None
    ai_investigation: AIExplanation
