import os, requests, datetime, pathlib, sys, base64

def fetch_gemini_content_live(prompt_text, headers, model):
    """Generate live content using Gemini models with Google Search grounding."""
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent"
    
    # NEW: The payload now includes 'tools' to enable live Google Search
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "tools": [{"googleSearch": {}}]
    }
    
    r = requests.post(gen_url, headers=headers, json=payload, timeout=90)
    if r.status_code != 200:
        print(f"ERROR: {r.status_code} - {r.text[:500]}")
        sys.exit(1)
        
    data = r.json()
    try:
        # Check for grounding metadata to confirm live search happened
        candidate = data["candidates"][0]
        if "groundingMetadata" in candidate:
            print("🌐 Live Search used for this update.")
            
        return candidate["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"ERROR parsing live response: {e}")
        sys.exit(1)

def generate_image_from_text(text, headers, model, filename):
    """Generate an image using Gemini Image Generation API."""
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateImage"
    payload = {"prompt": text, "aspect_ratio": "1:1"}
    
    r = requests.post(gen_url, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        print(f"ERROR generating image: {r.status_code}")
        return
        
    data = r.json()
    try:
        # Saving the first generated image
        img_b64 = data["output"]["images"][0]["image_bytes"]
        img_bytes = base64.b64decode(img_b64)
        with open(filename, "wb") as f:
            f.write(img_bytes)
        print(f"✅ Image saved at {filename}")
    except Exception as e:
        print(f"ERROR parsing image response: {e}")

def main():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        print("ERROR: GEMINI_API_KEY secret is missing")
        sys.exit(1)
    headers = {"X-goog-api-key": key, "Content-Type": "application/json"}

    # Use Gemini 3 Flash for the best live grounding performance
    text_model = "models/gemini-3-flash"
    image_model = "models/gemini-3-flash-image"

    today_str = datetime.date.today().isoformat()
    out_dir = pathlib.Path("output")
    out_dir.mkdir(exist_ok=True)

    # --- 1) Fetch Live News ---
    news_prompt = (
        f"Search for the absolute latest news in KR Puram, Bangalore for TODAY ({today_str}).\n"
        "Focus on: \n"
        "1. Traffic status at Tin Factory and KR Puram hanging bridge.\n"
        "2. Any civic protests or GBA (Greater Bengaluru Authority) updates.\n"
        "3. Local events like Holi 2026 parties in KR Puram.\n"
        "4. Weather and water alerts.\n"
        "Structure as a professional bulletin."
    )
    news_text = fetch_gemini_content_live(news_prompt, headers, text_model)
    (out_dir / f"{today_str}_krpuram_news.md").write_text(news_text, encoding="utf-8")

    # --- 2) Generate Flashcards from Live Content ---
    flashcard_prompt = (
        f"Convert this live news into 10 key flashcards for residents.\n"
        "Format: Front (Topic) | Back (Brief explanation).\n\n"
        f"News: {news_text}"
    )
    flashcards_text = fetch_gemini_content_live(flashcard_prompt, headers, text_model)
    (out_dir / f"{today_str}_krpuram_flashcards.md").write_text(flashcards_text, encoding="utf-8")

    # --- 3) Visual News Flash ---
    flash_prompt = f"Create a 10-word punchy 'News Flash' headline based on this: {news_text}"
    news_flash = fetch_gemini_content_live(flash_prompt, headers, text_model).strip()
    
    image_file = out_dir / f"{today_str}_flash.png"
    generate_image_from_text(f"News headline: {news_flash}. Bangalore urban style.", headers, image_model, image_file)

if __name__ == "__main__":
    main()
