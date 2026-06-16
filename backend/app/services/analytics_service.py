from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.cp_profile import CPProfile
from app.models.contest_participation import ContestParticipation
from app.models.contest import Contest
from app.models.problem_attempt import ProblemAttempt
from app.schemas.analytics import (
    UserAnalyticsResponse,
    RatingHistoryItem,
    ContestStatisticsResponse,
    ActivityStatisticsResponse
)


def get_user_analytics(db: Session, handle: str) -> UserAnalyticsResponse:
    profile = db.query(CPProfile).filter(func.lower(CPProfile.handle) == handle.lower()).first()
    if not profile:
        raise ValueError(f"User with handle {handle} not found")

    user_id = profile.user_id

    contest_count = db.query(func.count(ContestParticipation.id)).filter(
        ContestParticipation.user_id == user_id
    ).scalar() or 0

    problems_solved = db.query(func.count(ProblemAttempt.id)).filter(
        ProblemAttempt.user_id == user_id,
        ProblemAttempt.solved == True
    ).scalar() or 0

    total_submissions = db.query(func.sum(ProblemAttempt.attempts)).filter(
        ProblemAttempt.user_id == user_id
    ).scalar() or 0

    successful_submissions = problems_solved
    failed_submissions = max(0, total_submissions - successful_submissions)

    acceptance_rate = 0.0
    if total_submissions > 0:
        acceptance_rate = round((successful_submissions / total_submissions) * 100, 2)

    return UserAnalyticsResponse(
        handle=profile.handle,
        current_rating=profile.current_rating,
        max_rating=profile.max_rating,
        contest_count=contest_count,
        problems_solved=problems_solved,
        acceptance_rate=acceptance_rate,
        total_submissions=total_submissions,
        successful_submissions=successful_submissions,
        failed_submissions=failed_submissions
    )


def get_rating_history(db: Session, handle: str) -> List[RatingHistoryItem]:
    profile = db.query(CPProfile).filter(func.lower(CPProfile.handle) == handle.lower()).first()
    if not profile:
        raise ValueError(f"User with handle {handle} not found")

    participations = db.query(ContestParticipation).join(Contest).filter(
        ContestParticipation.user_id == profile.user_id,
        ContestParticipation.rating_change.isnot(None)
    ).order_by(Contest.start_time.asc()).all()

    history = []
    for p in participations:
        history.append(RatingHistoryItem(
            contest_id=p.contest.contest_code,
            contest_name=p.contest.contest_name,
            rank=p.rank,
            old_rating=p.rating_before,
            new_rating=p.rating_after,
            rating_change=p.rating_change,
            contest_date=p.contest.start_time.date()
        ))
    return history


def get_contest_statistics(db: Session, handle: str) -> ContestStatisticsResponse:
    profile = db.query(CPProfile).filter(func.lower(CPProfile.handle) == handle.lower()).first()
    if not profile:
        raise ValueError(f"User with handle {handle} not found")

    participations = db.query(ContestParticipation).filter(
        ContestParticipation.user_id == profile.user_id,
        ContestParticipation.rating_change.isnot(None)
    ).all()

    contest_count = len(participations)
    
    if contest_count == 0:
        return ContestStatisticsResponse(
            contest_count=0,
            rating_increases=0,
            rating_decreases=0,
            total_rating_gained=0,
            total_rating_lost=0
        )

    ranks = [p.rank for p in participations if p.rank is not None]
    average_rank = sum(ranks) / len(ranks) if ranks else None
    best_rank = min(ranks) if ranks else None
    worst_rank = max(ranks) if ranks else None

    rating_increases = 0
    rating_decreases = 0
    total_rating_gained = 0
    total_rating_lost = 0

    for p in participations:
        if p.rating_change and p.rating_change > 0:
            rating_increases += 1
            total_rating_gained += p.rating_change
        elif p.rating_change and p.rating_change < 0:
            rating_decreases += 1
            total_rating_lost += abs(p.rating_change)

    return ContestStatisticsResponse(
        contest_count=contest_count,
        average_rank=round(average_rank, 2) if average_rank is not None else None,
        best_rank=best_rank,
        worst_rank=worst_rank,
        rating_increases=rating_increases,
        rating_decreases=rating_decreases,
        total_rating_gained=total_rating_gained,
        total_rating_lost=total_rating_lost
    )


def get_activity_statistics(db: Session, handle: str) -> ActivityStatisticsResponse:
    profile = db.query(CPProfile).filter(func.lower(CPProfile.handle) == handle.lower()).first()
    if not profile:
        raise ValueError(f"User with handle {handle} not found")

    user_id = profile.user_id

    # Get submission dates
    first_sub = db.query(func.min(ProblemAttempt.submitted_at)).filter(
        ProblemAttempt.user_id == user_id
    ).scalar()
    
    last_sub = db.query(func.max(ProblemAttempt.submitted_at)).filter(
        ProblemAttempt.user_id == user_id
    ).scalar()

    # Get contest dates
    first_contest_part = db.query(func.min(Contest.start_time)).join(
        ContestParticipation, Contest.id == ContestParticipation.contest_id
    ).filter(
        ContestParticipation.user_id == user_id
    ).scalar()

    last_contest_part = db.query(func.max(Contest.start_time)).join(
        ContestParticipation, Contest.id == ContestParticipation.contest_id
    ).filter(
        ContestParticipation.user_id == user_id
    ).scalar()

    dates = [d for d in [first_sub, last_sub, first_contest_part, last_contest_part] if d is not None]
    
    if not dates:
        return ActivityStatisticsResponse(
            active_days=0,
            average_submissions_per_day=0.0,
            average_solved_per_week=0.0
        )

    first_activity_date = min(dates).date()
    last_activity_date = max(dates).date()
    
    active_days = (last_activity_date - first_activity_date).days + 1

    total_submissions = db.query(func.sum(ProblemAttempt.attempts)).filter(
        ProblemAttempt.user_id == user_id
    ).scalar() or 0

    problems_solved = db.query(func.count(ProblemAttempt.id)).filter(
        ProblemAttempt.user_id == user_id,
        ProblemAttempt.solved == True
    ).scalar() or 0

    avg_subs_per_day = round(total_submissions / active_days, 2) if active_days > 0 else 0.0
    
    weeks = max(1, active_days / 7)
    avg_solved_per_week = round(problems_solved / weeks, 2)

    return ActivityStatisticsResponse(
        first_activity_date=first_activity_date,
        last_activity_date=last_activity_date,
        active_days=active_days,
        average_submissions_per_day=avg_subs_per_day,
        average_solved_per_week=avg_solved_per_week
    )
