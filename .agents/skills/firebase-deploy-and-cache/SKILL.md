---
name: firebase-deploy-and-cache
description: Diagnoses stale Firebase Hosting rollouts, resolves HTTP 429 Hosting storage quota blocks via version pruning, and manages CDN Cache-Control separation and asset cache busting for AI News Radar. Use when live pages or images stay stale after CI runs, firebase deploy fails with 429, or modifying firebase.json cache rules.
---

# Firebase Hosting Deploy & Cache Playbook

## 1. Diagnosing Stale Live Content ("No Change" After Fix)

When `https://ainewsradar.xyz` or static assets appear unchanged after a push:

1. **Bypass Cloudflare & check Firebase origin directly**:
   - Inspect live `updated_at` and headers directly against `https://ai-radar-news.web.app` so CDN edge cache and origin state are separated immediately.
2. **Verify active Firebase Hosting releases**:
   - Run `npx firebase-tools hosting:channel:list --site ai-radar-news` and check GitHub Actions CI logs (`Step 12` in `.github/workflows/update_and_deploy.yml`).
3. **Fail loud in CI**:
   - Never swallow deploy errors with `|| echo`. Ensure `.github/workflows/update_and_deploy.yml` exits non-zero (`exit 1`) on final deploy failure after pruning/retries so frozen deployments never go unnoticed.

## 2. Resolving `HTTP 429: Hosting storage quota exceeded`

Even with `retainedReleaseCount` configured, frequent 24x7 deploys can leave orphaned `FINALIZED` versions consuming tens of GB and silently halting new releases.

1. **Prune stale versions via Hosting REST API**:
   - Run:
     ```bash
     python tools/prune_firebase_versions.py 2
     ```
   - Implementation notes in `tools/prune_firebase_versions.py`:
     - Calls `firebasehosting.googleapis.com/v1beta1` using `GCP_ACCESS_TOKEN` or `gcloud auth print-access-token` with `X-Goog-User-Project: ai-radar-news`.
     - Preserves `channels/live` and the newest `keep` versions (`keep=2` by default), deleting older `FINALIZED` versions concurrently (`ThreadPoolExecutor(max_workers=8)`).
2. **Pre-deploy CI protection**:
   - `.github/workflows/update_and_deploy.yml` activates `SA_KEY` via `gcloud auth activate-service-account`, sets `GCP_ACCESS_TOKEN`, and executes `python tools/prune_firebase_versions.py 2` both before deployment and automatically on quota retry.
3. **Manual fallback deploy**:
   - After pruning locally, trigger:
     ```bash
     npx firebase-tools deploy --only hosting --non-interactive
     ```

## 3. Immutable vs Mutable Asset Caching Rules (`firebase.json`)

- **Do not trap mutable product photos under `immutable` 1-year headers**:
  - `firebase.json` globally applies `max-age=31536000, immutable` to `**/*.webp`, which locks browsers into stale images if an image is replaced under the same filename.
  - Keep an explicit override for mutable catalog photos in `firebase.json`:
    - `/images/products/**` -> `Cache-Control: public, max-age=86400, stale-while-revalidate=604800`
  - Keep scripts/styles revalidated:
    - `**/*.@(js|css|mjs)` -> `Cache-Control: no-cache, must-revalidate`
- **Instant invalidation when replacing assets or UI behavior**:
  - Bump query cache-busters (`PHOTO_VER` in `public/js/monetization.js` and `?v=<N>` query params on `monetization.js` / `page_theme.js` in static publishers and HTML).
