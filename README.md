# Austin Picks

Austin Picks is a Streamlit app for discovering restaurants, cafes, and bars in Austin, Texas. It loads live Google Places results, ranks them using rating, rating volume, and affordability, and uses Gemini to explain why each recommendation fits.

## Setup

1. Install the Python dependencies:

   ```bash
   uv sync
   ```

2. Add these secure environment variables:

   - `GOOGLE_PLACES_API_KEY` — a Google Places API (New) key with Places API access
   - `GEMINI_API_KEY` — a Gemini API key with access to Gemini 3 Flash Preview

   The Google Cloud project behind the Places key must have **Places API (New)**
   enabled, and the key must allow requests to `places.googleapis.com`.

3. Start the app:

   ```bash
   streamlit run app.py --server.port 5000
   ```

Review snippets are fetched live from Google Places and are not written to a database or file.