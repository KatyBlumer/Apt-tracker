# Apt Tracker — Claude Session Notes

## What this is
A single-file React apartment-hunting tracker for Katy and Simon. Everything lives in `index.html`. No build step.

**Stack:** React 18 (CDN), Firebase Firestore (realtime sync), Leaflet maps, Babel standalone (in-browser JSX), hosted on Netlify.

## Git workflow

**Always push to both `main` and `release` together:**
```bash
git push origin HEAD:main HEAD:release
```

The `release` branch exists solely to keep Netlify PR #2 open, which gives a stable preview URL at `https://deploy-preview-2--dreamy-hamster-18b730.netlify.app/`. As long as PR #2 is open, Netlify redeploys that URL on every push to `release`. Never merge or close PR #2.

The session-start hook (`.claude/hooks/session-start.sh`) sets git config automatically:
```
user.email = noreply@anthropic.com
user.name = Claude
```
If commits show as Unverified, run:
```bash
git config user.email noreply@anthropic.com && git config user.name Claude
git rebase --exec "git commit --amend --no-edit --reset-author" origin/<working-branch>
git push origin HEAD:main HEAD:release --force-with-lease
```

## Architecture — the three places to edit

The app is designed so adding new features only requires editing one place each:

### Adding a new column / form field → `ALL_COL_DEFS`
Each entry has:
- `type`: `"yn"` | `"text"` | `"price"` | `"editable"` | `"stars"` | `"distance"` | `"bdba"` | `"status"` | `"title"` | `"actions"`
- `field`: listing field key
- `sortK` + `numericSort`: opt-in to sort bar
- `formPlaceholder`: auto-generates a text input in the form
- `formLabel`: auto-generates a StarSelect (use with `type:"stars"`)
- `tableHidden:true`: appears in form/popup but not the default table columns

Adding a `yn` field example:
```js
{key:"dishwasher", header:"Dishwasher", type:"yn", field:"dishwasher", formPlaceholder:"Dishwasher"},
```
This automatically: adds the form input, renders the table cell, shows in map popups, and is included in `blankDraft()`.

### Adding a new status → `STATUSES`
```js
{ key:"on_hold", label:"On hold", color:"#f4a261" },
```
Add `hideByDefault:true` to include it in the "hide rejected/deleted" toggle.

### Adding a new POI type → `POI_TYPES`
```js
{ key:"school", label:"School", emoji:"🏫" },
```

## Key implementation details

**Authentication:** Shared passphrase stored in localStorage. Used as a Firestore path component to namespace data per workspace.

**Firestore structure:** Two subcollections per workspace — one for listings, one for meta/config (anchors, overlay image).

**Isochrone overlay:** Stored as base64 JPEG in Firestore. Images are compressed to ≤800px on the longest side at 0.7 quality before saving. Firestore doesn't support nested arrays, so bounds `[[s,w],[n,e]]` are stored flat as `{s, w, nn, e}` and reconstructed on load.

**Map anchor points:**
- Simon: 3105 Patrick Henry Dr, Santa Clara CA — `lat:37.3965109149257, lng:-121.98442283299973`
- Katy: Google MTV — `lat:37.422, lng:-122.0841`

**Column order:** Stored per-user in `localStorage` under `"col-order"`. `DEFAULT_COL_ORDER` is the fallback for new users; it's hardcoded (not derived from `ALL_COL_DEFS` order) so the two can differ.

**POIs:** Listings with a `poiType` field set are treated as points of interest — excluded from the table, rendered as emoji markers on the map.

**Distances:** Straight-line (haversine). Marked with `~` if `addressCertain` is false on the listing.

**Parse with Claude:** The paste-to-parse feature calls the Anthropic API directly from the browser. Only works when the app is opened inside a Claude session (API key available). Shows a graceful error otherwise.
