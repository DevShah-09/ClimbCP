import logging
import uuid
import requests
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func

from app.models.cf_user import CFUser
from app.models.contest import Contest
from app.models.contest_participation import ContestParticipation
from app.models.problem import Problem
from app.models.problem_attempt import ProblemAttempt
from app.models.topic import Topic

# Set up logging
logger = logging.getLogger("codeforces_sync")
# Standard format output for debugging if needed
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Custom exceptions for mapping to HTTP status codes
class CodeforcesException(Exception):
    pass

class InvalidHandleException(CodeforcesException):
    pass

class CodeforcesUnavailableException(CodeforcesException):
    pass

class CodeforcesTimeoutException(CodeforcesException):
    pass


# Map Codeforces tags to local seeded Topics
TAG_TO_TOPIC_MAP = {
    "implementation": "Implementation",
    "math": "Math",
    "greedy": "Greedy Algorithms",
    "dp": "Dynamic Programming",
    "data structures": "Data Structures",
    "graphs": "Graphs",
    "trees": "Trees",
    "binary search": "Binary Search",
    "two pointers": "Two Pointers",
    "sortings": "Sorting",
    "bitmasks": "Bitmasking",
    "number theory": "Number Theory",
    "combinatorics": "Combinatorics",
    "constructive algorithms": "Constructive Algorithms",
    "shortest paths": "Shortest Paths",
    "strings": "String Algorithms",
    "flows": "Flows & Matchings",
    "geometry": "Geometry"
}


def get_user_info(handle: str) -> Dict[str, Any]:
    """
    Fetch user info from Codeforces API (user.info endpoint).
    """
    url = f"https://codeforces.com/api/user.info?handles={handle}"
    try:
        response = requests.get(url, timeout=10.0)
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout while fetching user info for handle {handle}: {e}")
        raise CodeforcesTimeoutException("Codeforces API request timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception while fetching user info for handle {handle}: {e}")
        if "timeout" in str(e).lower() or "time out" in str(e).lower():
            raise CodeforcesTimeoutException("Codeforces API request timed out")
        raise CodeforcesUnavailableException("Codeforces API is unavailable")

    if response.status_code == 400:
        try:
            data = response.json()
            comment = data.get("comment", "")
            if "not found" in comment.lower() or "handles:" in comment.lower():
                raise InvalidHandleException(f"Handle '{handle}' not found on Codeforces")
        except ValueError:
            pass
        raise InvalidHandleException(f"Invalid handle '{handle}'")

    if response.status_code != 200:
        raise CodeforcesUnavailableException(f"Codeforces API returned status code {response.status_code}")

    try:
        data = response.json()
    except ValueError:
        raise CodeforcesUnavailableException("Invalid JSON response from Codeforces API")

    if data.get("status") != "OK":
        comment = data.get("comment", "")
        if "not found" in comment.lower() or "handles:" in comment.lower():
            raise InvalidHandleException(f"Handle '{handle}' not found on Codeforces")
        raise CodeforcesException(f"Codeforces API error: {comment}")

    result = data.get("result")
    if not result or len(result) == 0:
        raise InvalidHandleException(f"Handle '{handle}' not found on Codeforces")

    return result[0]


def get_user_rating_history(handle: str) -> List[Dict[str, Any]]:
    """
    Fetch user rating history from Codeforces API (user.rating endpoint).
    """
    url = f"https://codeforces.com/api/user.rating?handle={handle}"
    try:
        response = requests.get(url, timeout=10.0)
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout while fetching rating history for handle {handle}: {e}")
        raise CodeforcesTimeoutException("Codeforces API request timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception while fetching rating history for handle {handle}: {e}")
        if "timeout" in str(e).lower() or "time out" in str(e).lower():
            raise CodeforcesTimeoutException("Codeforces API request timed out")
        raise CodeforcesUnavailableException("Codeforces API is unavailable")

    if response.status_code == 400:
        try:
            data = response.json()
            comment = data.get("comment", "")
            if "not found" in comment.lower() or "handle:" in comment.lower():
                raise InvalidHandleException(f"Handle '{handle}' not found on Codeforces")
        except ValueError:
            pass
        raise InvalidHandleException(f"Invalid handle '{handle}'")

    if response.status_code != 200:
        raise CodeforcesUnavailableException(f"Codeforces API returned status code {response.status_code}")

    try:
        data = response.json()
    except ValueError:
        raise CodeforcesUnavailableException("Invalid JSON response from Codeforces API")

    if data.get("status") != "OK":
        comment = data.get("comment", "")
        if "not found" in comment.lower() or "handle:" in comment.lower():
            raise InvalidHandleException(f"Handle '{handle}' not found on Codeforces")
        raise CodeforcesException(f"Codeforces API error: {comment}")

    return data.get("result", [])


