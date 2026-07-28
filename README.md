Rwanda price tracker

Tracking retail prices in Kigali daily, to build an independent measure of inflation and compare it against Rwanda's official CPI.

Rwanda's official inflation was running at 13.6% year-on-year in June 2026. This project asks a simple question: does that match what's actually happening to prices in Kigali's online shops?

How it works

A scraper runs every morning at 06:00 Kigali time, collects prices from Kigali online retailers, and appends them to data/price_history.csv. Nothing is manual — the dataset grows on its own.

Data
File	What it is
data/price_history.csv	One row per product, per shop, per day

Columns: date, shop, product_id, title, category, price_rwf, in_stock

Sources
Amahaho — Kigali online grocery
NISR — official Consumer Price Index
Collection ethics

Only public product listings are collected — no personal data. robots.txt was checked and permits access to product pages. Requests are rate-limited to one per second, once per day. Published output is an aggregate price index, not a copy of any shop's catalogue.

Status

Collection started July 2026. Analysis and dashboard to follow once enough history has accumulated