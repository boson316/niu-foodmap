# Streamlit Cloud × GitHub 部署步驟（宜大美食地圖）

**Languages:** [English](streamlit-cloud-deploy.md) · [中文](streamlit-cloud-部署步驟.md)

> 目標：期末 demo 用**免費** Streamlit Community Cloud 上線，網址可貼系上／社團／LINE。

---

## 0. 部署前檢查（本機）

```powershell
cd "c:\Users\User\Documents\code\python程式期末專案_美食系統"
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m pytest -q
streamlit run src/streamlit_app.py
```

瀏覽器開 `http://localhost:8501`，確認「美食地圖」「轉盤選擇」都正常。

---

## 1. 決定三件事

| 項目 | 建議 |
|------|------|
| **GitHub 帳號** | `boson316` 或 `b1443204-niu`（學校／個人擇一；見工作區 `SSH_GIT.md`） |
| **Repo 公開／私人** | 期末繳交、給同學掃 QR → **Public** 較方便 |
| **雲端資料筆數** | 見下方「資料策略」 |

### 資料策略（重要）

| 檔案 | Git | 雲端效果 |
|------|-----|----------|
| `data/places_cache.json` | ❌ 已在 `.gitignore` | 不會上傳 |
| `data/places_cache.public.json` | ✅ 可 commit | 雲端約 100 家（推薦 demo） |
| 兩者都沒有 | — | 只用內建 15 筆範例 |

**若要雲端也有 ~100 家（推薦）：**

```powershell
cd "c:\Users\User\Documents\code\python程式期末專案_美食系統"
Copy-Item data/places_cache.json data/places_cache.public.json
```

確認檔案內**沒有** API Key，只有餐廳 JSON。

---

## 2. 第一次建立 Git（專案目錄內）

```powershell
cd "c:\Users\User\Documents\code\python程式期末專案_美食系統"
git init
git branch -M main
```

### 上傳前安全檢查（必做）

```powershell
git status --short --ignored
```

**不要 commit：**

- `.env`、`GOOGLE_MAPS_API_KEY`
- `data/places_cache.json`（私人快取）
- `AGENTS.md`、`TASKS.md`、`KPI.md`、`CI_GATES.md`、`BENCHMARK.md`、`AI_HANDOFF.md`（內部用）
- `筆記.txt`、`next_actions.md`、`weekly_review.md`、`risk_register.md`

**應該 commit：**

- `src/`、`tests/`、`scripts/`、`requirements.txt`
- `README.md`、`README.zh-TW.md`、`PRD.md`（簡版即可）
- `.github/workflows/`（CI）
- `data/places_cache.public.json`（若有複製）
- `docs/`（含本文件）

### 第一次 commit

```powershell
git add README.md README.zh-TW.md PRD.md requirements.txt .gitignore
git add src tests scripts .github docs
git add data/places_cache.public.json
git status
```

`git status` 確認**沒有** `.env`、`places_cache.json`、內部 md 後：

```powershell
git commit -m "feat: 宜大美食地圖 Streamlit demo，準備雲端部署"
```

---

## 3. 建立 GitHub Repo 並 Push

### 3a. 在 GitHub 網頁

1. 登入 https://github.com  
2. **New repository**  
3. Repository name 例：`niu-foodmap` 或 `yilan-foodmap`  
4. **Public**（或 Private，Streamlit 也支援）  
5. **不要**勾選 Add README（本機已有）  
6. Create repository  

### 3b. 本機連線並推送

**帳號 `boson316`：**

```powershell
git remote add origin git@github-boson316:boson316/niu-foodmap.git
git push -u origin main
```

**帳號 `b1443204-niu`：**

```powershell
git remote add origin git@github-b1443204:b1443204-niu/niu-foodmap.git
git push -u origin main
```

> 若 SSH 失敗，見工作區根目錄 `SSH_GIT.md` 設定 `github-boson316` / `github-b1443204` Host。

---

## 4. Streamlit Community Cloud 部署

1. 開啟 https://share.streamlit.io  
2. **Sign in with GitHub**（授權讀取 repo）  
3. **Create app**  
4. 填寫：

| 欄位 | 值 |
|------|-----|
| Repository | 你的帳號/`niu-foodmap` |
| Branch | `main` |
| Main file path | `src/streamlit_app.py` |
| App URL（可選） | 例：`niu-foodmap` → `https://niu-foodmap.streamlit.app` |

5. **Advanced settings**（通常不用改）  
   - Python 3.10+  
   - 依賴：根目錄 `requirements.txt`  
6. **Deploy**

### Secrets（通常不需要）

日常運作讀 JSON 快取，**不必**設 `GOOGLE_MAPS_API_KEY`。

僅在雲端要「重新抓 Google 資料」時，於 Streamlit → Settings → Secrets 加入：

```toml
GOOGLE_MAPS_API_KEY = "你的金鑰"
```

---

## 5. 部署後驗收

- [ ] 首頁標題「國立宜蘭大學 校園美食地圖」  
- [ ] 清單有資料（有 `places_cache.public.json` 應 ≥50 筆）  
- [ ] 點表格列 → 地圖黃點定位  
- [ ] 「轉盤選擇」可轉、結果可開 Google Maps  
- [ ] 手機瀏覽器開啟版面正常  

---

## 6. 推廣給宜大學生

1. 複製 Streamlit 網址，例：`https://niu-foodmap.streamlit.app`  
2. 用 https://www.qrcode-monkey.com 或類似工具產 QR  
3. 貼到系上海報、社團、LINE 群  

一句話介紹：

> 宜大周邊美食地圖：依綜合分數排序 + 轉盤幫你決定今天吃什麼。

---

## 7. 之後更新程式

```powershell
cd "c:\Users\User\Documents\code\python程式期末專案_美食系統"
# 改完 code、pytest 綠燈後
git add <變更檔案>
git commit -m "fix: 說明這次改了什麼"
git push
```

Streamlit Cloud 會**自動重新部署**（約 1～3 分鐘）。

---

## 常見錯誤

| 現象 | 原因 | 解法 |
|------|------|------|
| 雲端只有 15 家店 | 沒有 `places_cache.public.json` | 見「資料策略」複製並 push |
| `ModuleNotFoundError: foodmap` | Main file 路徑錯 | 確認填 `src/streamlit_app.py` |
| 地圖空白 | pydeck 需網路 | 正常，等幾秒；換瀏覽器試 |
| push 被拒 | SSH 帳號錯 | 檢查 `git remote -v` Host |
| 不小心 push Key | commit 含 `.env` | 立即撤銷金鑰、重寫 history 或刪 repo 重建 |

---

## 檢查清單（繳交／demo 前）

- [ ] 本機 `pytest -q` 綠燈  
- [ ] `git status` 無 `.env`、無 `places_cache.json`  
- [ ] GitHub repo 可開、README 可讀  
- [ ] Streamlit 公開網址可開  
- [ ] 手機測過一輪  

---

*文件版本：2026-06-13*
