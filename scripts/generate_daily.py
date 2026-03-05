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

def call_gemini_with_fallback(prompt, api_key, models=None, max_retries=3):
    """Call Gemini API using multiple models until one succeeds."""
    if models is None:
        models = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
        ]

    for model in models:
        print(f"🔍 Trying Gemini model: {model}")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "candidateCount": 1
        }

        for attempt in range(1, max_retries + 1):
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=60)
                r.raise_for_status()
                data = r.json()

                candidates = data.get("candidates")
                if candidates and len(candidates) > 0:
                    candidate = candidates[0]
                    if candidate.get("finishReason") == "SAFETY":
                        print(f"⚠️ API blocked content due to safety filters for model {model}.")
                        return None
                    return candidate.get("content", [{}])[0].get("parts", [{}])[0].get("text")

                print(f"⚠️ Missing candidates for {model}, full response:\n{json.dumps(data, indent=2)}")
                break  # Move to next model

            except requests.exceptions.HTTPError as e:
                if r.status_code == 404:
                    print(f"❌ Model {model} not found (404). Trying next model.")
                    break
                print(f"⚠️ Attempt {attempt} failed for {model}: {e}")
            except Exception as e:
                print(f"⚠️ General error with {model}: {e}")
            time.sleep(5 * attempt)  # Exponential backoff
    return None

# -------------------------------
# MAIN
# -------------------------------
def main():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY environment variable is empty.")
        sys.exit(1)

    today_iso = datetime.date.today().isoformat()
    prompt = f"Today is {today_iso}. Give me a concise list of the latest local news in KR Puram, Bengaluru. Format: plain text, only news content."

    summarized_news = call_gemini_with_fallback(prompt, api_key)
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
