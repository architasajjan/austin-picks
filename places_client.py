"""Google Places API (New) client for live Austin recommendations."""

from __future__ import annotations

import os
from typing import Any

import requests


PLACES_BASE_URL = "https://places.googleapis.com/v1"
SEARCH_URL = f"{PLACES_BASE_URL}/places:searchText"
DETAILS_FIELDS = (
    "id,displayName,formattedAddress,rating,userRatingCount,priceLevel,"
    "types,primaryType,primaryTypeDisplayName,googleMapsUri,reviews,"
    "editorialSummary"
)
SEARCH_FIELDS = (
    "places.id,places.displayName,places.formattedAddress,places.rating,"
    "places.userRatingCount,places.priceLevel,places.types,places.primaryType,"
    "places.primaryTypeDisplayName,places.googleMapsUri"
)


class PlacesApiError(RuntimeError):
    """Raised when Google Places cannot return a usable response."""


def _api_key() -> str:
    """Read the Google key at request time so secrets are never hardcoded."""
    key = os.environ.get("GOOGLE_PLACES_API_KEY", "").strip()
    if not key:
        raise PlacesApiError(
            "Google Places is not connected yet. Add GOOGLE_PLACES_API_KEY to continue."
        )
    return key


def _headers(field_mask: str) -> dict[str, str]:
    """Build the headers required by Places API (New)."""
    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": _api_key(),
        "X-Goog-FieldMask": field_mask,
    }


def _normalize_place(raw: dict[str, Any], category_hint: str | None = None) -> dict[str, Any]:
    """Normalize Places API fields into the app's small internal place shape."""
    display_name = raw.get("displayName") or {}
    primary_type_name = raw.get("primaryTypeDisplayName") or {}
    types = raw.get("types") or []
    category = (
        primary_type_name.get("text")
        if isinstance(primary_type_name, dict)
        else None
    ) or category_hint or _category_from_types(types)

    reviews = []
    for review in raw.get("reviews") or []:
        text = (review.get("text") or {}).get("text", "")
        if text:
            reviews.append(text)

    editorial_summary = raw.get("editorialSummary") or {}
    return {
        "id": raw.get("id", ""),
        "name": display_name.get("text", "Unnamed place"),
        "category": _pretty_category(category),
        "address": raw.get("formattedAddress", ""),
        "rating": raw.get("rating"),
        "user_rating_count": raw.get("userRatingCount", 0),
        "price_level": raw.get("priceLevel"),
        "types": types,
        "google_maps_uri": raw.get("googleMapsUri", ""),
        "reviews": reviews[:5],
        "editorial_summary": (editorial_summary.get("text", "") if isinstance(editorial_summary, dict) else ""),
    }


def _category_from_types(types: list[str]) -> str:
    """Infer a human-readable category when Places does not return a label."""
    type_text = " ".join(types).lower()
    if "cafe" in type_text or "coffee" in type_text:
        return "Cafe"
    if "bar" in type_text or "night_club" in type_text:
        return "Bar"
    return "Restaurant"


def _pretty_category(category: str) -> str:
    """Keep Places labels useful and compact in cards."""
    cleaned = category.replace("_", " ").strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else "Restaurant"


def search_places(
    text_query: str,
    *,
    category_hint: str | None = None,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    """Search live places using the Places API Text Search endpoint."""
    payload = {
        "textQuery": text_query,
        "pageSize": page_size,
        "languageCode": "en",
        "regionCode": "US",
        "locationBias": {
            "circle": {
                "center": {"latitude": 30.2672, "longitude": -97.7431},
                "radius": 30000.0,
            }
        },
    }
    try:
        response = requests.post(
            SEARCH_URL,
            headers=_headers(SEARCH_FIELDS),
            json=payload,
            timeout=25,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise PlacesApiError(_friendly_api_error("search", response, exc)) from exc

    data = response.json()
    return [
        _normalize_place(place, category_hint)
        for place in data.get("places", [])
        if place.get("id")
    ]


def get_place_details(place_id: str, *, category_hint: str | None = None) -> dict[str, Any]:
    """Fetch full details, including live review snippets, for one place."""
    if not place_id:
        raise PlacesApiError("Google Places returned a place without an ID.")
    try:
        response = requests.get(
            f"{PLACES_BASE_URL}/places/{place_id}",
            headers=_headers(DETAILS_FIELDS),
            timeout=25,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise PlacesApiError(_friendly_api_error("details", response, exc)) from exc
    return _normalize_place(response.json(), category_hint)


def _friendly_api_error(
    operation: str,
    response: requests.Response | None,
    error: requests.RequestException,
) -> str:
    """Turn Google API errors into actionable messages without exposing secrets."""
    status = response.status_code if response is not None else None
    try:
        body = response.json() if response is not None else {}
        message = body.get("error", {}).get("message", "")
    except (ValueError, AttributeError):
        message = ""
    if status == 403 and "not been used" in message.lower():
        return (
            "Google Places is connected, but Places API (New) is disabled for its "
            "Google Cloud project. Enable Places API (New), wait a few minutes, "
            "then refresh this app."
        )
    if status == 403:
        return (
            "Google Places rejected the request. Check that Places API (New) is "
            "enabled and that this key allows requests to places.googleapis.com."
        )
    return f"Google Places {operation} failed. Please try again in a moment."


def search_with_details(
    text_query: str,
    *,
    category_hint: str | None = None,
    detail_limit: int = 8,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    """Search broadly, then enrich the strongest candidates with full details."""
    places = search_places(
        text_query,
        category_hint=category_hint,
        page_size=page_size,
    )
    # Fetch details for the best visible candidates while keeping API usage modest.
    ranked = sorted(
        places,
        key=lambda place: (
            place.get("rating") or 0,
            place.get("user_rating_count") or 0,
        ),
        reverse=True,
    )
    enriched_by_id: dict[str, dict[str, Any]] = {}
    for place in ranked[:detail_limit]:
        try:
            enriched_by_id[place["id"]] = get_place_details(
                place["id"],
                category_hint=category_hint,
            )
        except PlacesApiError:
            # Keep the search result if an individual details request fails.
            enriched_by_id[place["id"]] = place
    return [enriched_by_id.get(place["id"], place) for place in places]