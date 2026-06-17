"""
Prompt Builder — Phase 4

Constructs structured, data-grounded prompts for each AI coaching feature.
All prompts inject real user statistics as JSON context to prevent hallucination.

Functions:
  build_contest_review_prompt(context)   → (system_prompt, user_prompt)
  build_rating_loss_prompt(context)      → (system_prompt, user_prompt)
  build_bottleneck_prompt(context)       → (system_prompt, user_prompt)
"""

import json
import logging

logger = logging.getLogger("prompt_builder")

# ── Shared system role ─────────────────────────────────────────────────────────

_COACH_SYSTEM_PROMPT = """You are an expert competitive programming coach with 10+ years of experience \
mentoring contestants on Codeforces, AtCoder, and IOI.

Your role is to provide highly personalised, data-driven coaching insights based strictly on the \
analytics data provided. Your advice must:
- Reference specific numbers from the data (ratings, mastery scores, attempt counts, etc.)
- Be actionable and concrete, not generic
- Explain the "why" behind each recommendation
- Sound like advice from a knowledgeable human coach, not a statistics dashboard

CRITICAL RULES:
1. Base all advice STRICTLY on the provided JSON data. Do not invent statistics.
2. Always respond with a single valid JSON object. No markdown, no explanation outside the JSON.
3. Do not include <think> blocks or chain-of-thought in your final response.
4. Every list item must be a complete, useful sentence — not a single word.
"""

# ── Feature 1: Contest Review Prompt ──────────────────────────────────────────

_CONTEST_REVIEW_USER_TEMPLATE = """
A competitive programmer just completed a Codeforces contest. Analyse their performance and \
generate a personalised coaching report.

=== CONTEST DATA ===
{context_json}

=== YOUR TASK ===
Generate a JSON object with EXACTLY these keys:
{{
  "summary": "<2-3 sentence overall performance summary referencing rank, rating change, and problems solved>",
  "strengths": ["<strength 1>", "<strength 2>", ...],
  "weaknesses": ["<weakness 1>", "<weakness 2>", ...],
  "missed_opportunities": ["<opportunity 1>", "<opportunity 2>", ...],
  "action_plan": ["<specific action 1>", "<specific action 2>", "<specific action 3>", ...]
}}

Rules:
- "summary": Must mention rank #{rank}, rating change of {rating_change_sign}{rating_change}, \
and reference at least one topic from the data.
- "strengths": 2-4 items. Only mention strengths that are evidenced by the data.
- "weaknesses": 2-4 items. Only mention weaknesses evidenced by failed attempts or low mastery scores.
- "missed_opportunities": 1-3 items. Problems or time management issues visible in the data.
- "action_plan": 3-5 concrete steps. Each must include a specific problem count, rating range, or topic name.
- Respond with ONLY the JSON object. Nothing else.
"""


def build_contest_review_prompt(context: dict) -> tuple[str, str]:
    """
    Build system + user prompts for contest review.

    Expected context keys:
      handle, contest_name, contest_code, rank, rating_before, rating_after,
      rating_change, problems_solved, problems_attempted, topic_masteries,
      weak_topics, strong_topics, contest_attempts (list of attempt dicts)
    """
    logger.info(f"Building contest review prompt for {context.get('handle')} — {context.get('contest_name')}")

    rating_change = context.get("rating_change", 0) or 0
    rating_change_sign = "+" if rating_change >= 0 else ""
    context_json = json.dumps(context, indent=2, default=str)

    user_prompt = _CONTEST_REVIEW_USER_TEMPLATE.format(
        context_json=context_json,
        rank=context.get("rank", "N/A"),
        rating_change=abs(rating_change),
        rating_change_sign=rating_change_sign,
    )

    return _COACH_SYSTEM_PROMPT, user_prompt


# ── Feature 2: Rating Loss Explanation Prompt ─────────────────────────────────

