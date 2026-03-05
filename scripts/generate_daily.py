import os, requests, datetime, pathlib, sys, base64
from bs4 import BeautifulSoup

# ---------------------------
# Helper: Fetch real news
# ---------------------------
def fetch_real_news(api_key, query):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 10,
        "apiKey": api_key
    }
    r = requests.get(url, params=params, timeout=30)
    if r.status_code != 200:
        print("News API ERROR:", r.status_code, r.text)
        return []
    data = r.json()
    return [{"title": a["title"], "url": a["url"], "description": a.get("description","")} for a in data.get("articles",[])]

# ---------------------------
# Helper: Fetch rentals / sales (scraping example from MagicBricks)
# ---------------------------
def fetch_real_estate(query="KR Puram Bengaluru"):
    url = f"https://www.magicbricks.com/property-for-rent/residential-real-estate?searchLocation={query.replace(' ','%20')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != 200:
        print("Real Estate fetch failed:", r.status_code)
        return []
    
    soup = BeautifulSoup(r.text, "html.parser")
    listings = []
    for card in soup.select(".mb-srp__card"):
        title_tag = card.select_one(".mb-srp__card__title")
        price_tag = card.select_one(".mb-srp__card__price")
        link_tag = card.select_one("a[href]")
        if title_tag and price_tag and link_tag:
            listings.append({
                "title": title_tag.text.strip(),
                "price": price_tag.text.strip(),
                "url": "https://www.magicbricks.com" + link_tag['href']
            })
        if len(listings) >= 10:  # limit to 10
            break
    return listings

# ---------------------------
# Gemini content generation
# ---------------------------
def fetch_gemini_content(prompt_text, headers, model):
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent"
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    r = requests.post(gen_url, headers=headers, json=payload, timeout=60)
    if r.status_code != 200:
        print("ERROR generating Gemini content")
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

# ---------------------------
# Main Automation
# ---------------------------
def main():
    news_api_key = os.getenv("NEWS_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not news_api_key or not gemini_key:
        print("ERROR: Both NEWS_API_KEY and GEMINI_API_KEY are required")
        sys.exit(1)
    
    headers = {"X-goog-api-key": gemini_key}
    today_str = datetime.date.today().isoformat()
    
    text_model = "models/gemini-2.5-flash"
    image_model = "models/gemini-2.5-flash-image"
    
    # ---------------------------
    # 1) Fetch Live News
    # ---------------------------
    news_articles = fetch_real_news(news_api_key, "KR Puram Bengaluru")
    news_block = ""
    for i, a in enumerate(news_articles):
        news_block += f"{i+1}. {a['title']} ({a['url']})\n"
        if a.get("description"):
            news_block += f"   {a['description']}\n\n"
    
    # ---------------------------
    # 2) Fetch Real Estate Listings
    # ---------------------------
    real_estate_listings = fetch_real_estate()
    estate_block = ""
    for i, r in enumerate(real_estate_listings):
        estate_block += f"{i+1}. {r['title']} - {r['price']} ({r['url']})\n"
    
    # ---------------------------
    # 3) Generate combined summary via Gemini
    # ---------------------------
    combined_prompt = f"""
    Summarize the following KR Puram updates for residents:
    
    NEWS ARTICLES:
    {news_block}
    
    RENTALS & PROPERTIES FOR SALE:
    {estate_block}
    
    Include key points, title, price (if applicable), and real URLs. 
    Output in concise format suitable for a daily social media post.
    """
    combined_summary = fetch_gemini_content(combined_prompt, headers, text_model)
    
    # ---------------------------
    # 4) Save summary
    # ---------------------------
    out_dir = pathlib.Path("output")
    out_dir.mkdir(exist_ok=True)
    summary_file = out_dir / f"{today_str}_krpuram_daily.md"
    summary_file.write_text(combined_summary, encoding="utf-8")
    print(f"✅ Daily KR Puram summary saved at {summary_file}")
    
    # ---------------------------
    # 5) Generate social media 10-word news flash
    # ---------------------------
    flash_prompt = f"Summarize the above KR Puram updates in 10 words max, include URLs if possible."
    news_flash = fetch_gemini_content(flash_prompt, headers, text_model).strip().replace("\n"," ")
    
    # ---------------------------
    # 6) Generate image
    # ---------------------------
    image_dir = out_dir / "images" / today_str
    image_dir.mkdir(parents=True, exist_ok=True)
    image_file = image_dir / "krpuram_daily_flash.png"
    generate_image_from_text(news_flash, headers, image_model, image_file)

if __name__ == "__main__":
    main()
