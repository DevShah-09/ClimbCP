"""
AI Coach Service — Phase 4

Orchestrates the full pipeline for each AI coaching feature:
  1. Gather data from existing analytics services
  2. Check report cache (ai_reports table)
  3. Build prompt with prompt_builder
  4. Call LLM via llm_service
  5. Store result in ai_reports
  6. Return structured response

Public functions:
  generate_contest_review(db, handle, contest_id) → ContestReviewResponse
  explain_rating_loss(db, handle)                 → RatingLossResponse
  analyze_bottlenecks(db, handle)                 → BottleneckAnalysis
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ai_report import AIReport
from app.models.contest import Contest
from app.models.contest_participation import ContestParticipation
from app.models.platform_account import PlatformAccount
from app.models.problem_attempt import ProblemAttempt
from app.models.problem import Problem
from app.models.problem_topic import ProblemTopic
from app.models.topic import Topic
from app.schemas.ai import (
    ContestReviewResponse,
    RatingLossResponse,
    BottleneckAnalysis,
    BottleneckItem,
)
from app.services import llm_service, prompt_builder
from app.services.analytics_service import (
    get_user_analytics,
    get_rating_history,
    get_contest_statistics,
    get_activity_statistics,
)
from app.services.topic_service import (
    calculate_topic_mastery,
    get_weaknesses,
    get_strengths,
)

logger = logging.getLogger("ai_coach_service")

# ── Cache configuration ────────────────────────────────────────────────────────

def _cache_hours() -> int:
    try:
        return int(os.getenv("AI_REPORT_CACHE_HOURS", "6"))
    except ValueError:
        return 6


# ── Internal Helpers ───────────────────────────────────────────────────────────

def _resolve_account(db: Session, handle: str) -> PlatformAccount:
    """Return PlatformAccount or raise ValueError."""
    account = (
        db.query(PlatformAccount)
        .filter(func.lower(PlatformAccount.handle) == handle.lower())
        .first()
    )
    if not account:
        raise ValueError(f"No profile found for handle '{handle}'")
    return account


def _make_cache_key(report_type: str, user_id, extra: str = "none") -> str:
    """Build a unique cache key string."""
    return f"{report_type}:{user_id}:{extra}"


def _get_cached_report(db: Session, cache_key: str) -> Optional[AIReport]:
    """
    Return a recent AIReport matching cache_key if it was generated
    within the configured cache window, otherwise None.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=_cache_hours())
    report = (
        db.query(AIReport)
        .filter(
            AIReport.cache_key == cache_key,
            AIReport.created_at >= cutoff,
        )
        .order_by(AIReport.created_at.desc())
        .first()
    )
    return report


