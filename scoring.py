"""Scoring helpers for Austin place recommendations."""

from __future__ import annotations

import math
from typing import Any


PRICE_LEVEL_VALUES = {
    "PRICE_LEVEL_FREE": 0,
    "PRICE_LEVEL_INEXPENSIVE": 1,
    "PRICE_LEVEL_MODERATE": 2,
    "PRICE_LEVEL_EXPENSIVE": 3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 4,
    "FREE": 0,
    "INEXPENSIVE": 1,
    "MODERATE": 2,
    "EXPENSIVE": 3,
    "VERY_EXPENSIVE": 4,
}


def price_level_number(price_level: Any) -> int:
    """Convert a Places price-level enum or number to a 0-4 value."""
    if price_level is None:
        return 2
    if isinstance(price_level, (int, float)):
        return max(0, min(4, int(price_level)))
    return PRICE_LEVEL_VALUES.get(str(price_level).upper(), 2)


def price_symbols(price_level: Any) -> str:
    """Return a friendly dollar-symbol representation for a price level."""
    value = price_level_number(price_level)
    return "Free" if value == 0 else "$" * value


def calculate_score(
    rating: float | None,
    user_rating_count: int | None,
    price_level: Any,
) -> float:
    """Calculate the requested 0-1 recommendation score.

    The score combines normalized rating, logarithmically scaled review volume,
    and affordability. Missing price levels are treated as moderate.
    """
    normalized_rating = max(0.0, min(1.0, (rating or 0.0) / 5.0))
    review_count = max(0, user_rating_count or 0)
    review_volume = min(1.0, math.log10(review_count + 1) / math.log10(1000))
    affordability = (4 - price_level_number(price_level)) / 4
    return round(
        (0.50 * normalized_rating)
        + (0.30 * review_volume)
        + (0.20 * affordability),
        4,
    )


def enrich_place(place: dict[str, Any]) -> dict[str, Any]:
    """Add the computed score and display price to a place record."""
    enriched = dict(place)
    enriched["score"] = calculate_score(
        place.get("rating"),
        place.get("user_rating_count"),
        place.get("price_level"),
    )
    enriched["price_display"] = price_symbols(place.get("price_level"))
    return enriched