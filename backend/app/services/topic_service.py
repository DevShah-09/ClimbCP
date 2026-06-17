"""
Topic Intelligence Service — Phase 2

All functions operate exclusively on locally stored data.
No Codeforces API calls are made.

Query strategy (avoids N+1):
  - 3 aggregate SQL queries total for mastery calculation
  - Results merged in Python for scoring
"""

import logging
import math
from typing import Optional
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.platform_account import PlatformAccount
from app.models.problem_attempt import ProblemAttempt
from app.models.problem import Problem
from app.models.problem_topic import ProblemTopic
from app.models.topic import Topic
from app.schemas.topic import (
    TopicAnalyticsItem,
    TopicAnalyticsResponse,
    TopicMasteryItem,
    TopicMasteryResponse,
    WeaknessItem,
    WeaknessResponse,
    StrengthItem,
    StrengthResponse,
    TopicSummaryResponse,
)

logger = logging.getLogger("topic_service")

# ── Mastery level thresholds ───────────────────────────────────────────────────
LEVELS = [
    (90, "Expert"),
    (75, "Advanced"),
    (60, "Intermediate"),
    (40, "Beginner"),
    (0,  "Weak"),
]

# Difficulty normalization range (Codeforces rating scale)
DIFF_MIN = 800
DIFF_MAX = 3500

# Weakness suggestion map keyed by topic name (lower-cased)
SUGGESTIONS: dict[str, str] = {
    "dynamic programming":      "Practice bottom-up DP patterns. Start with classical problems: knapsack, LIS, LCS.",
    "graphs":                   "Focus on BFS/DFS traversal, Dijkstra, and Bellman-Ford shortest paths.",
    "trees":                    "Strengthen tree DP, LCA, and Euler tour techniques.",
    "binary search":            "Practice binary search on answer problems. Focus on predicate design.",
    "math":                     "Review modular arithmetic, prime sieve, number theory, and combinatorics.",
    "greedy algorithms":        "Study exchange argument proofs. Practice sorting-based greedy problems.",
    "data structures":          "Implement segment trees, BITs, and sparse tables from scratch.",
    "two pointers":             "Focus on sliding window and meet-in-the-middle patterns.",
    "string algorithms":        "Work on KMP, Z-function, suffix arrays, and string hashing.",
    "graphs":                   "Study SCC, bridges, and articulation points alongside BFS/DFS.",
    "flows & matchings":        "Understand max-flow (Dinic's) and bipartite matching.",
    "geometry":                 "Practice convex hull, line intersection, and point-in-polygon.",
    "number theory":            "Master GCD/LCM, Euler's totient, modular inverse, and CRT.",
    "combinatorics":            "Study inclusion-exclusion, Burnside's lemma, and generating functions.",
    "constructive algorithms":  "Practice building solutions incrementally; think about invariants.",
    "shortest paths":           "Implement Dijkstra and Bellman-Ford. Study SPFA and Floyd-Warshall.",
    "sorting":                  "Review merge sort, counting sort, and custom comparators.",
    "bitmasking":               "Practice bitmask DP and set enumeration techniques.",
    "implementation":           "Focus on clean code and simulation problems with complex specifications.",
}
DEFAULT_SUGGESTION = "Focus on foundational problems in this topic to build core intuition."


def _get_mastery_level(score: int) -> str:
    for threshold, label in LEVELS:
        if score >= threshold:
            return label
    return "Weak"


def _resolve_user_id(db: Session, handle: str):
    """Return user_id for the given CF handle, or raise ValueError."""
    account = (
        db.query(PlatformAccount)
        .filter(func.lower(PlatformAccount.handle) == handle.lower())
        .first()
    )
    if not account:
        raise ValueError(f"No profile found for handle '{handle}'")
    return account.user_id


# ── Feature 1: Topic Analytics ─────────────────────────────────────────────────

