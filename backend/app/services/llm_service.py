"""
LLM Service — Phase 4

Central abstraction layer for LLM providers.
Provider is selected via LLM_PROVIDER environment variable.

Supported providers:
  openrouter  — OpenRouter API (uses openai SDK, different base URL)
  openai      — OpenAI API directly
  gemini      — Google Gemini API
  ollama      — Local Ollama server

All public functions are synchronous to match the rest of the codebase.
They accept a system prompt + user prompt and return the raw text response.
"""

import logging
import os
import json
from typing import Optional

logger = logging.getLogger("llm_service")

# ── Configuration (loaded lazily to avoid import-time env reads) ───────────────

def _get_config() -> dict:
    return {
        "provider":           os.getenv("LLM_PROVIDER", "openrouter").lower(),
        "model":              os.getenv("LLM_MODEL", "qwen/qwen3-32b"),
        "openrouter_key":     os.getenv("OPENROUTER_API_KEY", ""),
        "openrouter_base":    os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        "openai_key":         os.getenv("OPENAI_API_KEY", ""),
        "gemini_key":         os.getenv("GEMINI_API_KEY", ""),
        "ollama_base":        os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "ollama_model":       os.getenv("OLLAMA_MODEL", "llama3"),
    }


# ── Internal Providers ─────────────────────────────────────────────────────────

