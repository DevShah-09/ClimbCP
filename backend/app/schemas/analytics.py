from datetime import date
from pydantic import BaseModel
from typing import Optional

class UserAnalyticsResponse(BaseModel):
    handle: str
    current_rating: Optional[int] = None
    max_rating: Optional[int] = None
    contest_count: int
    problems_solved: int
    acceptance_rate: float
    total_submissions: int
    successful_submissions: int
    failed_submissions: int

class RatingHistoryItem(BaseModel):
    contest_id: str
    contest_name: str
    rank: Optional[int] = None
    old_rating: Optional[int] = None
    new_rating: Optional[int] = None
    rating_change: Optional[int] = None
    contest_date: date

class ContestStatisticsResponse(BaseModel):
    contest_count: int
    average_rank: Optional[float] = None
    best_rank: Optional[int] = None
    worst_rank: Optional[int] = None
    rating_increases: int
    rating_decreases: int
    total_rating_gained: int
    total_rating_lost: int

class ActivityStatisticsResponse(BaseModel):
    first_activity_date: Optional[date] = None
    last_activity_date: Optional[date] = None
    active_days: int
    average_submissions_per_day: float
    average_solved_per_week: float