def get_topic_analytics(db: Session, handle: str) -> TopicAnalyticsResponse:
    logger.info(f"Topic analytics started for handle: {handle}")

    user_id = _resolve_user_id(db, handle)
    logger.info(f"User found: {user_id}")

    rows = (
        db.query(
            Topic.name.label("topic_name"),
            func.count(ProblemAttempt.id).label("attempted"),
            func.sum(
                case((ProblemAttempt.solved == True, 1), else_=0)
            ).label("solved"),
        )
        .join(ProblemTopic, Topic.id == ProblemTopic.topic_id)
        .join(Problem, Problem.id == ProblemTopic.problem_id)
        .join(ProblemAttempt, ProblemAttempt.problem_id == Problem.id)
        .filter(ProblemAttempt.user_id == user_id)
        .group_by(Topic.name)
        .order_by(Topic.name)
        .all()
    )

    if not rows:
        raise ValueError(f"No submission data available for handle '{handle}'")

    items = []
    for row in rows:
        attempted = int(row.attempted or 0)
        solved = int(row.solved or 0)
        accuracy = round((solved / attempted) * 100, 1) if attempted > 0 else 0.0
        items.append(TopicAnalyticsItem(
            topic=row.topic_name,
            solved=solved,
            attempted=attempted,
            accuracy=accuracy,
        ))

    logger.info(f"Topic calculations completed: {len(items)} topics found")
    return TopicAnalyticsResponse(topics=items)


# ── Feature 2: Topic Mastery Scoring ──────────────────────────────────────────

def _fetch_difficulty_scores(db: Session, user_id) -> dict[str, float]:
    """AVG difficulty of solved problems per topic (one query)."""
    rows = (
        db.query(
            Topic.name.label("topic_name"),
            func.avg(Problem.difficulty).label("avg_diff"),
        )
        .join(ProblemTopic, Topic.id == ProblemTopic.topic_id)
        .join(Problem, Problem.id == ProblemTopic.problem_id)
        .join(ProblemAttempt, ProblemAttempt.problem_id == Problem.id)
        .filter(
            ProblemAttempt.user_id == user_id,
            ProblemAttempt.solved == True,
            Problem.difficulty.isnot(None),
        )
        .group_by(Topic.name)
        .all()
    )
    return {row.topic_name: float(row.avg_diff) for row in rows if row.avg_diff}


def _fetch_contest_scores(db: Session, user_id) -> dict[str, tuple[int, int]]:
    """(contest_attempted, contest_solved) per topic (one query)."""
    rows = (
        db.query(
            Topic.name.label("topic_name"),
            func.count(ProblemAttempt.id).label("contest_attempted"),
            func.sum(
                case((ProblemAttempt.solved == True, 1), else_=0)
            ).label("contest_solved"),
        )
        .join(ProblemTopic, Topic.id == ProblemTopic.topic_id)
        .join(Problem, Problem.id == ProblemTopic.problem_id)
        .join(ProblemAttempt, ProblemAttempt.problem_id == Problem.id)
        .filter(
            ProblemAttempt.user_id == user_id,
            ProblemAttempt.participation_id.isnot(None),
        )
        .group_by(Topic.name)
        .all()
    )
    return {
        row.topic_name: (int(row.contest_attempted or 0), int(row.contest_solved or 0))
        for row in rows
    }


def _compute_mastery_score(
    accuracy: float,
    solved: int,
    avg_difficulty: Optional[float],
    contest_attempted: int,
    contest_solved: int,
) -> int:
    """
    mastery = 40% accuracy + 30% difficulty_score + 20% volume_score + 10% contest_score
    All sub-scores are 0–100 before weighting.
    """
    # Component 1: accuracy (already 0-100)
    acc_score = min(max(accuracy, 0.0), 100.0)

    # Component 2: difficulty (normalized 800→3500 scale)
    if avg_difficulty:
        diff_score = (avg_difficulty - DIFF_MIN) / (DIFF_MAX - DIFF_MIN) * 100
        diff_score = min(max(diff_score, 0.0), 100.0)
    else:
        diff_score = 50.0   # no rated problems → neutral

    # Component 3: volume (log-inspired; 50 solved → full score)
    volume_score = min(solved / 50.0, 1.0) * 100.0

    # Component 4: contest success
    if contest_attempted > 0:
        contest_score = (contest_solved / contest_attempted) * 100
    else:
        contest_score = 50.0   # no contest data → neutral

    raw = (
        0.40 * acc_score
        + 0.30 * diff_score
        + 0.20 * volume_score
        + 0.10 * contest_score
    )
    return int(round(min(max(raw, 0), 100)))


