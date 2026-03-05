import os
import requests
import datetime
import pathlib
import sys
import time
import feedparser
import json

# -------------------------------
# CONFIG: RSS feeds for KR Puram / Bengaluru
# -------------------------------
RSS_FEEDS = [
    "https://www.deccanherald.com/rss/local-bengaluru-news.xml",
    "https://www.thehindu.com/news/cities/bangalore/feeder/default.rss",
    "https://www.newindianexpress.com/feeds/metros/bengaluru.xml",
    "https://www.timesofindia.indiatimes.com/rssfeeds/2959238.cms",
    "https://bangaloremirror.indiatimes.com/rssfeedstopstories.cms",
    # Add more local feeds here
]

# -------------------------------
# FUNCTIONS
# -------------------------------
def fetch_local_news_rss(rss_urls, keyword="KR Puram"):
    """Fetch latest news items containing keyword from RSS feeds."""
    news_items = []
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:  # latest 10 items per feed
            title = entry.get("title", "").strip()
            summary = entry.get("summary", "").strip()
            text = f"{title}: {summary}" if summary else title
            if keyword.lower() in text.lower():  # filter for KR Puram
                news_items.append(text)
    return news_items

def generate_prompt(news_items):
    """Generate Gemini prompt from news items."""
    today_iso = datetime.date.today().isoformat()
    news_text = "\n".join([f"- {item}" for item in news_items])
    return (
        f"Today is {today_iso}. You are the News Editor for KR Puram.\n"
        f"Here are the latest local news snippets:\n{news_text}\n\n"
        "TASK: Create a clean, concise local news bulletin suitable for residents.\n"
        "FORMAT: Plain text. Only news content, no commentary."
    )

def call_gemini(prompt, api_key, max_retries=3):
    """Call Gemini API and return summarized news safely."""
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

            # ✅ Defensive check for 'candidates'
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

    news_items = fetch_local_news_rss(RSS_FEEDS)
    if not news_items:
        print("❌ No local news found for KR Puram in RSS feeds.")
        sys.exit(1)

    prompt = generate_prompt(news_items)
    summarized_news = call_gemini(prompt, api_key)
    if not summarized_news:
        print("❌ Failed to fetch summarized news from Gemini.")
        sys.exit(1)

    out_dir = pathlib.Path("output")
    out_dir.mkdir(exist_ok=True)
    filename = out_dir / f"{datetime.date.today().isoformat()}.txt"
    filename.write_text(summarized_news, encoding="utf-8")
    print(f"✅ Local news collected and summarized from Gemini at {filename}")

# -------------------------------
# ENTRY POINT
# -------------------------------
if __name__ == "__main__":
    main()
