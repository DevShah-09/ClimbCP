import logging
import requests
import uuid
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.cp_profile import CPProfile
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

        # Step 3: Create or update the user record
        profile = db.query(CPProfile).filter(
            CPProfile.platform == "codeforces",
            func.lower(CPProfile.handle) == handle.lower()
        ).first()

        if profile:
            user = profile.user
            # Update profile details
            profile.handle = official_handle
            profile.current_rating = cf_profile_info.get("rating")
            profile.max_rating = cf_profile_info.get("maxRating")
        else:
            # Check if User with username already exists (case-insensitive)
            user = db.query(User).filter(func.lower(User.username) == handle.lower()).first()
            if not user:
                # Generate unique email placeholder
                email = f"{handle.lower()}@climbcp.com"
                existing_email_user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
                if existing_email_user:
                    email = f"{handle.lower()}-{uuid.uuid4().hex[:8]}@climbcp.com"

                user = User(
                    username=official_handle,
                    email=email,
                    hashed_password="pbkdf2:sha256:dummy_password_for_synced_user"
                )
                db.add(user)
                db.flush()  # to populate user.id

            # Create CPProfile
            profile = CPProfile(
                user_id=user.id,
                platform="codeforces",
                handle=official_handle,
                current_rating=cf_profile_info.get("rating"),
                max_rating=cf_profile_info.get("maxRating")
            )
            db.add(profile)
            db.flush()

        # Step 4: Fetch rating history
        rating_history = get_user_rating_history(official_handle)

        # Step 5: Store contest participations (avoid duplicate contests & participations)
        contests_synced = 0
        for rating_change in rating_history:
            contest_code = str(rating_change["contestId"])

            # Find or create Contest
            contest = db.query(Contest).filter(
                Contest.platform == "codeforces",
                Contest.contest_code == contest_code
            ).first()

            if not contest:
                rating_time = datetime.fromtimestamp(rating_change["ratingUpdateTimeSeconds"])
                contest = Contest(
                    platform="codeforces",
                    contest_code=contest_code,
                    contest_name=rating_change["contestName"],
                    start_time=rating_time,
                    end_time=rating_time
                )
                db.add(contest)
                db.flush()

            # Find or create ContestParticipation
            participation = db.query(ContestParticipation).filter(
                ContestParticipation.user_id == user.id,
                ContestParticipation.contest_id == contest.id
            ).first()

            rating_change_val = rating_change["newRating"] - rating_change["oldRating"]
            if not participation:
                participation = ContestParticipation(
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
                contests_synced += 1
            else:
                # Update participation stats if they changed
                participation.rank = rating_change["rank"]
                participation.rating_before = rating_change["oldRating"]
                participation.rating_after = rating_change["newRating"]
                participation.rating_change = rating_change_val

        db.flush()
        logger.info(f"Number of contests stored: {contests_synced}")

        # Step 6: Fetch submissions
        submissions = get_user_submissions(official_handle)

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

        for prob_code, prob_submissions in submissions_by_problem.items():
            # Get problem details from the first submission
            sample_sub = prob_submissions[0]
            prob_info = sample_sub["problem"]
            contest_id = prob_info["contestId"]
            index = prob_info["index"]
            title = prob_info.get("name", "Unknown")
            difficulty = prob_info.get("rating")
            tags = prob_info.get("tags", [])

            # Find or create Problem
            problem = db.query(Problem).filter(
                Problem.platform == "codeforces",
                Problem.problem_code == prob_code
            ).first()

            if not problem:
                problem = Problem(
                    platform="codeforces",
                    problem_code=prob_code,
                    title=title,
                    difficulty=difficulty
                )

                # Associate topics
                for tag in tags:
                    mapped_topic_name = TAG_TO_TOPIC_MAP.get(tag.lower())
                    if mapped_topic_name:
                        topic_obj = topic_name_map.get(mapped_topic_name.lower())
                        if topic_obj:
                            problem.topics.append(topic_obj)

                db.add(problem)
                db.flush()
            else:
                # Update difficulty/title if needed
                if difficulty is not None:
                    problem.difficulty = difficulty
                problem.title = title

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
                contest_obj = db.query(Contest).filter(
                    Contest.platform == "codeforces",
                    Contest.contest_code == contest_code_str
                ).first()
                if contest_obj:
                    part_obj = db.query(ContestParticipation).filter(
                        ContestParticipation.user_id == user.id,
                        ContestParticipation.contest_id == contest_obj.id
                    ).first()
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
            attempt = db.query(ProblemAttempt).filter(
                ProblemAttempt.user_id == user.id,
                ProblemAttempt.problem_id == problem.id
            ).first()

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
                attempt.participation_id = participation_id or attempt.participation_id
                attempt.solved = solved
                attempt.attempts = attempts_count
                attempt.time_to_solve = time_to_solve
                attempt.penalty = penalty
                attempt.verdict = verdict[:30] if verdict else None
                attempt.language = language[:30] if language else None
                attempt.submitted_at = submitted_at

        db.flush()
        logger.info(f"Number of submissions stored: {submissions_synced}")

        # Update problems_solved count for all the user's contest participations
        user_participations = db.query(ContestParticipation).filter(
            ContestParticipation.user_id == user.id
        ).all()

        for part in user_participations:
            solved_count = db.query(ProblemAttempt).filter(
                ProblemAttempt.user_id == user.id,
                ProblemAttempt.participation_id == part.id,
                ProblemAttempt.solved == True
            ).count()
            part.problems_solved = solved_count

        db.commit()
        logger.info("Sync completed")

        return {
            "handle": official_handle,
            "contests_synced": contests_synced,
            "submissions_synced": submissions_synced,
            "status": "success"
        }

    except CodeforcesException as e:
        db.rollback()
        logger.error(f"Sync failed for handle {handle} (Codeforces error): {e}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Sync failed for handle {handle} (Database/System error): {e}")
        raise
