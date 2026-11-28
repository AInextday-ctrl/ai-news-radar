---
name: firebase-deploy-and-cache
description: Diagnoses GitHub Actions deployment failures and stale Firebase Hosting rollouts, resolves HTTP 429 Hosting storage quota blocks via version pruning, and manages CDN Cache-Control separation and asset cache busting for AI News Radar. Use when GitHub Actions deploy fails, live pages or images stay stale after CI runs, firebase deploy fails with 429, or modifying firebase.json cache rules.
---

# Firebase Hosting Deploy & Cache Playbook

## 1. Diagnosing Stale Live Content ("No Change" After Fix)

When `https://ainewsradar.xyz` or static assets appear unchanged after a push:

1. **Bypass Cloudflare & check Firebase origin directly**:
   - Inspect live `updated_at` and headers directly against `https://ai-radar-news.web.app` so CDN edge cache and origin state are separated immediately.
   - Because `/` and `/zh` carry `s-maxage=600` (10-min CDN edge cache), append a cache-busting query string (e.g. `https://ainewsradar.xyz/?cb=<ts>` and `https://ai-radar-news.web.app/?cb=<ts>`) when verifying HTML changes immediately after a CI deploy finishes.
2. **Verify active Firebase Hosting releases**:
   - Run `npx firebase-tools hosting:channel:list --site ai-radar-news` and check GitHub Actions CI logs (`Step 12` in `.github/workflows/update_and_deploy.yml`).
3. **Inspect GitHub Actions runs & logs on Windows (no `gh` CLI)**:
   - `gh` is not installed in this environment. Query `https://api.github.com/repos/AInextday-ctrl/ai-news-radar/actions/...` via Python `requests` through local proxy `http://127.0.0.1:7890`.
   - Retrieve the GitHub token via `git credential fill` (`protocol=https\nhost=github.com\n\n`).
   - **Pitfall**: Never use `urllib.request` for `/actions/jobs/{job_id}/logs` — GitHub's `302` redirect to Azure Blob Storage rejects forwarded `Authorization` headers with `401`. Always use `requests.get(..., proxies=...)` (which strips `Authorization` cross-origin) and decode via `r.content.decode('utf-8', errors='replace')` so UTF-8 Chinese log lines are not garbled.
4. **Fail loud in CI**:
   - Never swallow deploy errors with `|| echo`. Ensure `.github/workflows/update_and_deploy.yml` exits non-zero (`exit 1`) on final deploy failure after pruning/retries so frozen deployments never go unnoticed.
5. **Triggering CI verification when pushing via `tools/safe_sync.py`**:
   - `tools/safe_sync.py` auto-commits dirty working trees with `[skip ci]`, which skips GitHub Actions.
   - When pushing workflow/deploy fixes that need an immediate CI verification run, run `git add` + `git commit -m "..."` (without `[skip ci]`) **first**, then run `python tools/safe_sync.py` to rebase and push cleanly.
   - If `tools/safe_sync.py` fails to connect on `127.0.0.1:7890`, inspect the active system proxy via `python -c "import urllib.request; print(urllib.request.getproxies())"` (e.g. `127.0.0.1:7897`) and pass `-c http.proxy=<proxy> -c https.proxy=<proxy>` to `git pull --rebase` / `git push` (with `GIT_TERMINAL_PROMPT=0`); when rebasing frontend-only changes onto newer 24x7 bot data commits, keep upstream `data/` and re-apply only the frontend patch if `origin/main` advanced.

## 2. Resolving `HTTP 429: Hosting storage quota exceeded`

Even with `retainedReleaseCount` configured, frequent 24x7 deploys can leave orphaned `FINALIZED` versions consuming tens of GB and silently halting new releases.

1. **Prune stale versions via Hosting REST API**:
   - In Windows PowerShell behind a local proxy, set proxy env vars first:
     ```powershell
     $env:HTTP_PROXY='http://127.0.0.1:7890'; $env:HTTPS_PROXY='http://127.0.0.1:7890'
     ```
   - Inject `GCP_ACCESS_TOKEN` using the project-owning account `ladyvibeslofi@gmail.com` (other local `gcloud` accounts such as `lofishirley@gmail.com` return `403 PERMISSION_DENIED` on `ai-radar-news`):
     ```powershell
     $env:GCP_ACCESS_TOKEN = (gcloud.CMD auth print-access-token --account ladyvibeslofi@gmail.com)
     python tools/prune_firebase_versions.py 2
     ```
   - Implementation notes in `tools/prune_firebase_versions.py`:
     - Calls `firebasehosting.googleapis.com/v1beta1` with `X-Goog-User-Project: ai-radar-news`.
     - Token priority: `GCP_ACCESS_TOKEN` -> `FIREBASE_TOKEN` (exchanged dynamically via `firebase-tools/lib/auth.js` pointed to by `FIREBASE_TOOLS_AUTH_JS` or npm/npx cache; never hardcode OAuth secrets) -> `gcloud auth print-access-token`.
     - Queries `/versions` with `filter='status="FINALIZED" OR status="CREATED"'` (graceful fallback on 400) so thousands of historical `DELETED` versions never exhaust pagination.
     - Preserves `channels/live` and the newest `keep` versions (`keep=2` by default), deleting older `FINALIZED` versions concurrently (`ThreadPoolExecutor(max_workers=8)`).
2. **Pre-deploy CI protection**:
   - `.github/workflows/update_and_deploy.yml` installs `firebase-tools` once into `$RUNNER_TEMP/fbtools`, exports `FIREBASE_TOOLS_AUTH_JS`, and executes `python tools/prune_firebase_versions.py 2` pre-deploy (and `1` on quota retry) in **both** the `SA_KEY` and `FIREBASE_TOKEN` branches.
3. **Manual fallback deploy**:
   - After pruning locally (with proxy env vars active if on Windows behind `127.0.0.1:7890`), trigger:
     ```bash
     npx --no-install firebase-tools deploy --only hosting --project ai-radar-news --non-interactive
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
  - For `public/js/app-v746.min.js` (matched by `**/js/*-v*.min.js` `immutable` 1-year rule, and filename-locked by CI Assertion 22), keep the filename intact and bump `/js/app-v746.min.js?v=<N>` in `public/index.html` and `public/zh/index.html`.
