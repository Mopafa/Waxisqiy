import os, requests, datetime, pathlib, sys, base64

def fetch_gemini_content(prompt_text, headers, model):
    """Generate text content using Gemini models."""
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent"
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    r = requests.post(gen_url, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        print("ERROR generating content")
        print("STATUS:", r.status_code)
        print("BODY:", r.text[:2000])
        sys.exit(1)
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("ERROR parsing Gemini response:", e)
        print("Full response:", data)
        sys.exit(1)

def generate_image_from_text(text, headers, model, filename):
    """Generate an image from text using Gemini Image Generation API."""
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateImage"
    payload = {"prompt": text, "size": "1024x1024"}
    r = requests.post(gen_url, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        print("ERROR generating image")
        print("STATUS:", r.status_code)
        print("BODY:", r.text[:2000])
        return
    data = r.json()
    try:
        img_b64 = data["artifacts"][0]["binary"]
        img_bytes = base64.b64decode(img_b64)
        with open(filename, "wb") as f:
            f.write(img_bytes)
        print(f"✅ Image saved at {filename}")
    except Exception as e:
        print("ERROR parsing image response:", e)
        print("Full response:", data)

def main():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        print("ERROR: GEMINI_API_KEY secret is missing")
        sys.exit(1)
    headers = {"X-goog-api-key": key}

    text_model = "models/gemini-2.5-flash"
    image_model = "models/gemini-2.5-flash-image"

    today_str = datetime.date.today().isoformat()

    # --- 1) Generate strictly today KR Puram news with links ---
    news_prompt = (
        f"You are a local news reporter for KR Puram, Bangalore.\n"
        f"ONLY include news and events that happen TODAY ({today_str}).\n"
        "Do NOT include recurring, past, or speculative events.\n"
        "Generate in sections: Traffic, Weather, Local Events, Alerts, Community Updates.\n"
        "For each news item, include a **simulated source link** in the format [link](https://example.com/<short-title>).\n"
        "Output plain text, concise, suitable for residents."
    )
    news_text = fetch_gemini_content(news_prompt, headers, text_model)

    # Save news
    out_dir = pathlib.Path("output")
    out_dir.mkdir(exist_ok=True)
    news_file = out_dir / f"{today_str}_krpuram_news.md"
    news_file.write_text(news_text, encoding="utf-8")
    print(f"✅ KR Puram news saved at {news_file}")

    # --- 2) Generate flashcards (10 key words/phrases) with links ---
    flashcard_prompt = (
        f"Summarize the following news into 10 key words or phrases for flashcards.\n"
        f"Each phrase must reference today's events ({today_str}) and include the same source link as in the news.\n"
        f"Provide 1–2 sentence explanation per phrase.\n\n"
        f"News content:\n{news_text}\n\n"
        "Output in Markdown format:\n"
        "- Front: <word/phrase>\n"
        "- Back: <explanation> [link](https://example.com/<short-title>)"
    )
    flashcards_text = fetch_gemini_content(flashcard_prompt, headers, text_model)

    flash_file = out_dir / f"{today_str}_krpuram_flashcards.md"
    flash_file.write_text(flashcards_text, encoding="utf-8")
    print(f"✅ KR Puram flashcards saved at {flash_file}")

    # --- 3) Generate 10-word news flash with date and links ---
    flash_prompt = (
        f"Summarize the following KR Puram news in 10 words for a single news flash.\n"
        f"Include today's date ({today_str}) and the source links from the news in the format [link](https://example.com/<short-title>).\n"
        f"News content:\n{news_text}"
    )
    news_flash = fetch_gemini_content(flash_prompt, headers, text_model).strip().replace("\n", " ")

    # --- 4) Generate image for news flash ---
    image_dir = out_dir / "images" / today_str
    image_dir.mkdir(parents=True, exist_ok=True)
    image_file = image_dir / "krpuram_news_flash.png"
    generate_image_from_text(news_flash, headers, image_model, image_file)

if __name__ == "__main__":
    main()
