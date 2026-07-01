"""
Recommendation Service — Phase 3

All logic operates exclusively on locally stored data.
No Codeforces API calls are made.

Three public functions:
  - get_problem_recommendations()   → Feature 1
  - generate_practice_set()         → Feature 2
  - generate_learning_roadmap()     → Feature 3

Priority Score Formula
──────────────────────
  priority = (topic_weakness_weight * 0.50)
           + (difficulty_match_weight * 0.35)
           + (popularity_weight * 0.15)

All weights are normalised to 0–100 before combining.
"""

import logging
import random
from typing import Optional

from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.models.cf_user import CFUser
from app.models.problem import Problem
from app.models.problem_attempt import ProblemAttempt
from app.models.problem_topic import ProblemTopic
from app.models.topic import Topic
from app.schemas.recommendation import (
    RecommendedProblem,
    ProblemRecommendationResponse,
    PracticeSetProblem,
    PracticeSetMetadata,
    PracticeSetResponse,
    RoadmapTask,
    RoadmapWeek,
    RoadmapResponse,
    RecommendedProblemV2,
    ProblemRecommendationResponseV2,
)
from app.services.topic_service import calculate_topic_mastery, _resolve_user_id
from app.services import cf_problemset_service

logger = logging.getLogger("recommendation_service")

# ── Constants ──────────────────────────────────────────────────────────────────

# How many problems to return for each feature
RECOMMENDATION_LIMIT = 10
PRACTICE_SET_SIZE = 10

# Difficulty window around user rating
EASY_STRETCH_DELTA = -100
CHALLENGE_DELTA = +100
DIFFICULTY_WINDOW = 200   # ± from target for "near level"

# Practice set distribution
WEAK_TOPIC_COUNT = 5
MEDIUM_TOPIC_COUNT = 3
STRONG_TOPIC_COUNT = 2

# Topic mastery thresholds (must align with topic_service.LEVELS)
WEAK_THRESHOLD = 60      # score < 60  → weak
MEDIUM_THRESHOLD = 75    # 60 ≤ score < 75 → medium
# score ≥ 75 → strong

# Per-problem time estimates (minutes) by difficulty tier
TIME_ESTIMATES = {
    "Easy Stretch": 20,
    "Current Level": 35,
    "Challenge": 55,
}

