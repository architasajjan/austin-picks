# Austin Picks — Product Requirements Document

**Version:** 1.0  
**Status:** Active  
**Owner:** Product  
**Last updated:** August 2026

---

## 1. Executive Summary

Austin Picks is an AI-powered restaurant discovery tool for Austin, Texas. It fetches live venue data from Google Places, scores each place using a proprietary quality-confidence-value formula, and uses Gemini to explain why each pick is the right choice for the user — in plain English. The result is a focused, opinionated shortlist rather than a ranked list of hundreds.

The app solves a specific, recurring frustration: opening Google Maps or Yelp and getting overwhelmed by options, noise, and paid placements. Austin Picks always gives you exactly four automatic top picks (Best Overall, Best Brunch, Best Value, Hidden Gem) and a natural-language search flow that produces a shortlist of three.

---

## 2. Problem Statement

### The core problem
Choosing where to eat in Austin is harder than it should be. The city has thousands of venues across wildly different neighborhoods, price points, and categories. Existing tools — Google Maps, Yelp, TripAdvisor — return long lists sorted by proximity or ad spend. They require the user to do the filtering, reading, and decision-making work themselves.

### Pain points
| Pain point | Who feels it | Frequency |
|---|---|---|
| Too many options, no clear winner | Anyone deciding where to eat | Every meal |
| Sorted by proximity, not quality | Visitors and tourists | High |
| Paid placements dilute trust | Power users | Every session |
| Brunch/value/hidden-gem filters require multiple searches | Casual users | High |
| Natural language searches return raw lists, not ranked explanations | All users | High |

### What Austin Picks is not
- A full restaurant database (Yelp, TripAdvisor)
- A reservations platform (OpenTable, Resy)
- A food-ordering interface (DoorDash, Uber Eats)
- A review platform — it reads reviews to infer themes but never displays or stores them

---

## 3. Target Users

### Primary: The Indecisive Local
**Who:** Austin resident, 25–45, eats out 3–5 times a week  
**Need:** A trusted daily shortlist they don't have to think about  
**Behavior:** Opens the app when they're already hungry and need an answer in under 30 seconds  
**Success signal:** Opens the app → lands on a Top Pick → goes there

### Secondary: The Visiting Professional
**Who:** Business traveler or conference attendee in Austin for 2–4 days  
**Need:** Quality recommendations that locals would actually go to, not tourist traps  
**Behavior:** Searches for specific situations ("client dinner", "quick lunch near downtown")  
**Success signal:** Uses Ask the Agent, gets a shortlist, picks one confidently

### Tertiary: The Discovery-Oriented Explorer
**Who:** Food-curious Austin regular who wants to find spots they've never tried  
**Need:** The Hidden Gem pick and the ability to search for specific vibes  
**Behavior:** Checks the app weekly, uses natural-language queries to explore  
**Success signal:** Finds and visits a Hidden Gem they didn't know

---

## 4. Use Cases

### UC-1: Daily Top Picks (Zero-Input Flow)
**Actor:** Any user  
**Trigger:** Opens the app  
**Flow:**
1. App loads with four automatic picks visible on first scroll
2. Each pick is scored live from Google Places data (rating, review volume, price level)
3. Gemini writes a 1–2 sentence explanation for each, inferring themes from review signals without quoting verbatim
4. User reads the card, taps "Open in Maps", goes

**Why it matters:** Most users don't know what they want beyond a category. Giving them four confident picks with clear rationale removes decision fatigue entirely.

---

### UC-2: Natural-Language Search ("Ask the Agent")
**Actor:** User with a specific situation or vibe in mind  
**Trigger:** Types a query in the search bar  
**Example queries:**
- "quiet coffee shop good for working"  
- "best cheap brunch spot with outdoor seating"  
- "upscale dinner for a first date"  
- "bar with good cocktails and live music"  
- "something near South Congress that's not a chain"

**Flow:**
1. Gemini parses the query into structured filters: `category`, `price_preference`, `theme`, `refined_query`
2. App calls Google Places Text Search with the refined query
3. Results are scored and ranked
4. Gemini selects the top three and writes explanations tailored to the user's original query
5. Three cards are shown — same visual format as the automatic picks

**Why it matters:** Search intent is rich and contextual. A raw keyword search for "brunch" returns hundreds of results. The agent flow interprets intent and returns three confident, explained picks.

---

### UC-3: Discovering Hidden Gems
**Actor:** Austin regular who wants to go somewhere new  
**Trigger:** Sees the Hidden Gem pick on the automatic Top Picks panel  
**Selection criteria:**
- Rating ≥ 4.3 stars
- Review count < 200 (not yet mainstream)
- Scored competitively against the full candidate pool

**Why it matters:** High-rating, low-volume venues are systematically buried in traditional ranking algorithms because they don't have enough reviews to rank highly. Austin Picks surfaces them as a feature, not a footnote.

---

### UC-4: Value-Optimized Decision Making
**Actor:** User on a budget or cost-conscious for a specific meal  
**Trigger:** Sees the Best Value pick  
**Selection criteria:**
- Price level: Free or $ (Inexpensive) in the Google Places price enum
- Scored with 20% affordability weight in the composite formula

