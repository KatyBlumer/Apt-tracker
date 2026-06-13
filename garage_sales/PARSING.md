# How parse_ads.py works

Run from the repo root:
```
.venv/bin/python garage_sales/parse_ads.py
```
Reads `ph_ads.html`, geocodes every address, writes `sales_data.json`.

---

## HTML structure

The source page uses Foundation CSS grid. Each ad is a `<div class="cell small-12">` containing two `<p>` tags:

**First `<p>`** — header info:
- Day text (`Saturday, Jun 13`) as a bare text node
- `<strong><a href="details.cfm?ad_id=NNNN">ADDRESS</a></strong>` — the address and the numeric ad ID
- `<span style="font-size: 14px;">Cat1 | Cat2 | Cat3</span>` — pipe-separated categories

**Second `<p>`** — free-text ad body (skipping the "View Details" `<a class="bt_details">` paragraph)

The parser identifies ads by finding `<strong><a href="...details.cfm?ad_id=...">` links, then walks up to the enclosing cell to grab the other fields.

---

## Hours parsing

Hours are extracted from the ad body text with a two-step approach.

### Step 1 — regex match

```
(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s*[-–to]+\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm))
```

This matches a start time, a separator (`-`, `–`, or `to`), and an end time. Each time can be:
- `9am`, `10pm`
- `9:00am`, `2:30 PM`
- with or without spaces between digits and am/pm

It takes the **first** match in the text, so if a sale lists different hours for Saturday vs Sunday on separate lines, only Saturday's hours are captured.

### Step 2 — convert to 24-hour format

`parse_time_to_24h` normalizes each matched time to `HH:MM`:
- Strips spaces, lowercases
- Splits on `:` if present, otherwise assumes `:00`
- Applies am/pm: adds 12 for pm (except 12pm stays 12), sets 12am → 0

The output `hours` field looks like:
```json
{ "start": "10:00", "end": "15:00", "raw": "10am-3pm" }
```
`raw` preserves the original text as written. If parsing the times fails (rare malformed input), `start`/`end` are `null` but `raw` is still saved. If no time range is found at all, `hours` is `null`.

---

## Geocoding

Each address is sent to **Nominatim** (OpenStreetMap's free geocoder, no API key needed).

The city and state are appended automatically:
```
"31 Kathryn Dr"  →  "31 Kathryn Dr, Pleasant Hill, CA"
```

Nominatim's terms require a descriptive `User-Agent` header and a rate limit of **1 request per second**. The script sleeps 1.1 s between requests, so 134 addresses take ~2.5 minutes.

### Why some addresses fail

6/134 addresses returned no result. Common reasons:
- Vague addresses (`Sparrow Ct` with no number — Nominatim can't pin a specific point)
- Typos or non-standard abbreviations (`355 1st Ave So`, `53 Dobbs pleasant Hill`)
- Streets that aren't in OSM's Pleasant Hill data

Failed entries have `"lat": null, "lng": null` in the JSON and are silently skipped when the map renders markers.

### Re-running

You can re-run the script at any time; it overwrites `sales_data.json`. To fix a failed address, edit the `address` field in the JSON by hand after the script runs — the map reads whatever is in the file.