def get_user_submissions(handle: str) -> List[Dict[str, Any]]:
    """
    Fetch user status/submissions from Codeforces API (user.status endpoint).
    """
    url = f"https://codeforces.com/api/user.status?handle={handle}"
    try:
        response = requests.get(url, timeout=30.0)
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout while fetching submissions for handle {handle}: {e}")
        raise CodeforcesTimeoutException("Codeforces API request timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception while fetching submissions for handle {handle}: {e}")
        if "timeout" in str(e).lower() or "time out" in str(e).lower():
            raise CodeforcesTimeoutException("Codeforces API request timed out")
        raise CodeforcesUnavailableException("Codeforces API is unavailable")

    if response.status_code == 400:
        try:
            data = response.json()
            comment = data.get("comment", "")
            if "not found" in comment.lower() or "handle:" in comment.lower():
                raise InvalidHandleException(f"Handle '{handle}' not found on Codeforces")
        except ValueError:
            pass
        raise InvalidHandleException(f"Invalid handle '{handle}'")

    if response.status_code != 200:
        raise CodeforcesUnavailableException(f"Codeforces API returned status code {response.status_code}")

    try:
        data = response.json()
    except ValueError:
        raise CodeforcesUnavailableException("Invalid JSON response from Codeforces API")

    if data.get("status") != "OK":
        comment = data.get("comment", "")
        if "not found" in comment.lower() or "handle:" in comment.lower():
            raise InvalidHandleException(f"Handle '{handle}' not found on Codeforces")
        raise CodeforcesException(f"Codeforces API error: {comment}")

    return data.get("result", [])


def _insert_missing(db: Session, model, rows: List[Dict[str, Any]], key: str) -> None:
    """Let the database arbitrate concurrent inserts, then callers reload real IDs."""
    if db.get_bind().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    elif db.get_bind().dialect.name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else:
        raise RuntimeError("Profile sync requires PostgreSQL or SQLite")
    # A stable lock order avoids competing multi-row inserts taking locks in reverse order.
    unique_rows = {row[key]: row for row in rows}
    ordered = [unique_rows[value] for value in sorted(unique_rows)]
    for offset in range(0, len(ordered), 100):
        db.execute(insert(model.__table__).values(ordered[offset:offset + 100])
                   .on_conflict_do_nothing(index_elements=[key]))


