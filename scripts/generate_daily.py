import os
import requests
import datetime
import pathlib
import sys
import time
import feedparser

def fetch_local_news_rss(rss_url):
    """Fetch latest news entries from an RSS feed."""
    feed = feedparser.parse(rss_url)
    news_items = []
    for entry in feed.entries[:10]:  # Get the latest 10 news items
        title = entry.get("title", "").strip()
        summary = entry.get("summary", "").strip()
        if title or summary:
            news_items.append(f"{title}: {summary}" if summary else title)
    return news_items

def generate_prompt(news_items):
    """Generate a concise prompt for Gemini summarization."""
    today_iso = datetime.date.today().isoformat()
    news_text = "\n".join([f"- {item}" for item in news_items])
    return (
        f"Today is {today_iso}. You are the News Editor for KR Puram.\n"
        f"Here are the latest local news snippets:\n{news_text}\n\n"
        "TASK: Create a clean, concise local news bulletin suitable for residents.\n"
        "FORMAT: Plain text. Only news content, no commentary."
    )

def call_gemini(prompt, api_key, max_retries=3):
    """Call Gemini API and return summarized news."""
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
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
            response = requests.post(gen_url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()

            candidates = data.get("candidates")
            if candidates and len(candidates) > 0:
                candidate = candidates[0]
                if candidate.get("finishReason") == "SAFETY":
                    print("⚠️ API blocked content due to safety filters.")
                    return None
                return candidate["content"]["parts"][0]["text"]
            else:
                print(f"⚠️ Attempt {attempt}: 'candidates' missing or empty. Response: {data.get('error')}")
                if attempt < max_retries:
                    time.sleep(5 * attempt)
                else:
                    return None
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Attempt {attempt}: API request failed: {e}")
            if attempt < max_retries:
                time.sleep(5 * attempt)
            else:
                return None
    return None

def main():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY environment variable is empty.")
        sys.exit(1)

    # Replace this with any KR Puram / Bengaluru RSS feed
    rss_feed_url = "https://www.deccanherald.com/rss/local-bengaluru-news.xml"

    news_items = fetch_local_news_rss(rss_feed_url)
    if not news_items:
        print("❌ No local news found in RSS feed.")
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

if __name__ == "__main__":
    main()
