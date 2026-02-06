import os, sys, pathlib, re, requests, datetime

PAGE_ID = os.getenv("FB_PAGE_ID", "").strip()
PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN", "").strip()

if not PAGE_ID or not PAGE_TOKEN:
    print("ERROR: FB_PAGE_ID or FB_PAGE_TOKEN missing")
    sys.exit(1)

# Read today’s md
today = datetime.date.today().isoformat()
md_file = pathlib.Path("output") / f"{today}.md"

if not md_file.exists():
    print("ERROR: Daily markdown file not found:", md_file)
    sys.exit(1)

text = md_file.read_text(encoding="utf-8")

# Extract Facebook section
match = re.search(r"Facebook\s*(.*?)\n\n", text, re.S | re.I)
if not match:
    print("ERROR: Facebook section not found")
    sys.exit(1)

facebook_text = match.group(1).strip()

# Basic validation rules
if "₹" not in facebook_text:
    print("ERROR: Price symbol missing")
    sys.exit(1)

if "Bangalore" not in facebook_text:
    print("ERROR: Location Bangalore missing")
    sys.exit(1)

# Post to Facebook Page
url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/feed"
payload = {
    "message": facebook_text,
    "access_token": PAGE_TOKEN
}

r = requests.post(url, data=payload, timeout=30)

if r.status_code != 200:
    print("ERROR posting to Facebook")
    print(r.text)
    sys.exit(1)

print("Facebook post successful:", r.json())