# Topic-specific weekly tasks (lower-cased topic name → task list)
TOPIC_TASKS: dict[str, list[str]] = {
    "dynamic programming": [
        "Solve 10 DP problems focused on this topic",
        "Practice bottom-up formulation for knapsack and LIS",
        "Review memoization vs tabulation trade-offs",
    ],
    "graphs": [
        "Solve 10 Graph problems focused on this topic",
        "Review BFS and DFS traversal from scratch",
        "Implement Dijkstra's shortest path on a weighted graph",
    ],
    "trees": [
        "Solve 10 Tree problems focused on this topic",
        "Practice tree DP and LCA techniques",
        "Implement Euler tour for range queries",
    ],
    "binary search": [
        "Solve 10 Binary Search problems focused on this topic",
        "Practice binary search on the answer",
        "Focus on precise predicate design and boundary conditions",
    ],
    "math": [
        "Solve 10 Math problems focused on this topic",
        "Review modular arithmetic and prime sieve",
        "Practice number theory: GCD, Euler's totient, CRT",
    ],
    "greedy algorithms": [
        "Solve 10 Greedy problems focused on this topic",
        "Study exchange argument proofs",
        "Practice sorting-based greedy and interval scheduling",
    ],
    "data structures": [
        "Solve 10 Data Structures problems focused on this topic",
        "Implement a segment tree and BIT from scratch",
        "Practice sparse tables for range minimum queries",
    ],
    "two pointers": [
        "Solve 10 Two Pointers problems focused on this topic",
        "Focus on sliding window and meet-in-the-middle patterns",
        "Practice problems that require shrinking/expanding windows",
    ],
    "string algorithms": [
        "Solve 10 String problems focused on this topic",
        "Implement KMP and Z-function",
        "Practice string hashing for pattern matching",
    ],
    "number theory": [
        "Solve 10 Number Theory problems focused on this topic",
        "Master GCD/LCM, modular inverse, and CRT",
        "Implement Euler's totient sieve",
    ],
    "combinatorics": [
        "Solve 10 Combinatorics problems focused on this topic",
        "Study inclusion-exclusion principle",
        "Practice generating functions and Burnside's lemma",
    ],
    "geometry": [
        "Solve 10 Geometry problems focused on this topic",
        "Implement convex hull (Graham scan / Andrew's monotone chain)",
        "Practice line intersection and point-in-polygon",
    ],
    "constructive algorithms": [
        "Solve 10 Constructive problems focused on this topic",
        "Practice building solutions incrementally from invariants",
        "Focus on problems that require creative construction",
    ],
    "shortest paths": [
        "Solve 10 Shortest Paths problems focused on this topic",
        "Implement Dijkstra and Bellman-Ford",
        "Study SPFA and Floyd-Warshall for all-pairs shortest paths",
    ],
    "sorting": [
        "Solve 10 Sorting problems focused on this topic",
        "Review merge sort, counting sort, and radix sort",
        "Practice problems with custom comparators",
    ],
    "bitmasking": [
        "Solve 10 Bitmask problems focused on this topic",
        "Practice bitmask DP and set enumeration",
        "Implement subset-sum enumeration over bitmask states",
    ],
    "implementation": [
        "Solve 10 Implementation problems focused on this topic",
        "Focus on clean code and accurate simulation",
        "Practice problems with complex, layered specifications",
    ],
    "flows & matchings": [
        "Solve 10 Flow/Matching problems focused on this topic",
        "Implement Dinic's max-flow algorithm",
        "Practice bipartite matching and min-cut problems",
    ],
}

DEFAULT_TASKS = [
    "Solve 10 problems focused on this topic",
    "Review the core theory and common patterns",
    "Upsolve any problems you could not finish",
]

# Week 3 (combined) and Week 4 (virtual contest) fixed tasks
COMBINED_TASKS = [
    "Solve a mixed problem set covering your two focus topics",
    "Alternate between topic A and topic B in each session",
    "Upsolve any problems you failed during the week",
]

VIRTUAL_CONTEST_TASKS = [
    "Participate in 3 virtual contests on Codeforces",
    "Upsolve every problem you could not solve during each contest",
    "Analyse the editorial for problems rated above your current level",
]


# ── Internal Helpers ───────────────────────────────────────────────────────────

def _get_user_profile(db: Session, handle: str) -> CFUser:
    """Return CFUser or raise ValueError."""
    user = (
        db.query(CFUser)
        .filter(func.lower(CFUser.handle) == handle.lower())
        .first()
    )
    if not user:
        raise ValueError(f"No profile found for handle '{handle}'")
    return user


def _get_solved_problem_ids(db: Session, user_id) -> set:
    """Return a set of problem UUIDs the user has already solved."""
    rows = (
        db.query(ProblemAttempt.problem_id)
        .filter(
            ProblemAttempt.user_id == user_id,
            ProblemAttempt.solved == True,
        )
        .all()
    )
    return {row.problem_id for row in rows}


def _get_solved_problem_codes(db: Session, user_id) -> set[str]:
    """Return a set of problem_code strings the user has already solved."""
    from app.models.problem import Problem as ProblemModel
    rows = (
        db.query(ProblemModel.problem_code)
        .join(ProblemAttempt, ProblemAttempt.problem_id == ProblemModel.id)
        .filter(
            ProblemAttempt.user_id == user_id,
            ProblemAttempt.solved == True,
        )
        .all()
    )
    return {row.problem_code for row in rows}


def _get_topic_mastery_map(db: Session, handle: str) -> dict[str, int]:
    """Return {topic_name: mastery_score} dict, sorted weakest-first."""
    mastery_resp = calculate_topic_mastery(db, handle)
    return {m.topic: m.score for m in mastery_resp.masteries}


