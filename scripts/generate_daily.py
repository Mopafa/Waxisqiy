import os, requests, datetime, pathlib, sys

def get_latest_news_context():
    """
    Curated real-time local news for March 5, 2026.
    In a full production build, this would call a News API.
    """
    return {
        "weather": "CRITICAL: Bengaluru UV Index hit 13 today (Extreme). Stay indoors 11AM-3PM.",
        "metro": "BMRCL update: 16km KR Puram-Hoskote Double-Decker Metro study includes TC Palaya Gate station.",
        "water": "BWSSB mapping: KR Puram & Ramamurthy Nagar identified as high-alert water-stress zones.",
        "events": "Holi 2026: Major celebrations at Grand Mercure Gopalan Mall (KR Puram) and Runway 27 (Marathahalli).",
        "traffic": "Alert: Construction dust & congestion at Hanging Bridge due to Blue Line pillar work."
    }

def main():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("ERROR: GEMINI_API_KEY missing")
        sys.exit(1)

    news_data = get_latest_news_context()
    today_iso = datetime.date.today().isoformat()
    out_dir = pathlib.Path("output")
    img_dir = out_dir / "images" / today_iso
    img_dir.mkdir(parents=True, exist_ok=True)

    # 1. GENERATE THE CONTENT (News Text)
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    news_bullets = "\n".join([f"- {v}" for v in news_data.values()])
    prompt = (
        f"Today is {today_iso}. You are the News Editor for 'Namma KR Puram'.\n"
        f"DATA:\n{news_bullets}\n\n"
        "TASK:\n"
        "1. Create a Facebook News Bulletin.\n"
        "2. Create a WhatsApp Alert list.\n"
        "3. Create an Instagram Caption.\n\n"
        "FORMAT: Markdown. Refer to 'Visual Flash Cards' for each section."
    )

    r = requests.post(gen_url, json={"contents": [{"parts": [{"text": prompt}]}]})
    main_text = r.json()["candidates"][0]["content"]["parts"][0]["text"]

    # 2. GENERATE IMAGE FLASH CARD LINKS
    # Note: In a real 2026 environment, you would call an Image Gen API here.
    # For this script, we generate the Markdown references to the images.
    flash_card_md = "\n## 📸 Visual News Flash Cards\n"
    for key in news_data.keys():
        # This link points to the local image folder in your repo
        flash_card_md += f"![{key.upper()} Alert](./images/{today_iso}/{key}.png)\n"

    # 3. SAVE FINAL OUTPUT
    final_output = main_text + "\n" + flash_card_md
    (out_dir / f"{today_iso}.md").write_text(final_output, encoding="utf-8")
    
    print(f"✅ Success: Generated news and flash card references for {today_iso}")

if __name__ == "__main__":
    main()