_RATING_LOSS_USER_TEMPLATE = """
A competitive programmer's rating has changed recently. Analyse the data and explain \
what is causing their rating stagnation or decline.

=== USER ANALYTICS DATA ===
{context_json}

=== YOUR TASK ===
Generate a JSON object with EXACTLY these keys:
{{
  "explanation": "<3-4 sentence paragraph explaining the rating trend, referencing specific data points>",
  "major_causes": ["<cause 1 with specific data>", "<cause 2 with specific data>", ...],
  "recommended_actions": ["<concrete action 1>", "<concrete action 2>", ...]
}}

Rules:
- "explanation": Must mention the net rating change of {net_rating_change_sign}{net_rating_change} \
and reference at least 2 specific statistics from the data.
- "major_causes": 2-5 items, each explaining one root cause backed by data numbers.
  Examples of GOOD causes: "Graph mastery score of 52 with 38% failed attempts in graph problems"
  Examples of BAD causes: "Need to practice more" (too generic, no data reference)
- "recommended_actions": 3-5 concrete, measurable actions.
  Examples of GOOD actions: "Solve 15 shortest path problems rated 1400-1700 over the next 2 weeks"
  Examples of BAD actions: "Practice graphs" (not specific enough)
- Respond with ONLY the JSON object. Nothing else.
"""


def build_rating_loss_prompt(context: dict) -> tuple[str, str]:
    """
    Build system + user prompts for rating loss explanation.

    Expected context keys:
      handle, current_rating, max_rating, net_rating_change (over recent contests),
      recent_contests (list of {contest_name, rating_change, rank, problems_solved}),
      topic_masteries, weak_topics, strong_topics,
      total_submissions, acceptance_rate, avg_submissions_per_day,
      contest_count, rating_increases, rating_decreases
    """
    logger.info(f"Building rating loss prompt for {context.get('handle')}")

    net_change = context.get("net_rating_change", 0) or 0
    sign = "+" if net_change >= 0 else ""
    context_json = json.dumps(context, indent=2, default=str)

    user_prompt = _RATING_LOSS_USER_TEMPLATE.format(
        context_json=context_json,
        net_rating_change=abs(net_change),
        net_rating_change_sign=sign,
    )

    return _COACH_SYSTEM_PROMPT, user_prompt


# ── Feature 3: Bottleneck Analysis Prompt ─────────────────────────────────────

_BOTTLENECK_USER_TEMPLATE = """
A competitive programmer wants to understand what is preventing their rating from growing. \
Analyse the pre-computed bottleneck scores below and generate a coaching analysis.

=== PRE-SCORED BOTTLENECK DATA ===
{context_json}

The "pre_scored_bottlenecks" are algorithmic scores (0-100) computed from raw database statistics.
Higher score = bigger obstacle to rating growth.

=== YOUR TASK ===
Generate a JSON object with EXACTLY these keys:
{{
  "bottlenecks": [
    {{
      "factor": "<bottleneck name>",
      "impact": <integer 0-100>,
      "description": "<one sentence explaining WHY this is a bottleneck, referencing data>"
    }},
    ...
  ],
  "narrative": "<paragraph of 3-5 sentences connecting the bottlenecks into a coherent coaching story>"
}}

Rules:
- Include ALL factors from pre_scored_bottlenecks in your response.
- You may adjust impact scores slightly (±5) if the narrative context justifies it, \
but keep them close to the pre-computed values.
- Each description must reference the specific data that produced that score.
- "narrative" should read like advice from a coach, not a list. Mention the top 2-3 bottlenecks \
by name and explain the path forward.
- Sort "bottlenecks" by impact descending.
- Respond with ONLY the JSON object. Nothing else.
"""


def build_bottleneck_prompt(context: dict) -> tuple[str, str]:
    """
    Build system + user prompts for bottleneck analysis.

    Expected context keys:
      handle, current_rating, pre_scored_bottlenecks (list of {factor, impact, raw_data}),
      topic_masteries, weak_topics, acceptance_rate, contest_count,
      avg_submissions_per_day, avg_solved_per_week
    """
    logger.info(f"Building bottleneck prompt for {context.get('handle')}")

    context_json = json.dumps(context, indent=2, default=str)

    user_prompt = _BOTTLENECK_USER_TEMPLATE.format(context_json=context_json)

    return _COACH_SYSTEM_PROMPT, user_prompt
