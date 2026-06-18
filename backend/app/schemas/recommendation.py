"""
Recommendation Schemas — Phase 3

Covers:
  - GET /recommendations/{handle}  → ProblemRecommendationResponse
  - GET /practice-set/{handle}     → PracticeSetResponse
  - GET /roadmap/{handle}          → RoadmapResponse
"""

from typing import Optional
from pydantic import BaseModel


# ── Feature 1: Problem Recommendations ────────────────────────────────────────

class RecommendedProblem(BaseModel):
    """A single recommended problem with full explainability context."""
    problem_id: str           # UUID string of the Problem row
    problem_code: str         # e.g. "1845A"
    name: str
    rating: Optional[int]     # difficulty / CF rating
    topics: list[str]
    difficulty_tier: str      # "Easy Stretch" | "Current Level" | "Challenge"
    priority_score: float     # higher = better match
    reason: str               # human-readable explanation


class ProblemRecommendationResponse(BaseModel):
    handle: str
    user_rating: Optional[int]
    recommendations: list[RecommendedProblem]


# ── Feature 2: Practice Set ───────────────────────────────────────────────────

class PracticeSetProblem(BaseModel):
    """Extended problem entry inside the practice set."""
    problem_id: str
    problem_code: str
    name: str
    rating: Optional[int]
    topics: list[str]
    difficulty_tier: str
    category: str             # "Weak Topic" | "Medium Topic" | "Strong Topic"
    reason: str


class PracticeSetMetadata(BaseModel):
    estimated_time: str       # e.g. "5 hours"
    focus_topics: list[str]
    weak_topic_count: int
    medium_topic_count: int
    strong_topic_count: int
    easy_count: int
    medium_count: int
    challenge_count: int


class PracticeSetResponse(BaseModel):
    handle: str
    user_rating: Optional[int]
    practice_set: list[PracticeSetProblem]
    metadata: PracticeSetMetadata


# ── Feature 3: Learning Roadmap ───────────────────────────────────────────────

class RoadmapTask(BaseModel):
    description: str          # e.g. "Solve 10 Graph Problems"


class RoadmapWeek(BaseModel):
    week: int
    theme: str                # e.g. "Foundation", "Deep Dive", "Combined Practice"
    focus: list[str]          # topic names to focus on
    tasks: list[RoadmapTask]
    target_problems: int


class RoadmapResponse(BaseModel):
    handle: str
    user_rating: Optional[int]
    weeks: list[RoadmapWeek]
    total_weeks: int
    focus_summary: str        # one-sentence overview of the plan


# ── Feature 5: V2 Problem Recommendations (Embedding-Based) ─────────────────

class RecommendedProblemV2(BaseModel):
    problem_id: str
    problem_code: str
    name: str
    rating: Optional[int]
    reason: str

class ProblemRecommendationResponseV2(BaseModel):
    handle: str
    recommendations: list[RecommendedProblemV2]