def _fetch_candidate_problems(
    db: Session,
    rating_low: int,
    rating_high: int,
    solved_ids: set,
    limit: int = 200,
) -> list[Problem]:
    """
    Fetch unsolved problems within the given rating window.
    Returns up to `limit` rows, randomised to ensure variety.
    """
    query = (
        db.query(Problem)
        .filter(
            Problem.difficulty.isnot(None),
            Problem.difficulty >= rating_low,
            Problem.difficulty <= rating_high,
            ~Problem.id.in_(solved_ids) if solved_ids else True,
        )
        .limit(limit)
        .all()
    )
    random.shuffle(query)
    return query


def _problem_topics(problem: Problem) -> list[str]:
    """Extract topic names from a Problem ORM object (uses eager-loaded relationship)."""
    return [t.name for t in problem.topics]


def _difficulty_tier(problem_rating: Optional[int], user_rating: int) -> str:
    """Classify a problem as Easy Stretch / Current Level / Challenge."""
    if problem_rating is None:
        return "Current Level"
    delta = problem_rating - user_rating
    if delta <= EASY_STRETCH_DELTA:
        return "Easy Stretch"
    if delta >= CHALLENGE_DELTA:
        return "Challenge"
    return "Current Level"


def _topic_weakness_weight(
    topics: list[str],
    mastery_map: dict[str, int],
) -> float:
    """
    0–100.  Average weakness-inverse of topic mastery scores.
    Topics absent from mastery_map are assumed score=50 (neutral).
    """
    if not topics:
        return 50.0
    scores = [mastery_map.get(t, 50) for t in topics]
    avg_mastery = sum(scores) / len(scores)
    return max(0.0, 100.0 - avg_mastery)   # weak topic → high weight


def _difficulty_match_weight(
    problem_rating: Optional[int],
    user_rating: int,
    target_delta: int = 0,
) -> float:
    """
    0–100.  How closely the problem rating matches the desired target.
    Perfect match = 100, every 50-point deviation costs ~25 points.
    """
    if problem_rating is None:
        return 50.0
    target = user_rating + target_delta
    distance = abs(problem_rating - target)
    return max(0.0, 100.0 - (distance / 50.0) * 25.0)


def _popularity_weight(problem: Problem, all_attempts: dict) -> float:
    """
    0–100.  Rough popularity proxy: attempt count normalised to 0–100.
    all_attempts = {problem_id: attempt_count}
    """
    count = all_attempts.get(problem.id, 0)
    return min(count / 500.0, 1.0) * 100.0


def _compute_priority(
    weakness_w: float,
    difficulty_w: float,
    popularity_w: float,
) -> float:
    return round(
        weakness_w * 0.50
        + difficulty_w * 0.35
        + popularity_w * 0.15,
        2,
    )


def _build_reason(
    topics: list[str],
    mastery_map: dict[str, int],
    tier: str,
    user_rating: int,
    problem_rating: Optional[int],
) -> str:
    """Construct a human-readable, explainable reason string."""
    if not topics:
        topic_part = "general practice"
        mastery_part = ""
    else:
        # Lead with the weakest topic among those tagged
        sorted_topics = sorted(topics, key=lambda t: mastery_map.get(t, 50))
        primary = sorted_topics[0]
        score = mastery_map.get(primary, 50)
        topic_part = primary
        mastery_part = f" Your {primary} mastery score is {score}."

    tier_desc = {
        "Easy Stretch": "slightly below your level to build confidence",
        "Current Level": "right at your current rating to maximise learning",
        "Challenge": "above your current level to push your limits",
    }.get(tier, "matched to your level")

    rating_part = f" (rated {problem_rating})" if problem_rating else ""

    return (
        f"This problem targets {topic_part}{rating_part} and is {tier_desc}.{mastery_part}"
    )


def _get_global_attempt_counts(db: Session) -> dict:
    """
    Return {problem_id: total_attempt_count} for all problems.
    Single aggregate query.
    """
    rows = (
        db.query(
            ProblemAttempt.problem_id,
            func.count(ProblemAttempt.id).label("cnt"),
        )
        .group_by(ProblemAttempt.problem_id)
        .all()
    )
    return {row.problem_id: int(row.cnt) for row in rows}


