"""
Rwanda Price Tracker - daily scraper.
 
Collects product prices from Kigali online shops and appends them to
data/price_history.csv, one row per product per shop per day.
 
Runs unattended on GitHub Actions, so it must survive things going wrong:
a shop being down, a page erroring, a connection dropping.
 
    python scrape.py
"""
 
from datetime import date
from pathlib import Path
import time
 
import pandas as pd
import requests
 
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
HISTORY = DATA_DIR / "price_history.csv"
 
# Shopify shops publish their whole catalogue at /products.json.
# Adding another shop is one line - nothing else needs to change.
SHOPS = {
    "amahaho":  "https://amahaho.com",
    "murukali": "https://murukali.com",
}
 
HEADERS = {
    "User-Agent": "rwanda-price-tracker/1.0 (personal data science project)"
}
 
MAX_PAGES = 200          # safety net if a shop never signals the end
RETRIES = 3              # attempts per page before giving up
 
 
def get_page(base_url: str, page: int) -> list:
    """
    Ask for one page of products, retrying if the server hiccups.
 
    Waits get longer between attempts (5s, then 10s). Hammering a struggling
    server makes things worse; backing off gives it room to recover.
    """
    for attempt in range(RETRIES):
        try:
            r = requests.get(
                f"{base_url}/products.json",
                params={"limit": 250, "page": page},
                headers=HEADERS,
                timeout=30,
            )
            r.raise_for_status()
            return r.json().get("products", [])
        except Exception:
            if attempt == RETRIES - 1:
                raise                        # genuinely broken - give up
            time.sleep(5 * (attempt + 1))    # 5s, then 10s
 
 
def fetch_shop(name: str, base_url: str) -> pd.DataFrame:
    """Page through a shop's catalogue, keeping whatever we manage to get."""
    rows = []
    page = 1
 
    while page <= MAX_PAGES:
        try:
            products = get_page(base_url, page)
        except Exception as e:
            # Some shops error instead of returning an empty page at the end.
            # Stop paging, but keep everything collected so far.
            print(f"  {name}: stopped at page {page} ({type(e).__name__})")
            break
 
        if not products:
            break
 
        for p in products:
            if not p.get("variants"):
                continue
            v = p["variants"][0]
            rows.append({
                "shop": name,
                "product_id": p["id"],
                "title": p["title"].strip(),
                "category": p.get("product_type") or "uncategorised",
                "price_rwf": float(v["price"]),
                "grams": v.get("grams") or 0,
                "in_stock": bool(v["available"]),
            })
 
        page += 1
        time.sleep(1)          # one request per second - don't hammer them
 
    print(f"  {name}: {len(rows)} products")
    return pd.DataFrame(rows)
 
 
def scrape_all() -> pd.DataFrame:
    """
    Collect from every shop. If one shop fails entirely, carry on with the
    others - a single broken site should never cost you the whole day.
    """
    frames = []
 
    for name, url in SHOPS.items():
        try:
            frames.append(fetch_shop(name, url))
        except Exception as e:
            print(f"  {name}: FAILED - {e}")
 
    if not frames:
        raise RuntimeError("every shop failed - nothing collected")
 
    df = pd.concat(frames, ignore_index=True)
    df["date"] = date.today().isoformat()
    return df
 
 
def save(df: pd.DataFrame) -> None:
    """Append today's prices to the history file, without duplicating."""
    if HISTORY.exists():
        combined = pd.concat([pd.read_csv(HISTORY), df], ignore_index=True)
    else:
        combined = df
 
    # Re-running on the same day overwrites rather than duplicates.
    combined = combined.drop_duplicates(
        subset=["date", "shop", "title"], keep="last"
    )
    combined = combined.sort_values(["date", "shop", "title"])
    combined.to_csv(HISTORY, index=False)
 
    print(f"\nsaved {len(combined):,} rows "
          f"across {combined['date'].nunique()} day(s) -> {HISTORY}")
 
 
if __name__ == "__main__":
    print(f"scraping {date.today().isoformat()}")
    save(scrape_all())