def sync_user_data(db: Session, handle: str) -> Dict[str, Any]:
    """
    Synchronize Codeforces user details, rating history (contests), and submissions (attempts)
    to the database, ensuring idempotency.
    """
    logger.info(f"Sync started for Codeforces handle: {handle}")

    try:
        # Step 1: Check whether the handle exists & Step 2: Fetch profile information
        cf_profile_info = get_user_info(handle)
        official_handle = cf_profile_info.get("handle", handle)
        logger.info(f"User fetched from Codeforces: {official_handle}")

        # Finish network requests before opening a database transaction.
        rating_history = get_user_rating_history(official_handle)
        submissions = get_user_submissions(official_handle)

        # Serialize writes for the same user across workers and browser tabs.
        # External API calls above never hold a database row lock.
        user = db.query(CFUser).filter(
            func.lower(CFUser.handle) == official_handle.lower()
        ).with_for_update().first()
        if user is None:
            _insert_missing(db, CFUser, [{
                "id": uuid.uuid4(), "handle": official_handle,
                "current_rating": cf_profile_info.get("rating"),
                "max_rating": cf_profile_info.get("maxRating"),
            }], "handle")
            user = db.query(CFUser).filter(
                func.lower(CFUser.handle) == official_handle.lower()
            ).with_for_update().first()
        user.handle = official_handle
        user.current_rating = cf_profile_info.get("rating")
        user.max_rating = cf_profile_info.get("maxRating")

        # Contests are shared by every user. A pre-insert SELECT alone cannot
        # prevent another transaction creating the same contest in the meantime.
        contest_rows = []
        for change in rating_history:
            rating_time = datetime.fromtimestamp(change["ratingUpdateTimeSeconds"])
            contest_rows.append({
                "id": uuid.uuid4(), "platform": "codeforces",
                "contest_code": str(change["contestId"]),
                "contest_name": change["contestName"],
                "start_time": rating_time, "end_time": rating_time,
            })
        _insert_missing(db, Contest, contest_rows, "contest_code")
        contest_codes = sorted({row["contest_code"] for row in contest_rows})
        contests = {}
        for offset in range(0, len(contest_codes), 500):
            # Match the actual globally unique key, not an extra platform filter.
            contests.update({c.contest_code: c for c in db.query(Contest).filter(
                Contest.contest_code.in_(contest_codes[offset:offset + 500]),
            ).all()})
        participations = {p.contest_id: p for p in db.query(ContestParticipation).filter(
            ContestParticipation.user_id == user.id
        ).all()}

        # Step 5: Store contest participations (avoid duplicate contests & participations)
        contests_synced = 0
        for rating_change in rating_history:
            contest_code = str(rating_change["contestId"])

            contest = contests[contest_code]

            # Find or create ContestParticipation
            participation = participations.get(contest.id)

            rating_change_val = rating_change["newRating"] - rating_change["oldRating"]
            if not participation:
                participation = ContestParticipation(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    contest_id=contest.id,
                    rank=rating_change["rank"],
                    score=None,
                    rating_before=rating_change["oldRating"],
                    rating_after=rating_change["newRating"],
                    rating_change=rating_change_val,
                    problems_solved=None
                )
                db.add(participation)
                participations[contest.id] = participation
                contests_synced += 1
            else:
                # Update participation stats if they changed
                participation.rank = rating_change["rank"]
                participation.rating_before = rating_change["oldRating"]
                participation.rating_after = rating_change["newRating"]
                participation.rating_change = rating_change_val

        db.flush()
        logger.info(f"Number of contests stored: {contests_synced}")

        # Step 7 & 8: Store submissions & Create problem records if they do not already exist
        all_topics = db.query(Topic).all()
        topic_name_map = {t.name.lower(): t for t in all_topics}

        # Group submissions by problem code (contestId + index)
        submissions_by_problem = {}
        for s in submissions:
            prob = s.get("problem", {})
            contest_id = prob.get("contestId")
            index = prob.get("index")
            if contest_id is not None and index is not None:
                prob_code = f"{contest_id}{index}"
                submissions_by_problem.setdefault(prob_code, []).append(s)

        submissions_synced = len(submissions)
        problem_rows = []
        for code, problem_submissions in submissions_by_problem.items():
            info = problem_submissions[0]["problem"]
            problem_rows.append({
                "id": uuid.uuid4(), "platform": "codeforces", "problem_code": code,
                "title": info.get("name", "Unknown"), "difficulty": info.get("rating"),
            })
        _insert_missing(db, Problem, problem_rows, "problem_code")
        problem_codes = sorted(submissions_by_problem)
        problems = {}
        for offset in range(0, len(problem_codes), 500):
            problems.update({p.problem_code: p for p in db.query(Problem).options(
                selectinload(Problem.topics)
            ).filter(
                Problem.problem_code.in_(problem_codes[offset:offset + 500]),
            ).order_by(Problem.problem_code).with_for_update().all()})
        attempts = {a.problem_id: a for a in db.query(ProblemAttempt).filter(
            ProblemAttempt.user_id == user.id
        ).all()}

        for prob_code, prob_submissions in submissions_by_problem.items():
            # Get problem details from the first submission
            sample_sub = prob_submissions[0]
            prob_info = sample_sub["problem"]
            contest_id = prob_info["contestId"]
            index = prob_info["index"]
            title = prob_info.get("name", "Unknown")
            difficulty = prob_info.get("rating")
            tags = prob_info.get("tags", [])

            # Reloaded IDs include rows inserted by another transaction. Row
            # locks also protect shared topic associations while they are updated.
            problem = problems[prob_code]
            if difficulty is not None:
                problem.difficulty = difficulty
            problem.title = title
            problem.topics = [topic_name_map[name.lower()] for name in sorted({
                TAG_TO_TOPIC_MAP[tag.lower()] for tag in tags if tag.lower() in TAG_TO_TOPIC_MAP
            }) if name.lower() in topic_name_map]

            # Sort submissions chronologically (ascending creationTimeSeconds)
            prob_submissions.sort(key=lambda x: x.get("creationTimeSeconds", 0))

            # Compute attempt aggregates
            attempts_count = len(prob_submissions)

            # Find the first accepted submission
            accepted_sub = None
            for s in prob_submissions:
                if s.get("verdict") == "OK":
                    accepted_sub = s
                    break

            # Find if there was any attempt during a contest (participantType == "CONTESTANT")
            during_contest = any(s.get("author", {}).get("participantType") == "CONTESTANT" for s in prob_submissions)

            participation_id = None
            if during_contest:
                # Find the ContestParticipation to link
                contest_code_str = str(contest_id)
                contest_obj = contests.get(contest_code_str)
                part_obj = participations.get(contest_obj.id) if contest_obj else None
                if part_obj:
                    participation_id = part_obj.id

            solved = accepted_sub is not None

            if solved:
                # Find submissions before the first accepted submission, excluding compilation errors
                first_ok_time = accepted_sub.get("creationTimeSeconds", 0)
                subs_before = [s for s in prob_submissions if s.get("creationTimeSeconds", 0) < first_ok_time]
                penalty = sum(1 for s in subs_before if s.get("verdict") != "COMPILATION_ERROR")

                submitted_at = datetime.fromtimestamp(first_ok_time)
                verdict = "OK"
                language = accepted_sub.get("programmingLanguage")

                # Check if the accepted submission itself was during the contest
                if accepted_sub.get("author", {}).get("participantType") == "CONTESTANT":
                    time_to_solve = accepted_sub.get("relativeTimeSeconds")
                else:
                    time_to_solve = None
            else:
                penalty = 0
                time_to_solve = None
                # Last submission details
                last_sub = prob_submissions[-1]
                submitted_at = datetime.fromtimestamp(last_sub.get("creationTimeSeconds", 0))
                verdict = last_sub.get("verdict")
                language = last_sub.get("programmingLanguage")

            # Find or create ProblemAttempt
            attempt = attempts.get(problem.id)

            if not attempt:
                attempt = ProblemAttempt(
                    user_id=user.id,
                    problem_id=problem.id,
                    participation_id=participation_id,
                    solved=solved,
                    attempts=attempts_count,
                    time_to_solve=time_to_solve,
                    penalty=penalty,
                    verdict=verdict[:30] if verdict else None,
                    language=language[:30] if language else None,
                    submitted_at=submitted_at
                )
                db.add(attempt)
            else:
                attempt.participation_id = participation_id
                attempt.solved = solved
                attempt.attempts = attempts_count
                attempt.time_to_solve = time_to_solve
                attempt.penalty = penalty
                attempt.verdict = verdict[:30] if verdict else None
                attempt.language = language[:30] if language else None
                attempt.submitted_at = submitted_at

        db.flush()
        logger.info(f"Number of submissions stored: {submissions_synced}")

        # One grouped query for every contest, including zero-solve contests.
        solved_counts = dict(db.query(
            ProblemAttempt.participation_id, func.count(ProblemAttempt.id)
        ).filter(
            ProblemAttempt.user_id == user.id,
            ProblemAttempt.solved.is_(True),
            ProblemAttempt.time_to_solve.isnot(None),
        ).group_by(ProblemAttempt.participation_id).all())
        for part in participations.values():
            part.problems_solved = solved_counts.get(part.id, 0)

        # Only mark a complete, successful synchronization as fresh.
        user.last_synced_at = datetime.now(timezone.utc)
        synced_at = user.last_synced_at
        db.commit()
        logger.info("Sync completed")

        return {
            "handle": official_handle,
            "contests_synced": contests_synced,
            "submissions_synced": submissions_synced,
            "status": "success",
            "last_synced_at": synced_at
        }

    except CodeforcesException as e:
        db.rollback()
        logger.error(f"Sync failed for handle {handle} (Codeforces error): {e}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Sync failed for handle {handle} (Database/System error): {e}")
        raise