# ── Feature 1: Problem Recommendations ────────────────────────────────────────

def _score_cf_candidate(
    prob: dict,
    user_rating: int,
    mastery_map: dict[str, int],
    global_attempts: dict,
) -> tuple[float, str, str, list[str]]:
    """Score a single CF problemset dict. Returns (priority, tier, reason, topics)."""
    topics   = prob["topics"]
    rating   = prob["rating"]
    tier     = _difficulty_tier(rating, user_rating)
    weakness_w   = _topic_weakness_weight(topics, mastery_map)
    difficulty_w = _difficulty_match_weight(rating, user_rating)
    # Popularity is unknown for CF problems not in our DB — use neutral 50
    priority = _compute_priority(weakness_w, difficulty_w, 50.0)
    reason   = _build_reason(topics, mastery_map, tier, user_rating, rating)
    return priority, tier, reason, topics


def get_problem_recommendations(
    db: Session,
    handle: str,
    limit: int = RECOMMENDATION_LIMIT,
) -> ProblemRecommendationResponse:
    """
    Recommend problems from the full Codeforces problemset (~8,000+ problems).

    Tier distribution (enforced by quota):
        50% Current Level  (user_rating ± 100)
        30% Challenge      (user_rating + 100 to +500)
        20% Easy Stretch   (user_rating - 100 to -500)

    Algorithm
    ---------
    1. Resolve user profile + current rating.
    2. Get the set of problem codes the user has already solved (from DB).
    3. Fetch a large candidate pool from CF (cached 30 min).
    4. Score every candidate; bucket by tier.
    5. Fill each tier bucket by quota (top-scoring within tier), combine.
    """
    logger.info(f"Recommendation generation started for handle: {handle}")

    profile = _get_user_profile(db, handle)
    logger.info(f"User found: {profile.id}, rating={profile.current_rating}")

    user_rating = profile.current_rating or 1200

    # Solved codes (e.g. "1234A") used to exclude from CF pool
    solved_codes = _get_solved_problem_codes(db, profile.id)
    logger.info(f"Solved problems to exclude: {len(solved_codes)}")

    # Mastery map for topic scoring
    try:
        mastery_map = _get_topic_mastery_map(db, handle)
        logger.info(f"Weak topics identified: {[t for t, s in mastery_map.items() if s < WEAK_THRESHOLD]}")
    except ValueError:
        mastery_map = {}
        logger.warning(f"No topic score data for {handle}, using neutral weights")

    # Fetch a wide candidate pool from the live CF problemset
    try:
        cf_candidates = cf_problemset_service.get_candidate_problems(
            user_rating=user_rating,
            solved_codes=solved_codes,
            limit=max(limit * 30, 600),
            half_window=500,   # wider initial window to populate all three tiers
        )
    except RuntimeError as exc:
        logger.error(f"CF problemset fetch failed: {exc}")
        raise ValueError(
            f"Could not fetch problems from Codeforces: {exc}. "
            "Please try again in a moment."
        )

    if not cf_candidates:
        raise ValueError(
            f"No unsolved recommendation candidates found for '{handle}' "
            "in the Codeforces problemset."
        )

    logger.info(f"Scoring {len(cf_candidates)} CF candidates for {handle}")

    # ── Score and bucket by tier ──────────────────────────────────────────────
    buckets: dict[str, list[tuple[float, dict, str, list[str]]]] = {
        "Easy Stretch":  [],
        "Current Level": [],
        "Challenge":     [],
    }

    for prob in cf_candidates:
        priority, tier, reason, topics = _score_cf_candidate(
            prob, user_rating, mastery_map, {}
        )
        buckets[tier].append((priority, prob, reason, topics))

    # Sort each bucket descending by priority
    for tier in buckets:
        buckets[tier].sort(key=lambda x: x[0], reverse=True)

    logger.info(
        f"Tier buckets — Easy: {len(buckets['Easy Stretch'])}, "
        f"Current: {len(buckets['Current Level'])}, "
        f"Challenge: {len(buckets['Challenge'])}"
    )

    # ── Enforce quota: 20% Easy / 50% Current / 30% Challenge ────────────────
    n_easy      = max(1, round(limit * 0.20))
    n_challenge = max(1, round(limit * 0.30))
    n_current   = limit - n_easy - n_challenge

    def _pick(tier: str, count: int) -> list[tuple]:
        """Take top `count` from a tier bucket, falling short gracefully."""
        return buckets[tier][:count]

    selected = (
        _pick("Easy Stretch",  n_easy)
        + _pick("Current Level", n_current)
        + _pick("Challenge",     n_challenge)
    )

    # If any tier was under-populated, redistribute to whichever has spares
    deficit = limit - len(selected)
    if deficit > 0:
        picked_codes = {item[1]["problem_code"] for item in selected}
        for tier in ("Current Level", "Challenge", "Easy Stretch"):
            for entry in buckets[tier]:
                if deficit <= 0:
                    break
                if entry[1]["problem_code"] not in picked_codes:
                    selected.append(entry)
                    picked_codes.add(entry[1]["problem_code"])
                    deficit -= 1

    recommendations = [
        RecommendedProblem(
            problem_id=prob["problem_code"],
            problem_code=prob["problem_code"],
            name=prob["name"],
            rating=prob["rating"],
            topics=topics,
            difficulty_tier=_difficulty_tier(prob["rating"], user_rating),
            priority_score=round(priority, 2),
            reason=reason,
        )
        for priority, prob, reason, topics in selected
    ]

    logger.info(
        f"Generated {len(recommendations)} recommendations for {handle} "
        f"(easy={n_easy}, current={n_current}, challenge={n_challenge})"
    )
    return ProblemRecommendationResponse(
        handle=handle,
        user_rating=profile.current_rating,
        recommendations=recommendations,
    )


