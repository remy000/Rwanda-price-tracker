
"""
Rwanda Price Tracker - daily scraper.
 
Collects product prices from Kigali online shops and appends them to
data/price_history.csv, one row per product per shop per day.
 
Designed to run unattended (GitHub Actions), so it must never crash the
whole run because one shop is down.
 
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
 
# Shopify shops expose their whole catalogue at /products.json.
# Add more here later - the rest of the code doesn't need to change.
SHOPS = {
    "amahaho": "https://amahaho.com",
}
 
# Pretend to be a normal browser and say who we are. Some sites block
# requests with no user agent, and being identifiable is good manners.
HEADERS = {
    "User-Agent": "rwanda-price-tracker/1.0 (personal data science project)"
}
 
 
def fetch_shop(name: str, base_url: str) -> pd.DataFrame:
    """Page through one shop's catalogue and return everything it sells."""
    rows = []
    page = 1
 
    while True:
        r = requests.get(
            f"{base_url}/products.json",
            params={"limit": 250, "page": page},
            headers=HEADERS,
            timeout=30,
        )
        r.raise_for_status()
 
        products = r.json().get("products", [])
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
                "in_stock": bool(v["available"]),
            })
 
        page += 1
        time.sleep(1)          # one request per second - don't hammer them
 
    print(f"  {name}: {len(rows)} products")
    return pd.DataFrame(rows)
 
 
def scrape_all() -> pd.DataFrame:
    """
    Collect from every shop. If one shop fails, carry on with the others -
    a single broken site should never cost you the whole day's data.
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