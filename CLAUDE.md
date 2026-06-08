# Apt-tracker

Apartment hunting tracker for personal use — shared with my boyfriend so we can both view and edit it.

## Stack

Single-file app: everything lives in `index.html`. No build step, no package.json.

- **React 18** (loaded from CDN via Babel standalone — JSX transpiled in-browser)
- **Leaflet** (map view, also from CDN)
- **Firebase Firestore** (real-time database so both users see live updates)

## Deployment

Hosted on **Netlify free tier**. The free tier has a monthly build credit limit — when credits run out, pushes to `main` won't trigger a new production deploy.

Workaround: Netlify offers unlimited **branch deploys**, but the preview URL changes with each deploy. URLs look like:
`https://deploy-preview-2--dreamy-hamster-18b730.netlify.app/`

This is fine for now — share the latest branch deploy URL with my boyfriend to preview changes mid-month.

## Development notes

- Edit `index.html` directly — there is no build/compile step.
- Firebase config is hardcoded in `index.html` (it's a client-side key scoped to this project, not a secret).
- To test locally, open `index.html` in a browser or use a simple static server (`python3 -m http.server`).