# ── Feature 2: Practice Set Generator ────────────────────────────────────────

def generate_practice_set(db: Session, handle: str) -> PracticeSetResponse:
    """
    Generate a balanced 10-problem practice set.

    Distribution
    ────────────
    5 weak-topic  + 3 medium-topic + 2 strong-topic problems
    40% Easy Stretch + 40% Current Level + 20% Challenge
    No already-solved problems, no duplicates.
    """
    logger.info(f"Practice set generation started for handle: {handle}")

    profile = _get_user_profile(db, handle)
    logger.info(f"User found: {profile.id}")

    user_rating = profile.current_rating or 1200
    solved_ids = _get_solved_problem_ids(db, profile.id)

    try:
        mastery_map = _get_topic_mastery_map(db, handle)
    except ValueError:
        mastery_map = {}
        logger.warning(f"No mastery data for {handle}; using neutral topic weights")

    # Classify topics
    weak_topics = [t for t, s in mastery_map.items() if s < WEAK_THRESHOLD]
    medium_topics = [t for t, s in mastery_map.items() if WEAK_THRESHOLD <= s < MEDIUM_THRESHOLD]
    strong_topics = [t for t, s in mastery_map.items() if s >= MEDIUM_THRESHOLD]

    logger.info(
        f"Topics classified — weak: {len(weak_topics)}, "
        f"medium: {len(medium_topics)}, strong: {len(strong_topics)}"
    )

    global_attempts = _get_global_attempt_counts(db)

    # Tier targets (4 easy, 4 medium, 2 challenge)
    easy_target = user_rating + EASY_STRETCH_DELTA
    current_target = user_rating
    challenge_target = user_rating + CHALLENGE_DELTA

    def _pick_problems(
        topic_filter: list[str],
        category: str,
        count: int,
        used_ids: set,
    ) -> list[PracticeSetProblem]:
        """Pick `count` problems matching any of the given topics."""
        results: list[PracticeSetProblem] = []
        tier_quota = {"Easy Stretch": 0, "Current Level": 0, "Challenge": 0}

        # Determine how many of each tier to pick for this batch
        total = count
        n_challenge = max(1, round(total * 0.20))
        n_easy = max(1, round(total * 0.40))
        n_current = total - n_easy - n_challenge

        tier_quota["Easy Stretch"] = n_easy
        tier_quota["Current Level"] = n_current
        tier_quota["Challenge"] = n_challenge

        # Gather candidates in wide window
        rating_low = max(800, user_rating - 300)
        rating_high = user_rating + 300

        candidates = _fetch_candidate_problems(
            db, rating_low, rating_high, solved_ids | used_ids, limit=400
        )

        # Filter to relevant topics if we have a topic filter
        if topic_filter:
            topic_set = set(t.lower() for t in topic_filter)
            relevant = [
                p for p in candidates
                if any(t.name.lower() in topic_set for t in p.topics)
            ]
            # Fall back to any candidate if filtered list is too small
            if len(relevant) < count:
                extra = [p for p in candidates if p not in relevant]
                relevant += extra[: count - len(relevant)]
        else:
            relevant = candidates

        tier_counts = {"Easy Stretch": 0, "Current Level": 0, "Challenge": 0}

        for prob in relevant:
            if len(results) >= count:
                break
            tier = _difficulty_tier(prob.difficulty, user_rating)
            if tier_counts[tier] >= tier_quota[tier]:
                continue
            tier_counts[tier] += 1
            used_ids.add(prob.id)

            topics = _problem_topics(prob)
            reason = _build_reason(topics, mastery_map, tier, user_rating, prob.difficulty)
            results.append(
                PracticeSetProblem(
                    problem_id=str(prob.id),
                    problem_code=prob.problem_code,
                    name=prob.title,
                    rating=prob.difficulty,
                    topics=topics,
                    difficulty_tier=tier,
                    category=category,
                    reason=reason,
                )
            )

        # If we still don't have enough, fill with any remaining candidates
        if len(results) < count:
            fill = [p for p in relevant if p.id not in used_ids]
            for prob in fill:
                if len(results) >= count:
                    break
                used_ids.add(prob.id)
                topics = _problem_topics(prob)
                tier = _difficulty_tier(prob.difficulty, user_rating)
                reason = _build_reason(topics, mastery_map, tier, user_rating, prob.difficulty)
                results.append(
                    PracticeSetProblem(
                        problem_id=str(prob.id),
                        problem_code=prob.problem_code,
                        name=prob.title,
                        rating=prob.difficulty,
                        topics=topics,
                        difficulty_tier=tier,
                        category=category,
                        reason=reason,
                    )
                )

        return results

    used_ids: set = set(solved_ids)
    practice_set: list[PracticeSetProblem] = []

    practice_set += _pick_problems(weak_topics, "Weak Topic", WEAK_TOPIC_COUNT, used_ids)
    practice_set += _pick_problems(medium_topics, "Medium Topic", MEDIUM_TOPIC_COUNT, used_ids)
    practice_set += _pick_problems(strong_topics, "Strong Topic", STRONG_TOPIC_COUNT, used_ids)

    if not practice_set:
        raise ValueError(
            f"No recommendation candidates available to build a practice set for '{handle}'."
        )

    # Compute metadata
    easy_c = sum(1 for p in practice_set if p.difficulty_tier == "Easy Stretch")
    med_c = sum(1 for p in practice_set if p.difficulty_tier == "Current Level")
    chal_c = sum(1 for p in practice_set if p.difficulty_tier == "Challenge")

    total_minutes = (
        easy_c * TIME_ESTIMATES["Easy Stretch"]
        + med_c * TIME_ESTIMATES["Current Level"]
        + chal_c * TIME_ESTIMATES["Challenge"]
    )
    hours = total_minutes // 60
    mins = total_minutes % 60
    estimated_time = f"{hours}h {mins}m" if mins else f"{hours}h"

    # Focus topics = top 2 weakest
    focus_topics = sorted(mastery_map, key=lambda t: mastery_map[t])[:2]

    metadata = PracticeSetMetadata(
        estimated_time=estimated_time,
        focus_topics=focus_topics,
        weak_topic_count=sum(1 for p in practice_set if p.category == "Weak Topic"),
        medium_topic_count=sum(1 for p in practice_set if p.category == "Medium Topic"),
        strong_topic_count=sum(1 for p in practice_set if p.category == "Strong Topic"),
        easy_count=easy_c,
        medium_count=med_c,
        challenge_count=chal_c,
    )

    logger.info(f"Practice set generated: {len(practice_set)} problems for {handle}")
    return PracticeSetResponse(
        handle=handle,
        user_rating=profile.current_rating,
        practice_set=practice_set,
        metadata=metadata,
    )


