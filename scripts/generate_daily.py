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

def main():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        print("ERROR: GEMINI_API_KEY secret is missing")
        sys.exit(1)
    headers = {"X-goog-api-key": key}

    # 1) List models
    list_url = "https://generativelanguage.googleapis.com/v1beta/models"
    mr = requests.get(list_url, headers=headers, timeout=60)
    if mr.status_code != 200:
        print("ERROR listing models")
        sys.exit(1)
    models = mr.json().get("models", [])
    supported = [m.get("name") for m in models if "generateContent" in (m.get("supportedGenerationMethods") or [])]
    if not supported:
        print("ERROR: No models support generateContent for this key.")
        sys.exit(1)

    # Pick preferred model
    preferred_order = ["models/gemini-2.5-flash", "models/gemini-1.0-pro", "models/text-bison-001"]
    model = next((p for p in preferred_order if p in supported), supported[0])
    print("Chosen model:", model)

    # 2) Generate KR Puram news
    news_prompt = (
        "You are a local news reporter for KR Puram, Bangalore.\n"
        "Generate today's news bulletin in sections: Traffic, Weather, Local Events, Alerts, Community Updates.\n"
        "Plain text, concise, suitable for residents. Do NOT use placeholders.\n"
        f"DATE: {datetime.date.today().isoformat()}"
    )
    news_text = fetch_gemini_content(news_prompt, headers, model)

    # Save news
    out_dir = pathlib.Path("output")
    out_dir.mkdir(exist_ok=True)
    news_file = out_dir / f"{datetime.date.today().isoformat()}_krpuram_news.md"
    news_file.write_text(news_text, encoding="utf-8")
    print(f"✅ KR Puram news saved at {news_file}")

    # 3) Generate flashcards (10 words/phrases + explanation)
    flashcard_prompt = (
        f"Summarize the following news into 10 key words or phrases for flashcards.\n"
        f"For each, provide a short explanation (1–2 sentences) for residents.\n\n"
        f"News content:\n{news_text}\n\n"
        f"Output in Markdown format:\n"
        f"- Front: <word/phrase>\n"
        f"- Back: <explanation>"
    )
    flashcards_text = fetch_gemini_content(flashcard_prompt, headers, model)

    # Save flashcards
    flash_file = out_dir / f"{datetime.date.today().isoformat()}_krpuram_flashcards.md"
    flash_file.write_text(flashcards_text, encoding="utf-8")
    print(f"✅ KR Puram flashcards saved at {flash_file}")

if __name__ == "__main__":
    main()