def calculate_topic_mastery(db: Session, handle: str) -> TopicMasteryResponse:
    logger.info(f"Mastery scoring started for handle: {handle}")

    user_id = _resolve_user_id(db, handle)

    # 3 aggregate queries total
    analytics = get_topic_analytics(db, handle)
    diff_map = _fetch_difficulty_scores(db, user_id)
    contest_map = _fetch_contest_scores(db, user_id)

    items: list[TopicMasteryItem] = []
    for t in analytics.topics:
        avg_diff = diff_map.get(t.topic)
        c_attempted, c_solved = contest_map.get(t.topic, (0, 0))

        score = _compute_mastery_score(
            accuracy=t.accuracy,
            solved=t.solved,
            avg_difficulty=avg_diff,
            contest_attempted=c_attempted,
            contest_solved=c_solved,
        )
        items.append(TopicMasteryItem(
            topic=t.topic,
            score=score,
            strength=_get_mastery_level(score),
            solved=t.solved,
            accuracy=t.accuracy,
        ))

    # Sort descending by score for a natural display order
    items.sort(key=lambda x: x.score, reverse=True)
    logger.info(f"Mastery scores generated for {len(items)} topics")
    return TopicMasteryResponse(masteries=items)


# ── Feature 3: Weakness Detection ─────────────────────────────────────────────

def _priority_from_score(score: int) -> str:
    if score < 60:
        return "High"
    if score < 75:
        return "Medium"
    return "Low"


def get_weaknesses(db: Session, handle: str) -> WeaknessResponse:
    logger.info(f"Weakness detection started for handle: {handle}")

    mastery = calculate_topic_mastery(db, handle)

    items: list[WeaknessItem] = []
    for m in mastery.masteries:
        priority = _priority_from_score(m.score)
        suggestion = SUGGESTIONS.get(m.topic.lower(), DEFAULT_SUGGESTION)
        items.append(WeaknessItem(
            topic=m.topic,
            score=m.score,
            priority=priority,
            suggestion=suggestion,
        ))

    # Sort ascending (weakest first)
    items.sort(key=lambda x: x.score)
    logger.info(f"Weaknesses generated: {len(items)} topics returned")
    return WeaknessResponse(weaknesses=items)


# ── Feature 4: Strength Detection ─────────────────────────────────────────────

def get_strengths(db: Session, handle: str) -> StrengthResponse:
    logger.info(f"Strength detection started for handle: {handle}")

    mastery = calculate_topic_mastery(db, handle)

    items = [
        StrengthItem(topic=m.topic, score=m.score)
        for m in mastery.masteries
        if m.score >= 75
    ]
    # Already sorted descending from calculate_topic_mastery
    logger.info(f"Strengths generated: {len(items)} strong topics found")
    return StrengthResponse(strengths=items)


# ── Feature 5: Topic Summary ───────────────────────────────────────────────────

def get_topic_summary(db: Session, handle: str) -> TopicSummaryResponse:
    mastery = calculate_topic_mastery(db, handle)
    scores = mastery.masteries

    if not scores:
        return TopicSummaryResponse(
            strongest_topic=None,
            weakest_topic=None,
            average_mastery=0,
            topics_above_75=0,
            topics_below_60=0,
        )

    avg = int(round(sum(m.score for m in scores) / len(scores)))
    strongest = max(scores, key=lambda m: m.score)
    weakest = min(scores, key=lambda m: m.score)

    return TopicSummaryResponse(
        strongest_topic=strongest.topic,
        weakest_topic=weakest.topic,
        average_mastery=avg,
        topics_above_75=sum(1 for m in scores if m.score >= 75),
        topics_below_60=sum(1 for m in scores if m.score < 60),
    )