# ── Feature 3: Learning Roadmap ───────────────────────────────────────────────

def generate_learning_roadmap(db: Session, handle: str) -> RoadmapResponse:
    """
    Generate a 4-week structured learning roadmap.

    Structure
    ─────────
    Week 1: Weakest topic (deep dive)
    Week 2: Second weakest topic (deep dive)
    Week 3: Combined practice — both topics together
    Week 4: Virtual contest training + upsolving
    """
    logger.info(f"Roadmap generation started for handle: {handle}")

    profile = _get_user_profile(db, handle)
    logger.info(f"User found: {profile.id}")

    user_rating = profile.current_rating or 1200

    try:
        mastery_map = _get_topic_mastery_map(db, handle)
    except ValueError:
        raise ValueError(
            f"No topic score data available for '{handle}'. "
            "Please sync your Codeforces data and try again."
        )

    if not mastery_map:
        raise ValueError(
            f"No topic scores found for '{handle}'. Cannot generate a roadmap."
        )

    # Sort topics weakest → strongest
    sorted_topics = sorted(mastery_map.items(), key=lambda x: x[1])

    week1_topic, week1_score = sorted_topics[0]
    week2_topic, week2_score = sorted_topics[1] if len(sorted_topics) > 1 else (week1_topic, week1_score)

    logger.info(
        f"Weak topics identified: Week1={week1_topic} ({week1_score}), "
        f"Week2={week2_topic} ({week2_score})"
    )

    def _tasks_for_topic(topic: str) -> list[RoadmapTask]:
        task_strs = TOPIC_TASKS.get(topic.lower(), DEFAULT_TASKS)
        return [RoadmapTask(description=t) for t in task_strs]

    weeks: list[RoadmapWeek] = [
        RoadmapWeek(
            week=1,
            theme="Foundation — Weakest Topic",
            focus=[week1_topic],
            tasks=_tasks_for_topic(week1_topic),
            target_problems=10,
        ),
        RoadmapWeek(
            week=2,
            theme="Deep Dive — Second Weakest Topic",
            focus=[week2_topic],
            tasks=_tasks_for_topic(week2_topic),
            target_problems=10,
        ),
        RoadmapWeek(
            week=3,
            theme="Combined Practice",
            focus=[week1_topic, week2_topic],
            tasks=[RoadmapTask(description=t) for t in COMBINED_TASKS],
            target_problems=15,
        ),
        RoadmapWeek(
            week=4,
            theme="Virtual Contest Training",
            focus=[week1_topic, week2_topic, "All Topics"],
            tasks=[RoadmapTask(description=t) for t in VIRTUAL_CONTEST_TASKS],
            target_problems=20,
        ),
    ]

    focus_summary = (
        f"4-week plan for rating {user_rating}: "
        f"Week 1 strengthens {week1_topic} (score {week1_score}), "
        f"Week 2 targets {week2_topic} (score {week2_score}), "
        f"Week 3 combines both topics, "
        f"Week 4 applies everything in virtual contests."
    )

    logger.info(f"Roadmap generated for {handle}")
    return RoadmapResponse(
        handle=handle,
        user_rating=profile.current_rating,
        weeks=weeks,
        total_weeks=4,
        focus_summary=focus_summary,
    )


