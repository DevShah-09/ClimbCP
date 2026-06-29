"""
Codeforces Problemset Service

Fetches live problems from the CF problemset.problems API for use in
the recommendation engine. NOT used for user analytics (that uses the DB).

Caches the last fetch in memory for 30 minutes to avoid hammering CF.
"""

import logging
import time
import random
import requests
from typing import Optional

logger = logging.getLogger("cf_problemset_service")

# ── In-memory cache ────────────────────────────────────────────────────────────
_CACHE: dict = {
    "problems": [],        # list of raw CF problem dicts
    "fetched_at": 0.0,    # epoch seconds
}
CACHE_TTL = 300            # 5 minutes

CF_PROBLEMSET_URL = "https://codeforces.com/api/problemset.problems"


def _fetch_from_cf() -> list[dict]:
    """
    Call problemset.problems and return the raw list of problem objects.
    Raises RuntimeError on network / API failure.
    """
    try:
        resp = requests.get(CF_PROBLEMSET_URL, timeout=20)
    except requests.exceptions.Timeout:
        raise RuntimeError("Codeforces API timed out fetching the problemset.")
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Codeforces API request failed: {exc}")

    if resp.status_code != 200:
        raise RuntimeError(
            f"Codeforces API returned HTTP {resp.status_code} for problemset.problems"
        )

    try:
        data = resp.json()
    except ValueError:
        raise RuntimeError("Codeforces API returned non-JSON response.")

    if data.get("status") != "OK":
        raise RuntimeError(
            f"Codeforces API error: {data.get('comment', 'unknown')}"
        )

    return data["result"]["problems"]


def get_cf_problems(force_refresh: bool = False) -> list[dict]:
    """
    Return the full CF problemset, using the in-memory cache.
    Each problem dict has at minimum:
        contestId, index, name, rating (may be absent), tags
    """
    now = time.time()
    if force_refresh or not _CACHE["problems"] or (now - _CACHE["fetched_at"]) > CACHE_TTL:
        logger.info("Fetching fresh problemset from Codeforces API…")
        problems = _fetch_from_cf()
        _CACHE["problems"] = problems
        _CACHE["fetched_at"] = now
        logger.info(f"Cached {len(problems)} problems from Codeforces.")
    return _CACHE["problems"]


# ── Tag → local topic name (same map as codeforces_service) ───────────────────
TAG_TO_TOPIC: dict[str, str] = {
    "implementation":         "Implementation",
    "math":                   "Math",
    "greedy":                 "Greedy Algorithms",
    "dp":                     "Dynamic Programming",
    "data structures":        "Data Structures",
    "graphs":                 "Graphs",
    "trees":                  "Trees",
    "binary search":          "Binary Search",
    "two pointers":           "Two Pointers",
    "sortings":               "Sorting",
    "bitmasks":               "Bitmasking",
    "number theory":          "Number Theory",
    "combinatorics":          "Combinatorics",
    "constructive algorithms":"Constructive Algorithms",
    "shortest paths":         "Shortest Paths",
    "strings":                "String Algorithms",
    "flows":                  "Flows & Matchings",
    "geometry":               "Geometry",
}


def _map_tags(tags: list[str]) -> list[str]:
    """Convert CF tags to local topic names; keep only mapped ones."""
    out = []
    seen = set()
    for tag in tags:
        mapped = TAG_TO_TOPIC.get(tag.lower())
        if mapped and mapped not in seen:
            out.append(mapped)
            seen.add(mapped)
    return out


def get_candidate_problems(
    user_rating: int,
    solved_codes: set[str],
    limit: int = 500,
    half_window: int = 200,
) -> list[dict]:
    """
    Return up to `limit` unsolved CF problems near `user_rating`.

    Each returned dict:
        problem_code  str    e.g. "1234A"
        name          str
        rating        int | None
        topics        list[str]   (mapped local names)
        cf_url        str

    Uses progressive window expansion identical to the DB version:
        ±200 → ±400 → ±800 → full range
    """
    all_problems = get_cf_problems()

    for hw in (half_window, half_window * 2, half_window * 4, 1400):
        low  = max(800,  user_rating - hw)
        high = min(3500, user_rating + hw)

        candidates = []
        for p in all_problems:
            rating = p.get("rating")
            if rating is None:
                continue
            if not (low <= rating <= high):
                continue
            contest_id = p.get("contestId")
            index = p.get("index", "")
            if contest_id is None:
                continue
            code = f"{contest_id}{index}"
            if code in solved_codes:
                continue
            candidates.append({
                "problem_code": code,
                "name": p.get("name", "Unknown"),
                "rating": rating,
                "topics": _map_tags(p.get("tags", [])),
                "cf_url": f"https://codeforces.com/problemset/problem/{contest_id}/{index}",
            })

        logger.info(
            f"CF problemset window ±{hw} ({low}–{high}): "
            f"{len(candidates)} unsolved candidates"
        )
        if len(candidates) >= limit:
            break

    random.shuffle(candidates)
    return candidates[:limit]
