import os
import requests
import datetime
import pathlib
import sys
import time
import json

# -------------------------------
# FUNCTIONS
# -------------------------------
def call_gemini(prompt, api_key, max_retries=3):
    """Call Gemini API and return content safely."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(url, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()

            # Defensive access
            candidates = data.get("candidates")
            if not candidates:
                print(f"⚠️ Attempt {attempt}: 'candidates' missing. Full response:\n{json.dumps(data, indent=2)}")
                if attempt < max_retries:
                    time.sleep(5 * attempt)
                continue

            candidate = candidates[0]
            if candidate.get("finishReason") == "SAFETY":
                print("⚠️ API blocked content due to safety filters.")
                return None

            return candidate.get("content", {}).get("parts", [{}])[0].get("text")

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Attempt {attempt}: Request failed: {e}")
            if attempt < max_retries:
                time.sleep(5 * attempt)

    return None

# -------------------------------
# MAIN
# -------------------------------
def main():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY environment variable is empty.")
        sys.exit(1)

    # Prompt for KR Puram news today
    today_iso = datetime.date.today().isoformat()
    prompt = f"Today is {today_iso}. Give me a concise list of the latest local news in KR Puram, Bengaluru. Format: plain text, only news content."

    summarized_news = call_gemini(prompt, api_key)
    if not summarized_news:
        print("❌ Failed to fetch news from Gemini.")
        sys.exit(1)

    out_dir = pathlib.Path("output")
    out_dir.mkdir(exist_ok=True)
    filename = out_dir / f"{today_iso}.txt"
    filename.write_text(summarized_news, encoding="utf-8")
    print(f"✅ KR Puram news collected and saved at {filename}")

# -------------------------------
# ENTRY POINT
# -------------------------------
if __name__ == "__main__":
    main()
