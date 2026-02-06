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
    ]

    chosen = next((p for p in preferred_order if p in supported), supported[0])
    print("Chosen model:", chosen)

    # 2) Generate content
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/{chosen}:generateContent"
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You are a local marketing expert.\n\n"
                            
                            "Business details:\n"
                            "- Business type: Car wash\n"
                            "- City: Bangalore\n"
                            "- Target customers: daily commuters, apartment residents, EV owners\n"
                            "- Key strengths: scratch-free wash, water-saving, careful cleaning\n"
                            "- Starting price: ₹399\n\n"
                        
                            "Create TODAY'S marketing content. Be specific. Do NOT use placeholders.\n\n"
                        
                            "Output clean Markdown with headings:\n\n"
                        
                            "## Instagram\n"
                            "- Caption (friendly, local Indian English)\n"
                            "- Mention Bangalore\n"
                            "- Mention starting price ₹399\n"
                            "- 10–12 relevant hashtags\n\n"
                        
                            "## Facebook\n"
                            "- Slightly longer post\n"
                            "- Explain why scratch-free + water-saving matters\n"
                            "- Mention location Bangalore\n\n"
                        
                            "## YouTube\n"
                            "- Title (max 70 characters)\n"
                            "- Description (5–7 short lines)\n"
                            "- 5 SEO-friendly tags\n\n"
                        
                            "## WhatsApp\n"
                            "- Short message\n"
                            "- Include price ₹399\n"
                            "- Clear CTA: Call / Visit / Reply YES\n\n"
                        
                            "Rules:\n"
                            "- No placeholders like [Your Business]\n"
                            "- No generic corporate language\n"
                            "- Sound like a real local business\n"
                        )
                    }
                ]
            }
        ]
    }

    r = requests.post(
        gen_url,
        headers={**headers, "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )

    if r.status_code != 200:
        print("ERROR generating content")
        print("STATUS:", r.status_code)
        print("BODY:", r.text[:2000])
        sys.exit(1)

    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]

    out = pathlib.Path("output")
    out.mkdir(exist_ok=True)
    today = datetime.date.today().isoformat()
    file = out / f"{today}.md"
    file.write_text(text, encoding="utf-8")
    print("Saved:", file)

if __name__ == "__main__":
    main()
