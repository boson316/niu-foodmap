# Streamlit Cloud × GitHub Deployment (NIU Food Map)

**Languages:** [English](streamlit-cloud-deploy.md) · [中文](streamlit-cloud-部署步驟.md)

> **Goal:** Free Streamlit Community Cloud hosting for the final demo; share URL / QR with students.

---

## 0. Pre-flight (local)

```powershell
cd "c:\Users\User\Documents\code\python程式期末專案_美食系統"
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m pytest -q
streamlit run src/streamlit_app.py
```

Open `http://localhost:8501` and verify both tabs work.

---

## 1. Decide upfront

| Item | Recommendation |
|------|----------------|
| **GitHub account** | `boson316` or `b1443204-niu` (see workspace `SSH_GIT.md`) |
| **Public vs private** | **Public** for easy QR sharing |
| **Cloud data size** | See “Data strategy” below |

### Data strategy

| File | In Git? | On cloud |
|------|---------|----------|
| `data/places_cache.json` | No (`.gitignore`) | Not uploaded |
| `data/places_cache.public.json` | Yes (optional) | ~100 restaurants (recommended) |
| Neither | — | 15 sample restaurants only |

**Recommended for demo (~100 places):**

```powershell
cd "c:\Users\User\Documents\code\python程式期末專案_美食系統"
Copy-Item data/places_cache.json data/places_cache.public.json
```

Ensure the file contains **no API keys**, only restaurant JSON.

---

## 2. Initialize Git

```powershell
cd "c:\Users\User\Documents\code\python程式期末專案_美食系統"
git init
git branch -M main
```

### Safety check before commit

```powershell
git status --short --ignored
```

**Do not commit:** `.env`, `data/places_cache.json`, internal docs (`AGENTS.md`, `TASKS.md`, `AI_HANDOFF.md`, etc.).

**Do commit:** `src/`, `tests/`, `scripts/`, `requirements.txt`, `README.md`, `README.zh-TW.md`, `docs/`, `data/places_cache.public.json` (if created).

```powershell
git add README.md README.zh-TW.md PRD.md requirements.txt .gitignore
git add src tests scripts .github docs
git add data/places_cache.public.json
git status
git commit -m "feat: NIU food map Streamlit demo for cloud deploy"
```

---

## 3. GitHub repo + push

1. Create empty repo on GitHub (e.g. `niu-foodmap`), Public.  
2. Push:

**boson316:**

```powershell
git remote add origin git@github-boson316:boson316/niu-foodmap.git
git push -u origin main
```

**b1443204-niu:**

```powershell
git remote add origin git@github-b1443204:b1443204-niu/niu-foodmap.git
git push -u origin main
```

---

## 4. Streamlit Community Cloud

1. https://share.streamlit.io → Sign in with GitHub  
2. **Create app**  
3. Settings:

| Field | Value |
|-------|--------|
| Repository | `your-account/niu-foodmap` |
| Branch | `main` |
| Main file path | `src/streamlit_app.py` |

4. **Deploy** — URL like `https://niu-foodmap.streamlit.app`

**Secrets:** Not required for normal operation (JSON cache). Add `GOOGLE_MAPS_API_KEY` only if re-fetching Places on the server.

---

## 5. Post-deploy checks

- List loads with enough restaurants  
- Row select → map highlights restaurant  
- Wheel tab spins and opens Google Maps  
- Mobile layout OK  

---

## 6. Share with students

Copy Streamlit URL → generate QR → department / clubs / LINE groups.

---

## 7. Updates

```powershell
git add <files>
git commit -m "fix: describe change"
git push
```

Streamlit Cloud redeploys automatically.

---

*Version: 2026-06-13*
