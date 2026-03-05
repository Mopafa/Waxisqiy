import os, requests, datetime, pathlib, sys

def get_latest_news_context():
    """Specific news context for March 5, 2026."""
    return {
        "weather": "CRITICAL: Bengaluru UV Index hit 13 today (Extreme). Stay indoors 11AM-3PM.",
        "metro": "BMRCL update: 16km KR Puram-Hoskote Double-Decker Metro study includes TC Palaya Gate station.",
        "water": "BWSSB mapping: KR Puram & Ramamurthy Nagar identified as high-alert water-stress zones.",
        "events": "Holi 2026: Major celebrations at Grand Mercure Gopalan Mall (KR Puram) and Runway 27.",
        "traffic": "Alert: Construction dust & congestion at Hanging Bridge due to Blue Line pillar work."
    }

def main():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY missing in Environment Variables")
        sys.exit(1)

    news_data = get_latest_news_context()
    today_iso = datetime.date.today().isoformat()
    out_dir = pathlib.Path("output")
    out_dir.mkdir(exist_ok=True)

    # Use the stable 2026 endpoint for Gemini 1.5 Flash
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    news_bullets = "\n".join([f"- {v}" for v in news_data.values()])
    prompt = (
        f"Today is {today_iso}. You are the News Editor for 'Namma KR Puram'.\n"
        f"DATA:\n{news_bullets}\n\n"
        "TASK: Create a professional local news bulletin for residents. No marketing.\n"
        "FORMAT: Markdown with sections for Facebook, WhatsApp, and Instagram."
    )

    # Safety Settings to prevent the KeyError: 'candidates' when reporting sensitive news
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

        # Check if the model actually returned a response
        if "candidates" in data and data["candidates"]:
            main_text = data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Save the file
            filename = out_dir / f"{today_iso}.md"
            filename.write_text(main_text, encoding="utf-8")
            print(f"✅ Success: Saved daily news to {filename}")
        else:
            # This helps debug why 'candidates' was missing
            print("⚠️ API Response contained no candidates. Check safety filters or prompt.")
            print("Response details:", data.get("promptFeedback", "No feedback provided"))
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        print(f"❌ API Request Failed: {e}")
        if response is not None:
            print("Server Response:", response.text)
        sys.exit(1)

if __name__ == "__main__":
    main()