def _call_openai_compatible(
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    base_url: str,
    model: str,
    timeout: int = 90,
) -> str:
    """Call any OpenAI-compatible endpoint (OpenAI or OpenRouter)."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError(
            "The 'openai' package is not installed. Run: pip install openai>=1.30.0"
        )

    if not api_key:
        raise RuntimeError("API key not configured. Set OPENROUTER_API_KEY or OPENAI_API_KEY in .env")

    client = OpenAI(api_key=api_key, base_url=base_url)
    logger.info(f"Sending request to {base_url} with model={model}")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=2048,
        timeout=timeout,
        extra_headers={
            "HTTP-Referer": "https://climbcp.dev",
            "X-Title": "ClimbCP AI Coach",
        } if "openrouter" in base_url else {},
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("LLM returned an empty response.")
    return content.strip()


def _call_gemini(system_prompt: str, user_prompt: str, api_key: str, model: str) -> str:
    """Call Google Gemini API."""
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError(
            "The 'google-generativeai' package is not installed. "
            "Run: pip install google-generativeai>=0.7.0"
        )

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not configured in .env")

    genai.configure(api_key=api_key)
    model_obj = genai.GenerativeModel(
        model_name=model or "gemini-1.5-flash",
        system_instruction=system_prompt,
    )
    response = model_obj.generate_content(user_prompt)
    return response.text.strip()


def _call_ollama(system_prompt: str, user_prompt: str, base_url: str, model: str) -> str:
    """Call local Ollama server."""
    try:
        import httpx
    except ImportError:
        raise RuntimeError(
            "The 'httpx' package is not installed. Run: pip install httpx>=0.27.0"
        )

    url = f"{base_url.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "stream": False,
    }
    try:
        resp = httpx.post(url, json=payload, timeout=120)
        resp.raise_for_status()
    except httpx.ConnectError:
        raise RuntimeError(
            f"Cannot connect to Ollama at {base_url}. "
            "Make sure the Ollama server is running."
        )
    except httpx.TimeoutException:
        raise RuntimeError("Ollama request timed out after 120 seconds.")

    data = resp.json()
    return data["message"]["content"].strip()


# ── Public Interface ───────────────────────────────────────────────────────────

def _dispatch(system_prompt: str, user_prompt: str) -> str:
    """Route to the configured LLM provider and return raw text response."""
    cfg = _get_config()
    provider = cfg["provider"]
    model = cfg["model"]

    logger.info(f"LLM dispatch — provider={provider}, model={model}")

    try:
        if provider == "openrouter":
            return _call_openai_compatible(
                system_prompt, user_prompt,
                api_key=cfg["openrouter_key"],
                base_url=cfg["openrouter_base"],
                model=model,
            )
        elif provider == "openai":
            return _call_openai_compatible(
                system_prompt, user_prompt,
                api_key=cfg["openai_key"],
                base_url="https://api.openai.com/v1",
                model=model or "gpt-4o-mini",
            )
        elif provider == "gemini":
            return _call_gemini(
                system_prompt, user_prompt,
                api_key=cfg["gemini_key"],
                model=model or "gemini-1.5-flash",
            )
        elif provider == "ollama":
            return _call_ollama(
                system_prompt, user_prompt,
                base_url=cfg["ollama_base"],
                model=cfg["ollama_model"],
            )
        else:
            raise RuntimeError(
                f"Unknown LLM provider '{provider}'. "
                "Valid options: openrouter, openai, gemini, ollama"
            )
    except RuntimeError:
        raise
    except Exception as exc:
        logger.exception(f"Unexpected LLM error from provider={provider}")
        raise RuntimeError(f"LLM call failed: {exc}") from exc


def _parse_json_response(raw: str, required_keys: list[str]) -> dict:
    """
    Extract and parse a JSON object from the LLM response.
    Handles markdown code fences (```json ... ```) gracefully.
    Validates that all required_keys are present.
    """
    text = raw.strip()

    # Strip markdown fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first line (```json or ```) and last line (```)
        inner_lines = []
        in_block = False
        for line in lines:
            if line.startswith("```") and not in_block:
                in_block = True
                continue
            if line.startswith("```") and in_block:
                break
            if in_block:
                inner_lines.append(line)
        text = "\n".join(inner_lines).strip()

    # Also handle <think>...</think> blocks that Qwen 3 may emit
    if "<think>" in text:
        think_end = text.rfind("</think>")
        if think_end != -1:
            text = text[think_end + len("</think>"):].strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        # Last resort: find the first { ... } block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                data = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                raise ValueError(
                    f"LLM response is not valid JSON. Raw response (first 400 chars): "
                    f"{raw[:400]}"
                ) from exc
        else:
            raise ValueError(
                f"No JSON object found in LLM response. Raw (first 400 chars): {raw[:400]}"
            ) from exc

    missing = [k for k in required_keys if k not in data]
    if missing:
        raise ValueError(
            f"LLM JSON response missing required keys: {missing}. "
            f"Got keys: {list(data.keys())}"
        )
    return data


# ── Feature-specific wrappers (called by ai_coach_service) ────────────────────

def generate_contest_review(system_prompt: str, user_prompt: str) -> dict:
    """
    Call the LLM for a contest review.
    Returns a dict with keys: summary, strengths, weaknesses, missed_opportunities, action_plan.
    """
    logger.info("LLM: generating contest review")
    raw = _dispatch(system_prompt, user_prompt)
    logger.info("LLM: contest review response received")
    return _parse_json_response(
        raw,
        required_keys=["summary", "strengths", "weaknesses", "missed_opportunities", "action_plan"],
    )


def explain_rating_loss(system_prompt: str, user_prompt: str) -> dict:
    """
    Call the LLM for a rating loss explanation.
    Returns a dict with keys: explanation, major_causes, recommended_actions.
    """
    logger.info("LLM: generating rating loss explanation")
    raw = _dispatch(system_prompt, user_prompt)
    logger.info("LLM: rating loss response received")
    return _parse_json_response(
        raw,
        required_keys=["explanation", "major_causes", "recommended_actions"],
    )


def analyze_bottlenecks(system_prompt: str, user_prompt: str) -> dict:
    """
    Call the LLM for bottleneck analysis.
    Returns a dict with keys: bottlenecks (list of {factor, impact, description}), narrative.
    """
    logger.info("LLM: generating bottleneck analysis")
    raw = _dispatch(system_prompt, user_prompt)
    logger.info("LLM: bottleneck analysis response received")
    return _parse_json_response(
        raw,
        required_keys=["bottlenecks", "narrative"],
    )
