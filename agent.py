"""Gemini helpers for parsing queries and writing recommendation explanations."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import requests


MODEL = "gemini-flash-latest"
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/{MODEL}:generateContent"
)


class AgentError(RuntimeError):
    """Raised when Gemini cannot complete an agent task."""


def _api_key() -> str:
    """Read the Gemini key at request time so secrets are never hardcoded."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise AgentError("Gemini is not connected yet. Add GEMINI_API_KEY to use Ask the Agent.")
    return api_key


def _generate_content(prompt: str) -> str:
    """Call Gemini generateContent and return its text response."""
    try:
        response = requests.post(
            GEMINI_URL,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": _api_key(),
            },
            json={
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "maxOutputTokens": 8192,
                    "temperature": 0.3,
                },
            },
            timeout=45,
        )
        if not response.ok:
            raise AgentError(
                f"Gemini API error {response.status_code}: {response.text[:300]}"
            )
    except requests.RequestException as exc:
        raise AgentError(f"Gemini network error: {exc}") from exc

    try:
        candidates = response.json().get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", [])
        text = next((part.get("text", "") for part in parts if part.get("text")), "")
    except (IndexError, AttributeError, TypeError, ValueError) as exc:
        raise AgentError("Gemini returned an empty response.") from exc
    if not text:
        raise AgentError("Gemini returned an empty response.")
    return text


def _parse_json(text: str) -> dict[str, Any]:
    """Parse JSON even when Gemini wraps it in a markdown fence."""
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.DOTALL)
    if fenced:
        cleaned = fenced.group(1)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AgentError("Gemini returned an unreadable structured response.") from exc
    if not isinstance(parsed, dict):
        raise AgentError("Gemini returned an unexpected structured response.")
    return parsed


def parse_query(query: str) -> dict[str, Any]:
    """Turn a natural-language request into search filters and a refined query."""
    prompt = f"""Parse this Austin restaurant discovery request into JSON only.

Request: {query}

Return exactly these keys:
category (one of restaurant, cafe, bar, or any),
price_preference (one of free, inexpensive, moderate, expensive, or any),
theme (a short phrase or empty string),
refined_query (a concise Google Places search query scoped to Austin, TX).
Do not include markdown or extra keys."""
    try:
        parsed = _parse_json(_generate_content(prompt))
        return {
            "category": parsed.get("category", "any"),
            "price_preference": parsed.get("price_preference", "any"),
            "theme": parsed.get("theme", ""),
            "refined_query": parsed.get("refined_query") or f"{query}, Austin TX",
        }
    except Exception as exc:
        raise AgentError(f"Gemini could not parse that request: {exc}") from exc


def generate_place_blurbs(
    picks: list[dict[str, Any]],
    *,
    context: str = "top picks",
) -> dict[str, str]:
    """Write short, non-quoting explanations based on live review themes."""
    if not picks:
        return {}
    candidate_payload = [
        {
            "id": place.get("id"),
            "name": place.get("name"),
            "category": place.get("category"),
            "rating": place.get("rating"),
            "review_count": place.get("user_rating_count"),
            "review_themes": place.get("reviews", [])[:3],
        }
        for place in picks
    ]
    prompt = f"""You are writing recommendation blurbs for {context} in Austin.
Use the review snippets only to infer themes. Never quote them verbatim and never
claim facts that are not supported. Return JSON only: an object mapping each place
id to one or two warm, specific sentences.

Candidates:
{json.dumps(candidate_payload, ensure_ascii=False)}"""
    try:
        parsed = _parse_json(_generate_content(prompt))
        return {str(key): str(value) for key, value in parsed.items()}
    except Exception as exc:
        raise AgentError(f"Gemini could not write recommendation blurbs: {exc}") from exc


def choose_top_recommendations(
    query: str,
    candidates: list[dict[str, Any]],
) -> dict[str, str]:
    """Ask Gemini to select and explain the best three candidate places."""
    candidate_payload = [
        {
            "id": place.get("id"),
            "name": place.get("name"),
            "category": place.get("category"),
            "rating": place.get("rating"),
            "review_count": place.get("user_rating_count"),
            "price": place.get("price_display"),
            "review_themes": place.get("reviews", [])[:3],
        }
        for place in candidates
    ]
    prompt = f"""Choose the best three places for this Austin request: {query}

Candidates:
{json.dumps(candidate_payload, ensure_ascii=False)}

Return JSON only as an object with a "recommendations" array containing exactly
three objects with "id" and "explanation". Explain each in one or two sentences,
referencing themes from the reviews without quoting any review verbatim."""
    try:
        parsed = _parse_json(_generate_content(prompt))
        recommendations = parsed.get("recommendations", [])
        return {
            str(item.get("id")): str(item.get("explanation"))
            for item in recommendations
            if item.get("id") and item.get("explanation")
        }
    except Exception as exc:
        raise AgentError(f"Gemini could not rank those recommendations: {exc}") from exc