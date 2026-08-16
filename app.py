"""Austin restaurant recommendation app built with Streamlit."""

from __future__ import annotations

import html as _html
from typing import Any

import streamlit as st

from agent import AgentError, choose_top_recommendations, generate_place_blurbs, parse_query
from places_client import PlacesApiError, search_with_details
from scoring import enrich_place


st.set_page_config(
    page_title="Austin Picks",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── theme ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #f7f4ef; color: #1a1714; }

    #MainMenu, footer, header { visibility: hidden; }

    .block-container { padding: 0 !important; max-width: 100% !important; }

    [data-testid="stHorizontalBlock"] {
        padding: 0 56px;
        gap: 16px !important;
        align-items: stretch !important;
        margin-bottom: 0 !important;
    }

    /* strip Streamlit's default element spacing so sections butt together cleanly */
    [data-testid="stVerticalBlock"] > [data-testid="element-container"] {
        margin-bottom: 0 !important;
    }
    [data-testid="stVerticalBlock"] > div:has([data-testid="stHorizontalBlock"]) {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }

    /* ── hero ── */
    .ap-hero {
        background: linear-gradient(120deg, #fff8ef 0%, #f0ece6 100%);
        border-bottom: 1px solid #e8e2d9;
        padding: 48px 56px 44px;
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: 32px;
    }
    .ap-hero-left {}
    .ap-wordmark {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: .2em;
        text-transform: uppercase;
        color: #c9813b;
        margin-bottom: 14px;
    }
    .ap-hero h1 {
        font-size: clamp(36px, 4.5vw, 58px);
        font-weight: 800;
        line-height: 1.06;
        color: #1a1714;
        margin: 0 0 12px;
    }
    .ap-hero p {
        font-size: 16px;
        color: #8a7e73;
        max-width: 420px;
        line-height: 1.6;
        margin: 0;
    }

    /* ── section header ── */
    .ap-hdr {
        padding: 36px 56px 20px;
    }
    .ap-hdr h2 {
        font-size: 20px;
        font-weight: 700;
        color: #1a1714;
        margin: 0 0 4px;
        letter-spacing: -.01em;
    }
    .ap-hdr p {
        font-size: 13px;
        color: #a09689;
        margin: 0;
    }

    /* ── divider ── */
    .ap-divider { border: none; border-top: 1px solid #e8e2d9; margin: 0; }

    /* ── pick cards ── */
    .ap-card {
        background: #fff;
        border-radius: 14px;
        padding: 20px 20px 18px;
        height: 100%;
        box-sizing: border-box;
        box-shadow: 0 1px 3px rgba(0,0,0,.06), 0 4px 12px rgba(0,0,0,.04);
        border-top: 4px solid var(--card-color, #c9813b);
    }
    .ap-badge {
        display: inline-block;
        font-size: 9px;
        font-weight: 700;
        letter-spacing: .16em;
        text-transform: uppercase;
        padding: 3px 8px;
        border-radius: 4px;
        margin-bottom: 10px;
        color: var(--card-color, #c9813b);
        background: var(--card-color-bg, #fff8ef);
    }
    .ap-card-name {
        font-size: 16px;
        font-weight: 700;
        color: #1a1714;
        margin: 0 0 4px;
        line-height: 1.25;
    }
    .ap-card-meta {
        font-size: 12px;
        color: #b0a496;
        margin-bottom: 10px;
    }
    .ap-rating-row {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 10px;
    }
    .ap-stars { font-size: 12px; color: var(--card-color, #c9813b); }
    .ap-rating-num   { font-size: 13px; font-weight: 700; color: #1a1714; }
    .ap-rating-count { font-size: 11px; color: #b0a496; }
    .ap-blurb {
        font-size: 13px;
        color: #6b6259;
        line-height: 1.6;
        margin-bottom: 14px;
    }
    .ap-map-link a {
        font-size: 12px;
        font-weight: 600;
        color: var(--card-color, #c9813b);
        text-decoration: none;
        border: 1.5px solid var(--card-color, #c9813b);
        border-radius: 6px;
        padding: 5px 12px;
        opacity: .85;
    }

    /* card colour tokens */
    .card-overall { --card-color:#d97706; --card-color-bg:#fef9ee; }
    .card-brunch  { --card-color:#e11d48; --card-color-bg:#fff1f4; }
    .card-value   { --card-color:#059669; --card-color-bg:#f0fdf8; }
    .card-gem     { --card-color:#7c3aed; --card-color-bg:#f5f3ff; }
    .card-search  { --card-color:#2563eb; --card-color-bg:#eff6ff; }

    /* ── agent section ── */
    .ap-ask {
        padding: 28px 56px 32px;
        background: #fff;
        border-top: 1px solid #e8e2d9;
    }
    .ap-ask h2 { font-size: 17px; font-weight: 700; color: #1a1714; margin: 0 0 12px; }

    /* input — capped width so it doesn't span the full screen */
    .ap-ask .stTextInput {
        max-width: 480px !important;
    }
    .ap-ask .stTextInput > div > div {
        background: #f7f4ef !important;
        border: 1.5px solid #e2dcd5 !important;
        border-radius: 10px !important;
    }
    .ap-ask .stTextInput input {
        background: transparent !important;
        color: #1a1714 !important;
        font-size: 14px !important;
        padding: 11px 16px !important;
    }
    .ap-ask .stTextInput > div > div:focus-within {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px #2563eb12 !important;
    }
    .ap-ask .stTextInput input::placeholder { color: #c4bdb5 !important; }

    /* result sub-label */
    .ap-result-label {
        font-size: 12px;
        font-weight: 600;
        color: #a09689;
        letter-spacing: .06em;
        text-transform: uppercase;
        padding: 16px 0 10px;
    }

    /* columns padding inside ask section */
    .ap-ask [data-testid="stHorizontalBlock"] { padding: 0 !important; }

    /* spinner + alerts */
    .stSpinner > div { border-top-color: #2563eb !important; }
    .stAlert { background: #fff !important; border-color: #e8e2d9 !important; color: #1a1714 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── constants ─────────────────────────────────────────────────────────────────

CARD_CLASS = {
    "Best Overall": "card-overall",
    "Best Brunch":  "card-brunch",
    "Best Value":   "card-value",
    "Hidden Gem":   "card-gem",
}
STAR_MAP = {5: "★★★★★", 4: "★★★★☆", 3: "★★★☆☆", 2: "★★☆☆☆", 1: "★☆☆☆☆"}


def _e(s: Any) -> str:
    """HTML-escape any dynamic content so tags never bleed into the template."""
    return _html.escape(str(s)) if s else ""


def _stars(rating: float | None) -> str:
    return STAR_MAP.get(round(rating), "★★★★☆") if rating else ""


# ── data helpers ──────────────────────────────────────────────────────────────

def load_top_pick_candidates() -> list[dict[str, Any]]:
    queries = [
        ("Restaurant", "best restaurants in Austin TX"),
        ("Cafe",       "best cafes and brunch in Austin TX"),
        ("Bar",        "best bars in Austin TX"),
    ]
    places_by_id: dict[str, dict[str, Any]] = {}
    for category, query in queries:
        for place in search_with_details(query, category_hint=category):
            if place.get("id"):
                places_by_id[place["id"]] = enrich_place(place)
    return list(places_by_id.values())


def select_top_pick_roles(places: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    if not places:
        return []
    used: set[str] = set()

    def choose(predicate, fallback=True):
        pool = [p for p in places if p.get("id") not in used and predicate(p)]
        if not pool and fallback:
            pool = [p for p in places if p.get("id") not in used]
        if not pool:
            return None
        best = max(pool, key=lambda p: p.get("score", 0))
        used.add(best.get("id", ""))
        return best

    roles: list[tuple[str, dict[str, Any]]] = []
    if (p := choose(lambda _: True)):
        roles.append(("Best Overall", p))
    if (p := choose(
        lambda p: p.get("category", "").lower() in {"cafe", "coffee shop", "bakery"}
        or any("brunch" in t.lower() for t in p.get("types", []))
    )):
        roles.append(("Best Brunch", p))
    if (p := choose(
        lambda p: p.get("price_level") in {"PRICE_LEVEL_FREE", "PRICE_LEVEL_INEXPENSIVE"}
        or p.get("price_display") in {"Free", "$"}
    )):
        roles.append(("Best Value", p))
    if (p := choose(
        lambda p: (p.get("rating") or 0) >= 4.3 and (p.get("user_rating_count") or 0) < 200
    )):
        roles.append(("Hidden Gem", p))
    return roles


# ── card renderer ─────────────────────────────────────────────────────────────

def render_place_card(
    place: dict[str, Any],
    *,
    label: str | None = None,
    explanation: str | None = None,
) -> None:
    card_class = CARD_CLASS.get(label or "", "card-search")

    name     = _e(place.get("name", "Unnamed place"))
    category = _e(place.get("category", "Place"))
    price    = _e(place.get("price_display", "$$"))
    rating   = place.get("rating")
    count    = place.get("user_rating_count") or 0
    body     = _e(explanation or place.get("editorial_summary") or "")
    maps_uri = _e(place.get("google_maps_uri", ""))
    label_e  = _e(label) if label else ""

    badge_html = f'<div class="ap-badge">{label_e}</div>' if label_e else ""

    if rating:
        rating_html = (
            f'<div class="ap-rating-row">'
            f'<span class="ap-stars">{_stars(rating)}</span>'
            f'<span class="ap-rating-num">{rating:.1f}</span>'
            f'<span class="ap-rating-count">({count:,} ratings)</span>'
            f"</div>"
        )
    else:
        rating_html = '<p class="ap-rating-count" style="margin-bottom:10px">Rating unavailable</p>'

    blurb_html = f'<p class="ap-blurb">{body}</p>' if body else ""
    map_html   = (
        f'<div class="ap-map-link"><a href="{maps_uri}" target="_blank">Open in Maps ↗</a></div>'
        if maps_uri else ""
    )

    st.markdown(
        f'<div class="ap-card {card_class}">'
        f"{badge_html}"
        f'<div class="ap-card-name">{name}</div>'
        f'<div class="ap-card-meta">{category} · {price}</div>'
        f"{rating_html}"
        f"{blurb_html}"
        f"{map_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


# ── sections ──────────────────────────────────────────────────────────────────

def show_top_picks() -> None:
    st.markdown(
        '<div class="ap-hdr"><h2>Top picks for Austin</h2>'
        "<p>Live shortlist across restaurants, cafes, and bars — scored for quality, confidence, and value.</p></div>",
        unsafe_allow_html=True,
    )

    if "top_pick_roles" not in st.session_state:
        with st.spinner("Finding Austin's standouts…"):
            candidates = load_top_pick_candidates()
            roles      = select_top_pick_roles(candidates)
            places     = [p for _, p in roles]
            try:
                blurbs = generate_place_blurbs(places)
            except AgentError as exc:
                st.session_state["top_pick_agent_warning"] = str(exc)
                blurbs = {}
            st.session_state["top_pick_roles"] = [
                (lbl, place, blurbs.get(place.get("id", "")))
                for lbl, place in roles
            ]

    roles   = st.session_state.get("top_pick_roles", [])
    warning = st.session_state.get("top_pick_agent_warning")
    if warning:
        st.info("Top picks loaded — AI explanations unavailable right now.")
    if not roles:
        st.warning("Couldn't find Austin places right now — try refreshing.")
        return

    cols = st.columns(len(roles), gap="medium")
    for col, (lbl, place, blurb) in zip(cols, roles):
        with col:
            render_place_card(place, label=lbl, explanation=blurb)


def show_agent_search() -> None:
    st.markdown('<div class="ap-ask">', unsafe_allow_html=True)
    st.markdown("<h2>Ask the agent</h2>", unsafe_allow_html=True)

    query = st.text_input(
        "search",
        placeholder='e.g. "quiet coffee shop for working" or "cheap brunch with outdoor seating"',
        label_visibility="collapsed",
    )

    if query.strip():
        with st.spinner("Finding your shortlist…"):
            try:
                filters = parse_query(query.strip())
            except AgentError as exc:
                filters = {"refined_query": f"{query.strip()}, Austin TX"}
                st.warning(f"AI agent error: {exc}")

            try:
                candidates = [
                    enrich_place(p)
                    for p in search_with_details(filters["refined_query"], page_size=20)
                ]
            except PlacesApiError as exc:
                st.warning(str(exc))
                st.markdown("</div>", unsafe_allow_html=True)
                return

            candidates = sorted(candidates, key=lambda p: p.get("score", 0), reverse=True)
            if not candidates:
                st.warning("No matches — try a different phrase.")
                st.markdown("</div>", unsafe_allow_html=True)
                return

            try:
                explanations = choose_top_recommendations(query.strip(), candidates[:10])
            except AgentError:
                explanations = {}

        results = [p for p in candidates if p.get("id") in explanations][:3] or candidates[:3]

        st.markdown(
            f'<div class="ap-result-label">Your shortlist for "{_e(query.strip())}"</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(len(results), gap="medium")
        for col, place in zip(cols, results):
            with col:
                render_place_card(place, explanation=explanations.get(place.get("id")))

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.markdown(
        '<div class="ap-hero">'
        '<div class="ap-hero-left">'
        '<div class="ap-wordmark">Austin Picks</div>'
        "<h1>Where Austin<br>eats tonight.</h1>"
        "<p>Live recs across restaurants, cafes, and bars —"
        " scored by AI for quality, confidence, and value.</p>"
        "</div></div>",
        unsafe_allow_html=True,
    )

    try:
        show_top_picks()
    except PlacesApiError as exc:
        st.markdown('<div class="ap-hdr">', unsafe_allow_html=True)
        st.warning(str(exc))
        st.info("Once Google Places is connected, your live Austin picks will appear here.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<hr class="ap-divider">', unsafe_allow_html=True)
    show_agent_search()


if __name__ == "__main__":
    main()
