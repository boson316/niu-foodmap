# Yilan University Food Map — Deployment & Distribution

**Languages:** [English](deployment-strategy.md) · [中文](部署與推廣建議.md)

> **Audience:** National Ilan University students (mobile + desktop).  
> **Project:** `python程式期末專案_美食系統`

---

## App vs. cloud?

**Recommendation: ship a cloud web app first (PWA optional). Skip a native app for now.**

| | Cloud web | Native app |
|---|-----------|------------|
| **Distribution to students** | Share a link or QR; works on iOS and Android | App Store / sideload friction |
| **Maintenance** | Deploy once, everyone updates | Separate iOS + Android codebases |
| **Fits current stack** | Streamlit → Streamlit Community Cloud / Render / Railway | Rewrite the frontend |
| **Final project demo** | Deploy same day | Unlikely in time |

---

## Suggested roadmap

### Phase 1 — Final project (now)

- Deploy on **Streamlit Community Cloud** (free tier)
- Share URL via department, clubs, LINE groups

```powershell
cd python程式期末專案_美食系統
$env:PYTHONPATH = "src"
streamlit run src/streamlit_app.py
```

### Phase 2 — After summer (if traffic grows)

- Migrate to **FastAPI + static frontend**
- Reuse wheel HTML from `src/foodmap/wheel.py`
- Optional campus subdomain (e.g. `foodmap.niu.edu.tw`)

### Phase 3 — PWA (optional, low cost)

- Add `manifest.json` + home-screen icons
- “Add to Home Screen” feels app-like without store listing

### Phase 4 — Native app (defer)

Build only when you need push notifications, offline cache, or background location. Current features (list, map, wheel, scores) do not require it.

---

## Deployment checklist

### Data

| File | Notes |
|------|--------|
| `data/places_cache.json` | Offline Google Places cache; must be available on the server, or fall back to `sample_restaurants.json` |
| `src/foodmap/data/sample_restaurants.json` | Built-in mock data for demos without API keys |

### Security

- Never commit `GOOGLE_MAPS_API_KEY` or `.env`
- Before a public push: `git status --short --ignored`

### Streamlit Cloud (reference)

| Setting | Value |
|---------|--------|
| Main file | `src/streamlit_app.py` |
| Python | 3.10+ |
| Env | `PYTHONPATH=src` if imports require it |
| Secrets | `GOOGLE_MAPS_API_KEY` only for **re-fetching** Places; runtime reads JSON cache |

---

## One-line decision

> Students need “open and use” — cloud web + QR is the best ROI; native apps wait until push/offline/location are hard requirements.

---

*Version: 2026-06-13 · Aligned with `AI_HANDOFF.md` and the Streamlit stack.*
