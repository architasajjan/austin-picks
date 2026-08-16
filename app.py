"""Austin restaurant recommendation app built with Streamlit."""

from __future__ import annotations

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
    .stApp { background: #0f0d0b; color: #f5f0eb; }

    /* hide Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }

    /* main content column — uniform horizontal padding */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* every Streamlit column group gets left/right padding */
    [data-testid="stHorizontalBlock"] {
        padding: 0 64px;
        gap: 20px !important;
    }

    /* ── hero ─────────────────────────────────── */
    .ap-hero {
        background: linear-gradient(135deg, #1a1108 0%, #0f0d0b 60%);
        border-bottom: 1px solid #2a2218;
        padding: 56px 64px 52px;
    }
    .ap-wordmark {
        font-size: 12px;
        font-weight: 700;
        letter-spacing: .2em;
        text-transform: uppercase;
        color: #c9813b;
        margin-bottom: 22px;
    }
    .ap-hero h1 {
        font-size: clamp(40px, 5vw, 68px);
        font-weight: 800;
        line-height: 1.04;
        color: #f5f0eb;
        margin: 0 0 18px;
    }
    .ap-hero p {
        font-size: 17px;
        color: #7a6e63;
        max-width: 480px;
        line-height: 1.65;
        margin: 0;
    }

    /* ── section wrapper ──────────────────────── */
    .ap-section-hdr {
        padding: 44px 64px 28px;
    }
    .ap-section-hdr h2 {
        font-size: 22px;
        font-weight: 700;
        color: #f5f0eb;
        margin: 0 0 5px;
        letter-spacing: -.01em;
    }
    .ap-section-hdr p {
        font-size: 14px;
        color: #5c5249;
        margin: 0;
    }

    /* padding below the cards grid */
    .ap-section-footer { padding: 32px 0; }

    /* ── divider ──────────────────────────────── */
    .ap-divider {
        border: none;
        border-top: 1px solid #1a1612;
        margin: 0;
    }

    /* ── search area ──────────────────────────── */
    .ap-ask-hdr {
        padding: 44px 64px 24px;
    }
    .ap-ask-hdr h2 {
        font-size: 22px;
        font-weight: 700;
        color: #f5f0eb;
        margin: 0 0 5px;
        letter-spacing: -.01em;
    }
    .ap-ask-hdr p {
        font-size: 14px;
        color: #5c5249;
        margin: 0;
    }
    .ap-input-wrap {
        padding: 0 64px 48px;
    }

    /* input field */
    .ap-input-wrap .stTextInput > div > div {
        background: #13110d !important;
        border: 1.5px solid #2a2218 !important;
        border-radius: 10px !important;
    }
    .ap-input-wrap .stTextInput input {
        background: transparent !important;
        color: #f5f0eb !important;
        font-size: 15px !important;
        padding: 14px 18px !important;
        caret-color: #c9813b;
    }
    .ap-input-wrap .stTextInput input:focus {
        outline: none !important;
    }
    .ap-input-wrap .stTextInput > div > div:focus-within {
        border-color: #c9813b !important;
        box-shadow: 0 0 0 3px #c9813b14 !important;
    }
    .ap-input-wrap .stTextInput input::placeholder { color: #3d352d !important; }

    /* ── pick badge ───────────────────────────── */
    .ap-badge {
        display: inline-block;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: .15em;
        text-transform: uppercase;
        padding: 3px 9px;
        border-radius: 4px;
        margin-bottom: 12px;
    }
    .badge-overall { background: #c9813b1a; color: #c9813b; border: 1px solid #c9813b33; }
    .badge-brunch  { background: #c96b7a1a; color: #c96b7a; border: 1px solid #c96b7a33; }
    .badge-value   { background: #5da5681a; color: #5da568; border: 1px solid #5da56833; }
    .badge-gem     { background: #7b6ec61a; color: #a099e0; border: 1px solid #7b6ec633; }
    .badge-search  { background: #3b82f61a; color: #7db5f7; border: 1px solid #3b82f633; }

    /* ── place card ───────────────────────────── */
    .ap-card {
        background: #131009;
        border: 1px solid #231f18;
        border-radius: 12px;
        padding: 22px 22px 20px;
        height: 100%;
        box-sizing: border-box;
    }
    .ap-card-name {
        font-size: 17px;
        font-weight: 700;
        color: #f5f0eb;
        margin: 0 0 5px;
        line-height: 1.25;
    }
    .ap-card-meta {
        font-size: 12px;
        color: #5c5249;
        margin-bottom: 12px;
        letter-spacing: .01em;
    }
    .ap-rating-row {
        display: flex;
        align-items: center;
        gap: 7px;
        margin-bottom: 12px;
    }
    .ap-stars  { color: #c9813b; font-size: 13px; letter-spacing: .04em; }
    .ap-rating-num   { font-size: 14px; font-weight: 700; color: #f5f0eb; }
    .ap-rating-count { font-size: 12px; color: #5c5249; }
    .ap-blurb {
        font-size: 13px;
        color: #8a7e73;
        line-height: 1.65;
        margin-bottom: 16px;
    }
    .ap-map-link a {
        display: inline-block;
        font-size: 12px;
        font-weight: 600;
        color: #c9813b;
        text-decoration: none;
        border: 1px solid #c9813b33;
        border-radius: 6px;
        padding: 6px 13px;
    }

    /* ── result sub-header ────────────────────── */
    .ap-result-hdr {
        padding: 28px 64px 20px;
    }
    .ap-result-hdr h3 {
        font-size: 18px;
        font-weight: 700;
        color: #f5f0eb;
        margin: 0 0 4px;
    }
    .ap-result-hdr p {
        font-size: 13px;
        color: #5c5249;
        margin: 0;
    }

    /* ── spinner ──────────────────────────────── */
    .stSpinner > div { border-top-color: #c9813b !important; }

    /* ── alerts ───────────────────────────────── */
    .stAlert { background: #13110d !important; border-color: #231f18 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── helpers ───────────────────────────────────────────────────────────────────

BADGE_CLASS = {
    "Best Overall": "badge-overall",
    "Best Brunch":  "badge-brunch",
    "Best Value":   "badge-value",
    "Hidden Gem":   "badge-gem",
}

STAR_MAP = {5: "★★★★★", 4: "★★★★☆", 3: "★★★☆☆", 2: "★★☆☆☆", 1: "★☆☆☆☆"}


def _stars(rating: float | None) -> str:
    return STAR_MAP.get(round(rating), "★★★★☆") if rating else ""


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

    best_overall = choose(lambda _: True)
    if best_overall:
        roles.append(("Best Overall", best_overall))

    best_brunch = choose(
        lambda p: p.get("category", "").lower() in {"cafe", "coffee shop", "bakery"}
        or any("brunch" in t.lower() for t in p.get("types", []))
    )
    if best_brunch:
        roles.append(("Best Brunch", best_brunch))

    best_value = choose(
        lambda p: p.get("price_level") in {"PRICE_LEVEL_FREE", "PRICE_LEVEL_INEXPENSIVE"}
        or p.get("price_display") in {"Free", "$"}
    )
    if best_value:
        roles.append(("Best Value", best_value))

    hidden_gem = choose(
        lambda p: (p.get("rating") or 0) >= 4.3
        and (p.get("user_rating_count") or 0) < 200
    )
    if hidden_gem:
        roles.append(("Hidden Gem", hidden_gem))

    return roles


def render_place_card(
    place: dict[str, Any],
    *,
    label: str | None = None,
    explanation: str | None = None,
) -> None:
    badge_class = BADGE_CLASS.get(label or "", "badge-search")
    badge_html  = f'<div class="ap-badge {badge_class}">{label}</div>' if label else ""

    name     = place.get("name", "Unnamed place")
    category = place.get("category", "Place")
    price    = place.get("price_display", "$$")
    rating   = place.get("rating")
    count    = place.get("user_rating_count") or 0
    body     = explanation or place.get("editorial_summary") or ""
    maps_uri = place.get("google_maps_uri", "")

    if rating:
        rating_html = f"""
        <div class="ap-rating-row">
            <span class="ap-stars">{_stars(rating)}</span>
            <span class="ap-rating-num">{rating:.1f}</span>
            <span class="ap-rating-count">({count:,} ratings)</span>
        </div>"""
    else:
        rating_html = '<p class="ap-rating-count" style="margin-bottom:12px">Rating unavailable</p>'

    blurb_html = f'<p class="ap-blurb">{body}</p>' if body else ""
    map_html   = f'<div class="ap-map-link"><a href="{maps_uri}" target="_blank">Open in Maps ↗</a></div>' if maps_uri else ""

    st.markdown(
        f"""
        <div class="ap-card">
            {badge_html}
            <div class="ap-card-name">{name}</div>
            <div class="ap-card-meta">{category} &nbsp;·&nbsp; {price}</div>
            {rating_html}
            {blurb_html}
            {map_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── sections ──────────────────────────────────────────────────────────────────

def show_top_picks() -> None:
    st.markdown(
        '<div class="ap-section-hdr">'
        "<h2>Top picks for Austin</h2>"
        "<p>A live shortlist across restaurants, cafes, and bars — scored for quality, confidence, and value.</p>"
        "</div>",
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
                (label, place, blurbs.get(place.get("id", "")))
                for label, place in roles
            ]

    roles   = st.session_state.get("top_pick_roles", [])
    warning = st.session_state.get("top_pick_agent_warning")

    if warning:
        st.info("Top picks are live, but AI explanations are unavailable right now.")

    if not roles:
        st.warning("Couldn't find Austin places right now — try refreshing in a moment.")
        return

    cols = st.columns(len(roles), gap="medium")
    for col, (label, place, blurb) in zip(cols, roles):
        with col:
            render_place_card(place, label=label, explanation=blurb)

    st.markdown('<div class="ap-section-footer"></div>', unsafe_allow_html=True)


def show_agent_search() -> None:
    st.markdown(
        '<div class="ap-ask-hdr">'
        "<h2>Ask the agent</h2>"
        "<p>Tell me what you're in the mood for — I'll find the right Austin shortlist.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="ap-input-wrap">', unsafe_allow_html=True)
    query = st.text_input(
        "What are you looking for?",
        placeholder='e.g. "quiet coffee shop good for working" or "best cheap brunch spot"',
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if not query.strip():
        return

    with st.spinner("Tuning the search to your taste…"):
        try:
            filters = parse_query(query.strip())
        except AgentError:
            filters = {
                "category": "any",
                "price_preference": "any",
                "theme": query.strip(),
                "refined_query": f"{query.strip()}, Austin TX",
            }
            st.info("AI query parsing unavailable — using your request directly.")

        try:
            candidates = [
                enrich_place(p)
                for p in search_with_details(filters["refined_query"], page_size=20)
            ]
        except PlacesApiError as exc:
            st.warning(str(exc))
            return

        candidates = sorted(candidates, key=lambda p: p.get("score", 0), reverse=True)

        if not candidates:
            st.warning("No Austin places matched that — try a different phrase.")
            return

        try:
            explanations = choose_top_recommendations(query.strip(), candidates[:10])
        except AgentError:
            explanations = {}
            st.info("Found live matches, but AI explanations are unavailable right now.")

    results = [p for p in candidates if p.get("id") in explanations][:3] or candidates[:3]

    st.markdown(
        f'<div class="ap-result-hdr">'
        f"<h3>Your Austin shortlist</h3>"
        f'<p>Based on: "{query.strip()}"</p>'
        f"</div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(len(results), gap="medium")
    for col, place in zip(cols, results):
        with col:
            render_place_card(place, explanation=explanations.get(place.get("id")))

    st.markdown('<div class="ap-section-footer"></div>', unsafe_allow_html=True)


def main() -> None:
    # ── hero ──
    st.markdown(
        '<div class="ap-hero">'
        '<div class="ap-wordmark">Austin Picks</div>'
        "<h1>Where Austin<br>eats tonight.</h1>"
        "<p>Live recommendations across restaurants, cafes, and bars —"
        " scored by AI for quality, confidence, and value.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── top picks ──
    try:
        show_top_picks()
    except PlacesApiError as exc:
        st.markdown('<div class="ap-section-hdr">', unsafe_allow_html=True)
        st.warning(str(exc))
        st.info("Once Google Places is connected, your live Austin picks will appear here.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<hr class="ap-divider">', unsafe_allow_html=True)

    # ── agent search ──
    show_agent_search()


if __name__ == "__main__":
    main()