**Why it matters:** Price level is a first-class signal that most recommendation apps treat as a filter, not a ranking criterion. Austin Picks makes value a top-level pick category so budget-conscious users don't have to search for it.

---

## 5. Features

### F-1: Automatic Top Picks
- **Best Overall** — highest composite score across all categories
- **Best Brunch** — top scorer among cafes, coffee shops, and brunch-typed venues
- **Best Value** — top scorer among Free or $ price-level venues
- **Hidden Gem** — top scorer with rating ≥ 4.3 and review count < 200

All picks are refreshed per session from live Google Places data. No curation, no editorial bias, no paid placements.

### F-2: AI Explanations
- Each card shows a Gemini-written 1–2 sentence explanation
- Explanations reference inferred review themes (atmosphere, food quality, service) without quoting any review verbatim
- If Gemini is unavailable, cards degrade gracefully to showing the editorial summary from Google Places

### F-3: Scoring Engine
Composite 0–1 score weighted across:
- **50%** — normalized rating (place rating / 5.0)
- **30%** — review volume (log-scaled to 1,000 reviews)
- **20%** — affordability (4 − price_level_index) / 4

This formula rewards places that are genuinely well-rated, trusted by a meaningful number of people, and accessible on price — not just the most-reviewed or closest venue.

### F-4: Ask the Agent Search
- Free-text input parsed by Gemini into structured filters
- Live Google Places Text Search using the refined query
- Results scored, ranked, and top-three selected and explained by Gemini
- Graceful degradation: if Gemini is unavailable, raw query is used directly

### F-5: Google Maps Link
Every card links directly to the Google Maps listing, so users can see photos, hours, and directions without leaving the Austin Picks flow.

---

## 6. Out of Scope (v1)

| Feature | Reason deferred |
|---|---|
| User accounts / saved favorites | Adds auth complexity; solves a stickiness problem, not the core discovery problem |
| Reservations / booking integration | Third-party API dependency; changes the product category |
| Neighborhood or cuisine filters | Adds UI surface area; Ask the Agent handles this via natural language |
| Review display | Avoided intentionally — review text is session-only, never stored or shown |
| Push notifications / daily picks digest | Requires a mobile app or email integration |
| Multiple cities | Austin-specific scoring and query defaults are intentional for v1 focus |

---

## 7. Success Metrics

| Metric | Target | Measurement |
|---|---|---|
| Time-to-pick (load → maps tap) | < 45 seconds | Session timing |
| Ask the Agent query success rate | > 85% return ≥ 1 result | Server-side logging |
| Gemini explanation availability | > 95% uptime during business hours | API error logging |
| Hidden Gem pick quality (rating) | ≥ 4.3 stars on average | Places data audit |
| Returning users (weekly) | 30% of users return within 7 days | Session analytics |

---

## 8. Technical Architecture

```
┌─────────────┐    ┌───────────────────┐    ┌──────────────────┐
│   Streamlit │    │  Google Places    │    │  Gemini API      │
│   Frontend  │───▶│  Text Search API  │    │  (generateContent│
│   (app.py)  │    │  + Place Details  │    │   + JSON mode)   │
└─────────────┘    └───────────────────┘    └──────────────────┘
       │                    │                        │
       ▼                    ▼                        ▼
  places_client.py    Raw place data          agent.py
  (search + details   (name, rating,          (query parsing,
   normalization)      reviews, price,         blurb generation,
                       maps URI)               recommendation
                            │                  ranking)
                            ▼
                       scoring.py
                       (composite 0–1
                        score per place)
```

**Key design decisions:**
- Review text is read live and passed to Gemini for theme inference — it is never written to disk or a database
- Gemini is called with `responseMimeType: application/json` to enforce structured output, eliminating markdown-fence parsing failures
- All Places queries are scoped to Austin, TX at the query level (not via location bias) so the results are city-specific regardless of where the user is
- Session state caches the Top Picks result for the duration of a user session to avoid redundant API calls on re-renders

---

## 9. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Google Places API quota exhaustion | Medium | High | Three-query strategy (restaurant/cafe/bar) uses Text Search, not per-ID calls; cache session results |
| Gemini response rate limit | Medium | Low | Graceful degradation to editorial summaries from Places; explanations are enhancement, not core |
| Places API returning 403 (disabled) | Low (post-setup) | High | Friendly error shown with setup instructions; app does not crash |
| Hidden Gem selection finding no candidate | Low | Low | Falls back to next-highest scorer from any category |
| Gemini hallucinating place facts | Low | Medium | Prompt explicitly restricts explanations to inferred review themes; no factual claims allowed |

---

## 10. Roadmap

### Now (v1 — shipped)
- Four automatic Top Picks with live data and AI explanations
- Ask the Agent natural-language search flow
- Dark editorial UI with burnt-orange brand accent
- Google Maps deep link on every card
- Graceful degradation when APIs are unavailable

### Next (v1.1)
- Neighborhood filter (South Congress, East Austin, Domain, etc.)
- Cuisine-type filter surface in the agent search bar
- Refresh button for Top Picks without full page reload

### Later (v2)
- Mobile app (Expo / React Native) with the same scoring and agent logic
- User favorites — save places across sessions via lightweight auth
- Weekly "Austin Picks Digest" email — top picks for the week delivered to subscribers
- Expanded cities — Dallas and Houston with city-specific scoring tuning