def _store_report(
    db: Session,
    user_id,
    contest_id_uuid: Optional[uuid.UUID],
    report_type: str,
    cache_key: str,
    summary: str,
    strengths_text: str,
    weaknesses_text: str,
    recommendations_text: str,
    generated_text: str,
) -> AIReport:
    """Persist an AI report to the database."""
    report = AIReport(
        user_id=user_id,
        contest_id=contest_id_uuid,
        report_type=report_type,
        cache_key=cache_key,
        summary=summary,
        strengths=strengths_text,
        weaknesses=weaknesses_text,
        recommendations=recommendations_text,
        generated_text=generated_text,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    logger.info(f"Report stored: id={report.id}, type={report_type}, key={cache_key}")
    return report


def _get_topic_mastery_map(db: Session, handle: str) -> dict[str, int]:
    """Return {topic_name: mastery_score} dict."""
    try:
        mastery_resp = calculate_topic_mastery(db, handle)
        return {m.topic: m.score for m in mastery_resp.masteries}
    except ValueError:
        return {}


def _get_weak_topics(db: Session, handle: str) -> list[str]:
    """Return topic names with mastery score < 60."""
    try:
        weakness_resp = get_weaknesses(db, handle)
        return [w.topic for w in weakness_resp.weaknesses if w.score < 60]
    except ValueError:
        return []


def _get_strong_topics(db: Session, handle: str) -> list[str]:
    """Return topic names with mastery score >= 75."""
    try:
        strength_resp = get_strengths(db, handle)
        return [s.topic for s in strength_resp.strengths]
    except ValueError:
        return []


# ── Feature 1: Contest Review ──────────────────────────────────────────────────

def generate_contest_review(
    db: Session,
    handle: str,
    contest_id: int,
) -> ContestReviewResponse:
    """
    Generate a detailed post-contest coaching report.

    Pipeline:
      1. Resolve user + find ContestParticipation by contest_code
      2. Load problem attempts for that participation
      3. Load topic mastery + weak/strong topics
      4. Cache check
      5. Build prompt → call LLM → parse JSON
      6. Store in ai_reports
      7. Return ContestReviewResponse
    """
    logger.info(f"AI contest review started: handle={handle}, contest_id={contest_id}")

    account = _resolve_account(db, handle)
    user_id = account.user_id

    # Find the contest by Codeforces contest_code
    contest_code = str(contest_id)
    contest = (
        db.query(Contest)
        .filter(Contest.contest_code == contest_code)
        .first()
    )
    if not contest:
        raise ValueError(
            f"Contest with ID {contest_id} not found in the database. "
            "Please sync your Codeforces data first."
        )

    # Find participation
    participation = (
        db.query(ContestParticipation)
        .filter(
            ContestParticipation.user_id == user_id,
            ContestParticipation.contest_id == contest.id,
        )
        .first()
    )
    if not participation:
        raise ValueError(
            f"No participation record for handle '{handle}' in contest {contest_id}. "
            "Please sync your Codeforces data first."
        )

    logger.info("Contest participation found — loading problem attempts")

    # Load problem attempts for this participation
    attempts = (
        db.query(ProblemAttempt)
        .filter(ProblemAttempt.participation_id == participation.id)
        .all()
    )

    # Build attempt detail list with topics
    contest_attempts = []
    for att in attempts:
        prob = db.query(Problem).filter(Problem.id == att.problem_id).first()
        if not prob:
            continue
        topic_rows = (
            db.query(Topic.name)
            .join(ProblemTopic, ProblemTopic.topic_id == Topic.id)
            .filter(ProblemTopic.problem_id == prob.id)
            .all()
        )
        topics = [r.name for r in topic_rows]
        contest_attempts.append({
            "problem_code": prob.problem_code,
            "problem_title": prob.title,
            "difficulty": prob.difficulty,
            "topics": topics,
            "solved": att.solved,
            "attempts": att.attempts,
            "verdict": att.verdict,
            "time_to_solve_seconds": att.time_to_solve,
        })

    logger.info(f"Data aggregation completed: {len(contest_attempts)} attempts loaded")

    # Topic intelligence
    mastery_map = _get_topic_mastery_map(db, handle)
    weak_topics = _get_weak_topics(db, handle)
    strong_topics = _get_strong_topics(db, handle)

    # Cache check
    cache_key = _make_cache_key("contest_review", user_id, contest_code)
    cached = _get_cached_report(db, cache_key)
    if cached and cached.generated_text:
        logger.info(f"Cache hit for contest review: {cache_key}")
        data = json.loads(cached.generated_text)
        return ContestReviewResponse(
            handle=handle,
            contest_id=contest_id,
            contest_name=contest.contest_name,
            summary=data.get("summary", ""),
            strengths=data.get("strengths", []),
            weaknesses=data.get("weaknesses", []),
            missed_opportunities=data.get("missed_opportunities", []),
            action_plan=data.get("action_plan", []),
            cached=True,
            generated_at=cached.created_at,
        )

    # Build context for prompt
    context = {
        "handle": handle,
        "contest_name": contest.contest_name,
        "contest_code": contest_code,
        "rank": participation.rank,
        "rating_before": participation.rating_before,
        "rating_after": participation.rating_after,
        "rating_change": participation.rating_change,
        "problems_solved": participation.problems_solved,
        "problems_attempted": len(contest_attempts),
        "topic_masteries": mastery_map,
        "weak_topics": weak_topics,
        "strong_topics": strong_topics,
        "contest_attempts": contest_attempts,
    }

    logger.info("Prompt generated — calling LLM")
    system_prompt, user_prompt = prompt_builder.build_contest_review_prompt(context)

    llm_result = llm_service.generate_contest_review(system_prompt, user_prompt)
    logger.info("LLM response received")

    # Store report
    generated_text = json.dumps(llm_result)
    _store_report(
        db=db,
        user_id=user_id,
        contest_id_uuid=contest.id,
        report_type="contest_review",
        cache_key=cache_key,
        summary=llm_result.get("summary", ""),
        strengths_text=json.dumps(llm_result.get("strengths", [])),
        weaknesses_text=json.dumps(llm_result.get("weaknesses", [])),
        recommendations_text=json.dumps(llm_result.get("action_plan", [])),
        generated_text=generated_text,
    )

    return ContestReviewResponse(
        handle=handle,
        contest_id=contest_id,
        contest_name=contest.contest_name,
        summary=llm_result["summary"],
        strengths=llm_result["strengths"],
        weaknesses=llm_result["weaknesses"],
        missed_opportunities=llm_result["missed_opportunities"],
        action_plan=llm_result["action_plan"],
        cached=False,
        generated_at=datetime.now(timezone.utc),
    )


# ── Feature 2: Rating Loss Explanation ────────────────────────────────────────

def explain_rating_loss(db: Session, handle: str) -> RatingLossResponse:
    """
    Explain rating stagnation or rating drops for a user.

    Pipeline:
      1. Resolve user
      2. Gather rating history, contest stats, topic mastery, activity stats
      3. Compute net rating change over last 10 contests
      4. Cache check
      5. Build prompt → call LLM → parse JSON
      6. Store in ai_reports
      7. Return RatingLossResponse
    """
    logger.info(f"AI rating loss explanation started: handle={handle}")

    account = _resolve_account(db, handle)
    user_id = account.user_id

    # Gather analytics
    analytics = get_user_analytics(db, handle)
    rating_history = get_rating_history(db, handle)
    contest_stats = get_contest_statistics(db, handle)
    activity_stats = get_activity_statistics(db, handle)
    mastery_map = _get_topic_mastery_map(db, handle)
    weak_topics = _get_weak_topics(db, handle)
    strong_topics = _get_strong_topics(db, handle)

    logger.info("Data aggregation completed for rating loss analysis")

    # Compute net rating change over last 10 contests
    recent = rating_history[-10:] if len(rating_history) >= 10 else rating_history
    net_rating_change = 0
    recent_contest_data = []
    for item in recent:
        change = item.rating_change or 0
        net_rating_change += change
        recent_contest_data.append({
            "contest_name": item.contest_name,
            "date": str(item.contest_date),
            "rank": item.rank,
            "rating_change": change,
            "old_rating": item.old_rating,
            "new_rating": item.new_rating,
        })

    # Cache check
    cache_key = _make_cache_key("rating_loss", user_id)
    cached = _get_cached_report(db, cache_key)
    if cached and cached.generated_text:
        logger.info(f"Cache hit for rating loss: {cache_key}")
        data = json.loads(cached.generated_text)
        return RatingLossResponse(
            handle=handle,
            current_rating=analytics.current_rating,
            rating_change=net_rating_change,
            explanation=data.get("explanation", ""),
            major_causes=data.get("major_causes", []),
            recommended_actions=data.get("recommended_actions", []),
            cached=True,
            generated_at=cached.created_at,
        )

    context = {
        "handle": handle,
        "current_rating": analytics.current_rating,
        "max_rating": analytics.max_rating,
        "net_rating_change": net_rating_change,
        "recent_contests": recent_contest_data,
        "total_contests": analytics.contest_count,
        "rating_increases": contest_stats.rating_increases,
        "rating_decreases": contest_stats.rating_decreases,
        "total_rating_gained": contest_stats.total_rating_gained,
        "total_rating_lost": contest_stats.total_rating_lost,
        "average_rank": contest_stats.average_rank,
        "best_rank": contest_stats.best_rank,
        "problems_solved": analytics.problems_solved,
        "total_submissions": analytics.total_submissions,
        "acceptance_rate": analytics.acceptance_rate,
        "avg_submissions_per_day": activity_stats.average_submissions_per_day,
        "avg_solved_per_week": activity_stats.average_solved_per_week,
        "topic_masteries": mastery_map,
        "weak_topics": weak_topics,
        "strong_topics": strong_topics,
    }

    logger.info("Prompt generated — calling LLM for rating loss")
    system_prompt, user_prompt = prompt_builder.build_rating_loss_prompt(context)
    llm_result = llm_service.explain_rating_loss(system_prompt, user_prompt)
    logger.info("LLM response received for rating loss")

    generated_text = json.dumps(llm_result)
    _store_report(
        db=db,
        user_id=user_id,
        contest_id_uuid=None,
        report_type="rating_loss",
        cache_key=cache_key,
        summary=llm_result.get("explanation", "")[:500],
        strengths_text="[]",
        weaknesses_text=json.dumps(llm_result.get("major_causes", [])),
        recommendations_text=json.dumps(llm_result.get("recommended_actions", [])),
        generated_text=generated_text,
    )

    return RatingLossResponse(
        handle=handle,
        current_rating=analytics.current_rating,
        rating_change=net_rating_change,
        explanation=llm_result["explanation"],
        major_causes=llm_result["major_causes"],
        recommended_actions=llm_result["recommended_actions"],
        cached=False,
        generated_at=datetime.now(timezone.utc),
    )


# ── Feature 3: Bottleneck Analysis ────────────────────────────────────────────

# Bottleneck factors and how to pre-score them from raw data
_BOTTLENECK_FACTORS = [
    "Dynamic Programming",
    "Graph Algorithms",
    "Binary Search",
    "Math",
    "Trees",
    "Constructive Algorithms",
    "Implementation Errors",
    "Low Contest Frequency",
    "Slow Solving Speed",
    "Poor Upsolving Habits",
]

# Topic name mapping from Bottleneck Factor → topic_service topic name
_FACTOR_TO_TOPIC: dict[str, str] = {
    "Dynamic Programming":   "dynamic programming",
    "Graph Algorithms":      "graphs",
    "Binary Search":         "binary search",
    "Math":                  "math",
    "Trees":                 "trees",
    "Constructive Algorithms": "constructive algorithms",
}


def _compute_pre_scores(
    mastery_map: dict[str, int],
    analytics,
    contest_stats,
    activity_stats,
    rating_history: list,
) -> list[dict]:
    """
    Algorithmically pre-score each bottleneck factor from raw DB data.
    Returns list of {factor, impact, raw_data} dicts.
    """
    scores = []

    # ── Topic-based bottlenecks ───────────────────────────────────────────────
    for factor, topic_key in _FACTOR_TO_TOPIC.items():
        # Check both exact and partial topic name match
        topic_score = None
        for topic_name, score in mastery_map.items():
            if topic_key in topic_name.lower() or topic_name.lower() in topic_key:
                topic_score = score
                break

        if topic_score is not None:
            # Weak topic (low mastery) → high impact
            # score 0 → impact 100, score 100 → impact 0
            impact = max(0, 100 - topic_score)
            raw = {
                "mastery_score": topic_score,
                "formula": "100 - mastery_score",
            }
        else:
            # Topic not in user's data — moderate impact (unknown territory)
            impact = 45
            raw = {"mastery_score": None, "note": "No submission data for this topic"}

        scores.append({"factor": factor, "impact": impact, "raw_data": raw})

    # ── Implementation Errors ─────────────────────────────────────────────────
    acceptance_rate = analytics.acceptance_rate or 0.0
    # Low acceptance rate → high implementation error impact
    # 90%+ AR → 0 impact; 50% AR → 50 impact; 10% AR → 90 impact
    impl_impact = max(0, min(100, int((100 - acceptance_rate))))
    scores.append({
        "factor": "Implementation Errors",
        "impact": impl_impact,
        "raw_data": {
            "acceptance_rate": acceptance_rate,
            "failed_submissions": analytics.failed_submissions,
            "formula": "100 - acceptance_rate",
        },
    })

    # ── Low Contest Frequency ─────────────────────────────────────────────────
    # Target: 2 contests/week. Less → higher impact.
    # avg_solved_per_week as proxy (we don't have direct contest_per_week)
    contest_count = analytics.contest_count or 0
    active_days = activity_stats.active_days or 1
    contests_per_week = (contest_count / (active_days / 7)) if active_days > 0 else 0
    # 2+ per week → 0 impact; 0 per week → 100 impact
    freq_impact = max(0, min(100, int(100 - (contests_per_week / 2) * 100)))
    scores.append({
        "factor": "Low Contest Frequency",
        "impact": freq_impact,
        "raw_data": {
            "total_contests": contest_count,
            "active_days": active_days,
            "estimated_contests_per_week": round(contests_per_week, 2),
            "target_per_week": 2,
        },
    })

    # ── Slow Solving Speed ────────────────────────────────────────────────────
    # Proxy: average submissions per day (more is better, up to a point)
    # Low daily activity can indicate slow solving or infrequent practice
    avg_subs = activity_stats.average_submissions_per_day or 0
    # 5+ subs/day → 0 impact; 0 subs/day → 70 impact
    speed_impact = max(0, min(70, int(70 - (avg_subs / 5) * 70)))
    # Also factor in rating trend — if declining, bump speed impact
    recent = rating_history[-5:] if len(rating_history) >= 5 else rating_history
    net_recent = sum(r.rating_change or 0 for r in recent)
    if net_recent < -50:
        speed_impact = min(100, speed_impact + 15)
    scores.append({
        "factor": "Slow Solving Speed",
        "impact": speed_impact,
        "raw_data": {
            "avg_submissions_per_day": avg_subs,
            "recent_net_rating_change": net_recent,
        },
    })

    # ── Poor Upsolving Habits ─────────────────────────────────────────────────
    # Proxy: ratio of contest rating decreases to total contests
    total_contests = contest_count
    decreases = contest_stats.rating_decreases if contest_stats else 0
    if total_contests > 0:
        decrease_ratio = decreases / total_contests
        # 0% decreases → 10 impact; 70%+ decreases → 80 impact
        upsolve_impact = max(10, min(80, int(10 + decrease_ratio * 100)))
    else:
        upsolve_impact = 30  # No contest data — moderate impact
    scores.append({
        "factor": "Poor Upsolving Habits",
        "impact": upsolve_impact,
        "raw_data": {
            "contest_count": total_contests,
            "rating_decreases": decreases,
            "decrease_ratio": round(decreases / total_contests, 2) if total_contests > 0 else 0,
        },
    })

    # Sort descending by impact
    scores.sort(key=lambda x: x["impact"], reverse=True)
    return scores


def analyze_bottlenecks(db: Session, handle: str) -> BottleneckAnalysis:
    """
    Identify the biggest factors preventing rating growth.

    Pipeline:
      1. Gather all analytics data
      2. Algorithmically pre-score each bottleneck factor
      3. Cache check
      4. Send pre-scored data to LLM for narrative + validation
      5. Store + return BottleneckAnalysis
    """
    logger.info(f"AI bottleneck analysis started: handle={handle}")

    account = _resolve_account(db, handle)
    user_id = account.user_id

    # Gather all data
    analytics = get_user_analytics(db, handle)
    rating_history = get_rating_history(db, handle)
    contest_stats = get_contest_statistics(db, handle)
    activity_stats = get_activity_statistics(db, handle)
    mastery_map = _get_topic_mastery_map(db, handle)
    weak_topics = _get_weak_topics(db, handle)

    logger.info("Data aggregation completed for bottleneck analysis")

    # Algorithmic pre-scoring
    pre_scored = _compute_pre_scores(
        mastery_map=mastery_map,
        analytics=analytics,
        contest_stats=contest_stats,
        activity_stats=activity_stats,
        rating_history=rating_history,
    )

    # Cache check
    cache_key = _make_cache_key("bottleneck_analysis", user_id)
    cached = _get_cached_report(db, cache_key)
    if cached and cached.generated_text:
        logger.info(f"Cache hit for bottleneck analysis: {cache_key}")
        data = json.loads(cached.generated_text)
        bottlenecks = [
            BottleneckItem(
                factor=b["factor"],
                impact=b["impact"],
                description=b.get("description", ""),
            )
            for b in data.get("bottlenecks", [])
        ]
        return BottleneckAnalysis(
            handle=handle,
            bottlenecks=bottlenecks,
            narrative=data.get("narrative", ""),
            cached=True,
            generated_at=cached.created_at,
        )

    context = {
        "handle": handle,
        "current_rating": analytics.current_rating,
        "max_rating": analytics.max_rating,
        "total_contests": analytics.contest_count,
        "problems_solved": analytics.problems_solved,
        "acceptance_rate": analytics.acceptance_rate,
        "avg_submissions_per_day": activity_stats.average_submissions_per_day,
        "avg_solved_per_week": activity_stats.average_solved_per_week,
        "topic_masteries": mastery_map,
        "weak_topics": weak_topics,
        "pre_scored_bottlenecks": pre_scored,
    }

    logger.info("Prompt generated — calling LLM for bottleneck analysis")
    system_prompt, user_prompt = prompt_builder.build_bottleneck_prompt(context)
    llm_result = llm_service.analyze_bottlenecks(system_prompt, user_prompt)
    logger.info("LLM response received for bottleneck analysis")

    raw_bottlenecks = llm_result.get("bottlenecks", [])
    bottleneck_items = []
    for b in raw_bottlenecks:
        try:
            bottleneck_items.append(
                BottleneckItem(
                    factor=str(b.get("factor", "")),
                    impact=int(b.get("impact", 0)),
                    description=str(b.get("description", "")),
                )
            )
        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping malformed bottleneck entry: {b} — {e}")

    # Sort descending
    bottleneck_items.sort(key=lambda x: x.impact, reverse=True)

    generated_text = json.dumps(llm_result)
    _store_report(
        db=db,
        user_id=user_id,
        contest_id_uuid=None,
        report_type="bottleneck_analysis",
        cache_key=cache_key,
        summary=llm_result.get("narrative", "")[:500],
        strengths_text="[]",
        weaknesses_text=json.dumps([b.factor for b in bottleneck_items[:3]]),
        recommendations_text=json.dumps([b.description for b in bottleneck_items[:3]]),
        generated_text=generated_text,
    )

    return BottleneckAnalysis(
        handle=handle,
        bottlenecks=bottleneck_items,
        narrative=llm_result["narrative"],
        cached=False,
        generated_at=datetime.now(timezone.utc),
    )
