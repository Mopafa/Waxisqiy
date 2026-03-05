import os, requests, datetime, pathlib, sys

def fetch_gemini_content(prompt_text, headers, model):
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
    payload = {
        "prompt": text,
        "size": "1024x1024"
    }
    r = requests.post(gen_url, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        print("ERROR generating image")
        print("STATUS:", r.status_code)
        print("BODY:", r.text[:2000])
        return
    data = r.json()
    try:
        # The image is usually returned as base64
        import base64
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

    # Choose model for text
    text_model = "models/gemini-2.5-flash"

    # 1) Generate KR Puram news
    news_prompt = (
        "You are a local news reporter for KR Puram, Bangalore.\n"
        "Generate today's news bulletin in sections: Traffic, Weather, Local Events, Alerts, Community Updates.\n"
        "Plain text, concise, suitable for residents.\n"
        f"DATE: {datetime.date.today().isoformat()}"
    )
    news_text = fetch_gemini_content(news_prompt, headers, text_model)

    # Save news
    out_dir = pathlib.Path("output")
    out_dir.mkdir(exist_ok=True)
    news_file = out_dir / f"{datetime.date.today().isoformat()}_krpuram_news.md"
    news_file.write_text(news_text, encoding="utf-8")
    print(f"✅ KR Puram news saved at {news_file}")

    # 2) Generate 10-word flash for image
    flash_prompt = f"Summarize the following KR Puram news in 10 words for a single news flash:\n{news_text}"
    news_flash = fetch_gemini_content(flash_prompt, headers, text_model).strip().replace("\n", " ")

    # 3) Generate image with news flash
    image_dir = out_dir / "images" / datetime.date.today().isoformat()
    image_dir.mkdir(parents=True, exist_ok=True)
    image_file = image_dir / "krpuram_news_flash.png"

    # Use Gemini Image model for generation
    image_model = "models/gemini-2.5-flash-image"
    generate_image_from_text(news_flash, headers, image_model, image_file)

if __name__ == "__main__":
    main()