# ── Feature 5: V2 Problem Recommendations (Embedding-Based) ─────────────────

def get_recommendations_v2(
    db: Session,
    handle: str,
    limit: int = 10,
) -> ProblemRecommendationResponseV2:
    """
    Generate embedding-based recommendations for a user.
    Looks at unsolved problems they struggled with recently, and recommends
    semantically similar problems using vector search.
    """
    from app.services.problem_embedding_service import find_similar_problems
    from app.schemas.recommendation import ProblemRecommendationResponseV2, RecommendedProblemV2
    import uuid

    profile = _get_user_profile(db, handle)
    user_id = profile.id

    # 1. Fetch user's failed attempts (attempted > 0, solved == False)
    failed_attempts = (
        db.query(ProblemAttempt, Problem)
        .join(Problem, Problem.id == ProblemAttempt.problem_id)
        .filter(
            ProblemAttempt.user_id == user_id,
            ProblemAttempt.solved == False,
            ProblemAttempt.attempts > 0
        )
        .order_by(ProblemAttempt.attempts.desc())
        .all()
    )

    # Fetch set of solved/attempted problem IDs to exclude
    solved_ids = _get_solved_problem_ids(db, user_id)
    
    recommendations = []
    recommended_ids = set()

    # 2. Loop over failed problems and find similar problems
    for attempt, prob in failed_attempts:
        if len(recommendations) >= limit:
            break
        try:
            # Get similar problems
            similar = find_similar_problems(db, attempt.problem_id, limit=limit)
            
            for sim in similar:
                sim_uuid_str = sim["problem_id"]
                sim_uuid_obj = uuid.UUID(sim_uuid_str)
                
                # Filter out solved, already attempted, or already recommended problems
                if sim_uuid_obj in solved_ids or sim_uuid_obj in recommended_ids:
                    continue
                
                recommended_ids.add(sim_uuid_obj)
                
                # Retrieve problem code
                p_code = db.query(Problem.problem_code).filter(Problem.id == sim_uuid_obj).scalar() or ""
                
                # Build reasoning
                reason = f"Similar to '{prob.title}' where you had {attempt.attempts} failed attempts."
                
                recommendations.append(RecommendedProblemV2(
                    problem_id=sim_uuid_str,
                    problem_code=p_code,
                    name=sim["name"],
                    rating=sim["rating"],
                    reason=reason
                ))
                
                if len(recommendations) >= limit:
                    break
        except Exception as e:
            logger.error(f"Error finding similar problems for failed problem {attempt.problem_id}: {e}")

    # 3. Fallback: If no recommendations generated, recommend problems from their weakest concept clusters
    if not recommendations:
        from app.services.concept_clustering_service import get_weak_concepts
        try:
            weak_concepts = get_weak_concepts(db, handle)
            if weak_concepts:
                # Pick top weak concept
                top_weak = weak_concepts[0]
                concept_name = top_weak["concept"]
                for rec in top_weak["recommendations"]:
                    if len(recommendations) >= limit:
                        break
                    recommendations.append(RecommendedProblemV2(
                        problem_id=rec["problem_id"],
                        problem_code=rec["problem_code"],
                        name=rec["name"],
                        rating=rec["rating"],
                        reason=f"Recommended to strengthen your understanding of '{concept_name}' (mastery: {top_weak['mastery']}%)."
                    ))
        except Exception as e:
            logger.error(f"Error generating fallback recommendations: {e}")

    # 4. Absolute fallback: If still empty, return some candidates from overall pool
    if not recommendations:
        try:
            rating = profile.current_rating or 1200
            candidates = _fetch_candidate_problems(
                db, 
                rating_low=max(800, rating - 200), 
                rating_high=rating + 200, 
                solved_ids=solved_ids, 
                limit=limit
            )
            for c in candidates:
                recommendations.append(RecommendedProblemV2(
                    problem_id=str(c.id),
                    problem_code=c.problem_code,
                    name=c.title,
                    rating=c.difficulty,
                    reason="Recommended for general competitive programming practice."
                ))
        except Exception as e:
            logger.error(f"Error generating absolute fallback: {e}")

    return ProblemRecommendationResponseV2(
        handle=handle,
        recommendations=recommendations[:limit]
    )

