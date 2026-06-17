from typing import Optional
from pydantic import BaseModel


# ── Topic Analytics ────────────────────────────────────────────────────────────

class TopicAnalyticsItem(BaseModel):
    """Per-topic raw performance stats."""
    topic: str
    solved: int
    attempted: int
    accuracy: float       # 0–100


class TopicAnalyticsResponse(BaseModel):
    topics: list[TopicAnalyticsItem]


# ── Topic Mastery ──────────────────────────────────────────────────────────────

class TopicMasteryItem(BaseModel):
    """Per-topic mastery score + derived fields the frontend needs."""
    topic: str
    score: int            # 0–100 mastery score
    strength: str         # Expert / Advanced / Intermediate / Beginner / Weak
    solved: int
    accuracy: float


class TopicMasteryResponse(BaseModel):
    masteries: list[TopicMasteryItem]


# ── Weakness ───────────────────────────────────────────────────────────────────

class WeaknessItem(BaseModel):
    topic: str
    score: int
    priority: str         # High / Medium / Low
    suggestion: str


class WeaknessResponse(BaseModel):
    weaknesses: list[WeaknessItem]


# ── Strength ───────────────────────────────────────────────────────────────────

class StrengthItem(BaseModel):
    topic: str
    score: int


class StrengthResponse(BaseModel):
    strengths: list[StrengthItem]


# ── Summary ────────────────────────────────────────────────────────────────────

class TopicSummaryResponse(BaseModel):
    strongest_topic: Optional[str] = None
    weakest_topic: Optional[str] = None
    average_mastery: int
    topics_above_75: int
    topics_below_60: int
