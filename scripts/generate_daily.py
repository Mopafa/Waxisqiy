import os, requests, datetime, pathlib, sys

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
        print("STATUS:", mr.status_code)
        print("BODY:", mr.text[:2000])
        sys.exit(1)

    models = mr.json().get("models", [])
    supported = []
    for m in models:
        name = m.get("name", "")
        methods = m.get("supportedGenerationMethods", []) or []
        if "generateContent" in methods:
            supported.append(name)

    print("Models supporting generateContent:")
    for n in supported[:50]:
        print(" -", n)

    if not supported:
        print("ERROR: No models support generateContent for this key.")
        sys.exit(1)

    preferred_order = [
        "models/gemini-1.0-pro",
        "models/gemini-pro",
        "models/text-bison-001",
        "models/gemini-2.5-flash",
    ]

    chosen = next((p for p in preferred_order if p in supported), supported[0])
    print("Chosen model:", chosen)

    # 2) Generate KR Puram news content
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/{chosen}:generateContent"
    prompt_text = (
        "You are a local news reporter for KR Puram, Bangalore.\n\n"
        "TASK: Generate today's news bulletin for KR Puram residents.\n"
        "Include recent events, traffic, weather, community updates, and any relevant alerts.\n"
        "FORMAT: Plain text. Concise, easy to read, suitable for a local news bulletin.\n"
        "DO NOT use placeholders.\n"
        f"DATE: {datetime.date.today().isoformat()}\n\n"
        "Output in sections with headings like:\n"
        "## Traffic\n"
        "## Weather\n"
        "## Local Events\n"
        "## Alerts\n"
        "## Community Updates\n"
    )

    payload = {
        "contents": [
            {"parts": [{"text": prompt_text}]}
        ]
    }

    r = requests.post(gen_url, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        print("ERROR generating news content")
        print("STATUS:", r.status_code)
        print("BODY:", r.text[:2000])
        sys.exit(1)

    data = r.json()
    try:
        # FIXED: access content correctly as dict, not list
        news_text = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print("ERROR parsing Gemini response:", e)
        print("Full response:", data)
        sys.exit(1)

    out_dir = pathlib.Path("output")
    out_dir.mkdir(exist_ok=True)
    filename = out_dir / f"{datetime.date.today().isoformat()}_krpuram_news.md"
    filename.write_text(news_text, encoding="utf-8")
    print(f"✅ KR Puram news saved at {filename}")


if __name__ == "__main__":
    main()
