import os, requests, datetime, pathlib, sys, base64

def fetch_gemini_content_live(prompt_text, headers, model):
    """Generate live content using Gemini models with Google Search grounding."""
    # Using v1beta for tool/search support
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent"
    
    # PAYLOAD FIX: Ensure the 'tools' block is at the root level of the request
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "tools": [{"google_search": {}}]  # Corrected key for search tool
    }
    
    r = requests.post(gen_url, headers=headers, json=payload, timeout=90)
    
    if r.status_code != 200:
        print(f"ERROR: {r.status_code}")
        print(f"Full Body: {r.text}")
        sys.exit(1)
        
    data = r.json()
    try:
        candidate = data["candidates"][0]
        # Grounding check
        if "groundingMetadata" in candidate:
            print("🌐 Live Search successfully grounded this response.")
            
        return candidate["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"ERROR parsing response: {e}")
        sys.exit(1)

def main():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        print("ERROR: GEMINI_API_KEY missing")
        sys.exit(1)
        
    headers = {"X-goog-api-key": key, "Content-Type": "application/json"}

    # FIXED MODEL NAMES (As of March 2026)
    text_model = "models/gemini-3-flash-preview"
    # For images, if 3.1 is out, use the preview string
    image_model = "models/gemini-3.1-flash-image-preview"

    today_str = datetime.date.today().isoformat()
    out_dir = pathlib.Path("output")
    out_dir.mkdir(exist_ok=True)

    # 1) Search for Live Local News
    news_prompt = (
        f"Search for today's ({today_str}) live local news in KR Puram, Bangalore. "
        "Report on traffic (Tin Factory/Hanging Bridge), local civic alerts, "
        "and Holi 2026 celebrations happening today. "
        "Provide a concise, factual bulletin for residents."
    )
    
    print(f"🔍 Fetching live news for {today_str}...")
    news_text = fetch_gemini_content_live(news_prompt, headers, text_model)
    
    # Save the live results
    news_file = out_dir / f"{today_str}_krpuram_news.md"
    news_file.write_text(news_text, encoding="utf-8")
    print(f"✅ Live news saved to {news_file}")

    # 2) Flashcards from Search Data
    flash_prompt = f"Convert this live news into 10 flashcards (Front: Topic | Back: Detail):\n\n{news_text}"
    flash_text = fetch_gemini_content_live(flash_prompt, headers, text_model)
    (out_dir / f"{today_str}_flashcards.md").write_text(flash_text, encoding="utf-8")
    print(f"✅ Flashcards generated.")

if __name__ == "__main__":
    main()
