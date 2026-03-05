import os, requests, datetime, pathlib, sys

def get_latest_news_context():
    """General local community news for KR Puram & TC Palaya (March 5, 2026)."""
    return {
        "metro_update": "Namma Metro Phase 4: BMRCL conceptualizing new lines to suburban areas, including KR Puram connectivity.",
        "traffic_alert": "MG Road Resurfacing: Work begins today on a 2.2km stretch. Expect minor delays during evening hours.",
        "weather": "Today's Outlook: Clear skies with a high of 32°C. Evenings remain pleasant at 21°C.",
        "local_events": "Holi 2026: Rain Dance & Foam Party today at Bella House Go Go, KR Puram. Music starts at 6 PM.",
        "community": "Infrastructure: Traffic police propose 101 new skywalks across Bengaluru junctions to improve pedestrian safety."
    }

def main():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("❌ ERROR: GEMINI_API_KEY missing.")
        sys.exit(1)

    news_data = get_latest_news_context()
    today_iso = datetime.date.today().isoformat()
    out_dir = pathlib.Path("output")
    out_dir.mkdir(exist_ok=True)

    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    news_bullets = "\n".join([f"- {v}" for v in news_data.values()])
    prompt = (
        f"Today is {today_iso}. You are the Community News Editor for 'Namma KR Puram'.\n"
        f"LATEST UPDATES:\n{news_bullets}\n\n"
        "TASK: Create a friendly local bulletin for residents.\n"
        "SECTIONS: 1. Facebook Post, 2. WhatsApp Alert, 3. Instagram Tags.\n"
        "Avoid any alarming language."
    )

    # FIX: Add safetySettings to the payload to prevent silent blocking
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

        # FIX: Check if 'candidates' exists and has content before accessing index [0]
        if "candidates" in data and len(data["candidates"]) > 0:
            candidate = data["candidates"][0]
            
            # Check if the text part actually exists (sometimes it's blocked here)
            if "content" in candidate and "parts" in candidate["content"]:
                main_text = candidate["content"]["parts"][0]["text"]
                filename = out_dir / f"{today_iso}.md"
                filename.write_text(main_text, encoding="utf-8")
                print(f"✅ Success: News generated at {filename}")
            else:
                print(f"⚠️ Warning: Candidate exists but has no content. Reason: {candidate.get('finishReason')}")
                sys.exit(1)
        else:
            print("❌ No candidates returned. The prompt might have been blocked.")
            print("Full API Response for debugging:", data)
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error during API call: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
