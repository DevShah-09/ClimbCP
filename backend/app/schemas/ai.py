"""
AI Coaching Schemas — Phase 4

Request and response models for:
  - POST /ai/contest-review
  - GET  /ai/rating-loss/{handle}
  - GET  /ai/bottlenecks/{handle}
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Requests ───────────────────────────────────────────────────────────────────

class ContestReviewRequest(BaseModel):
    handle: str = Field(..., description="Codeforces handle")
    contest_id: int = Field(..., description="Codeforces contest ID (e.g. 1920)")


# ── Contest Review Response ────────────────────────────────────────────────────

class ContestReviewResponse(BaseModel):
    handle: str
    contest_id: int
    contest_name: str
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    missed_opportunities: list[str]
    action_plan: list[str]
    cached: bool = False
    generated_at: datetime


# ── Rating Loss Explanation Response ──────────────────────────────────────────

class RatingLossResponse(BaseModel):
    handle: str
    current_rating: Optional[int] = None
    rating_change: Optional[int] = None           # net change across recent contests
    explanation: str
    major_causes: list[str]
    recommended_actions: list[str]
    cached: bool = False
    generated_at: datetime


# ── Bottleneck Analysis Response ───────────────────────────────────────────────

class BottleneckItem(BaseModel):
    factor: str
    impact: int = Field(..., ge=0, le=100, description="Impact score 0-100; higher = bigger bottleneck")
    description: str = ""


class BottleneckAnalysis(BaseModel):
    handle: str
    bottlenecks: list[BottleneckItem]
    narrative: str                                 # LLM-generated explanatory paragraph
    cached: bool = False
    generated_at: datetime
