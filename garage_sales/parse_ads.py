#!/usr/bin/env python3
"""
Parse ph_ads.html, extract sale data, geocode addresses, output sales_data.json.
Run from repo root: .venv/bin/python garage_sales/parse_ads.py
"""

import json
import re
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup


def geocode(address, city="Pleasant Hill", state="CA"):
    full = f"{address}, {city}, {state}"
    url = "https://nominatim.openstreetmap.org/search"
    try:
        r = requests.get(
            url,
            params={"q": full, "format": "json", "limit": 1},
            headers={"User-Agent": "PHGarageSaleMapper/1.0 katyblumer"},
            timeout=10,
        )
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"    geocode error: {e}")
    return None, None


def parse_time_to_24h(t):
    """Convert '9am', '2:30pm', '9:00 AM' → 'HH:MM'."""
    t = t.strip().lower().replace(" ", "")
    ampm = "am" if "am" in t else "pm" if "pm" in t else None
    t = t.replace("am", "").replace("pm", "")
    if ":" in t:
        h, m = t.split(":")
    else:
        h, m = t, "00"
    h, m = int(h), int(m)
    if ampm == "pm" and h != 12:
        h += 12
    elif ampm == "am" and h == 12:
        h = 0
    return f"{h:02d}:{m:02d}"


def extract_hours(text):
    """Return {start, end, raw} or None."""
    pattern = r"(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s*[-–to]+\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm))"
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        raw = m.group(0)
        try:
            start = parse_time_to_24h(m.group(1))
            end = parse_time_to_24h(m.group(2))
            return {"start": start, "end": end, "raw": raw}
        except Exception:
            return {"start": None, "end": None, "raw": raw}
    return None


def parse_ads(html_path):
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    sales = []

    for cell in soup.find_all("div", class_="cell small-12"):
        strong = cell.find("strong")
        if not strong:
            continue
        a_tag = strong.find("a", href=re.compile(r"details\.cfm\?ad_id="))
        if not a_tag:
            continue

        address = a_tag.get_text(" ", strip=True)
        ad_id = re.search(r"ad_id=(\d+)", a_tag["href"]).group(1)

        # First <p>: date + categories
        first_p = cell.find("p")
        date_str = ""
        categories = []
        if first_p:
            raw = first_p.get_text("\n")
            for line in raw.split("\n"):
                line = line.strip()
                if re.search(r"saturday|sunday|friday", line, re.IGNORECASE):
                    date_str = line
                    break
            span = first_p.find("span")
            if span:
                categories = [c.strip() for c in span.get_text().split("|") if c.strip()]

        # Second <p>: ad text (skip the "View Details" one)
        ad_text = ""
        for p in cell.find_all("p")[1:]:
            if not p.find("a", class_="bt_details"):
                ad_text = p.get_text("\n", strip=True)
                break

        hours = extract_hours(ad_text)

        sales.append({
            "id": ad_id,
            "address": address,
            "date": date_str,
            "categories": categories,
            "text": ad_text,
            "hours": hours,
            "lat": None,
            "lng": None,
        })

    return sales


def main():
    here = Path(__file__).parent
    sales = parse_ads(here / "ph_ads.html")
    print(f"Parsed {len(sales)} ads")

    for i, sale in enumerate(sales):
        print(f"  [{i+1:3d}/{len(sales)}] {sale['address']}", end=" ... ", flush=True)
        lat, lng = geocode(sale["address"])
        sale["lat"] = lat
        sale["lng"] = lng
        print("ok" if lat else "FAILED")
        time.sleep(1.1)

    out = here / "sales_data.json"
    out.write_text(json.dumps(sales, indent=2))
    ok = sum(1 for s in sales if s["lat"])
    print(f"\nGeocoded {ok}/{len(sales)}. Saved to {out}")


if __name__ == "__main__":
    main()
