import os, requests, datetime, pathlib, sys

def get_latest_news_context():
    """Community news context for March 5, 2026."""
    return {
        "metro": "BMRCL update: Phase 4 expansion conceptualizing new suburban links near KR Puram.",
        "traffic": "MG Road: Roadwork begins today between Trinity and Cubbon Park. Expect evening slows.",
        "weather": "Sunny with a high of 32°C. Local UV Index is high—stay hydrated!",
        "events": "Holi 2026: Rain dance celebrations at KR Puram local clubs starting 6PM.",
        "infrastructure": "New skywalks proposed for pedestrian safety across 101 city junctions."
    }

def main():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY environment variable is empty.")
        sys.exit(1)

    news_data = get_latest_news_context()
    today_iso = datetime.date.today().isoformat()
    out_dir = pathlib.Path("output")
    out_dir.mkdir(exist_ok=True)

    # Global endpoint for better quota stability in 2026
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    news_bullets = "\n".join([f"- {v}" for v in news_data.values()])
    prompt = (
        f"Today is {today_iso}. Act as the News Editor for 'Namma KR Puram'.\n"
        f"NEWS DATA:\n{news_bullets}\n\n"
        "TASK: Create a professional local community bulletin for residents.\n"
        "FORMAT: Markdown. Include sections for Facebook and WhatsApp."
    )

    # 1. ADD SAFETY SETTINGS: This prevents the 'candidates' key from disappearing
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    try:
        response = requests.post(gen_url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        # 2. DEFENSIVE CHECK: Don't crash if 'candidates' is missing
        if "candidates" in data and len(data["candidates"]) > 0:
            candidate = data["candidates"][0]
            
            # Check for the finishReason (usually 'SAFETY' or 'STOP')
            if candidate.get("finishReason") == "SAFETY":
                print("⚠️ API blocked this content due to safety filters.")
                sys.exit(1)

            main_text = candidate["content"]["parts"][0]["text"]
            filename = out_dir / f"{today_iso}.md"
            filename.write_text(main_text, encoding="utf-8")
            print(f"✅ Success: Daily news generated at {filename}")
        else:
            # Helpful debugging for the KeyError
            print("❌ Error: API response succeeded but 'candidates' list is missing/empty.")
            print(f"Prompt Feedback: {data.get('promptFeedback', 'No feedback provided')}")
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
