# python程式期末實作

**Languages:** [English](README.md) · [中文](README.zh-TW.md)

本目錄同時保留 **project_bootstrap** 說明與本學期主題 **校園附近美食地圖**（`src/foodmap/`）。

---

## 校園附近美食地圖｜國立宜蘭大學（Mock JSON + 排序）

### 功能摘要

- 預設校園中心：**國立宜蘭大學校本部**（神農路一段1號），約 `24.7464°N, 121.7457°E`。
- 依**中心緯經度**與**半徑（公里）**篩選；可設**最少評論數**。
- **排序**：`composite`（**黃氏星等 × 距離衰減**，預設）、`rating`（貝氏星等）、`huang`（黃氏星等）、`distance`（由近到遠）。
- **黃氏星等**：1～2 星低／3 星普通／4～5 星高分級 × 星分權重 × 評論量權重；`composite_score = 黃氏 × 距離衰減`。
- **輸入防護**：自訂 JSON 上限 5 MiB、最多 10,000 筆，schema 驗證（`foodmap/validation.py`）。
- **離線資料**：`src/foodmap/data/sample_restaurants.json`，15 筆位置位於宜大周邊的**範例餐廳**（**名稱以「街道＋品項」命名、評分為虛構**，僅供 demo；正式版需替換為實際資料）。
- **Streamlit**：表格 + 點位圖；中心可由側欄或環境變數 `CAMPUS_LAT`、`CAMPUS_LON` 覆寫。

### 安裝與測試

```powershell
cd python程式期末實作
python -m pip install -r requirements.txt
pytest -q --cov=src --cov-fail-under=70
```

### CLI（需將 `src` 加入 `PYTHONPATH`）

PowerShell：

```powershell
$env:PYTHONPATH = "src"
python -m foodmap search --lat 24.7464 --lon 121.7457 --radius 2.0 --sort composite --format table
python -m foodmap search --lat 24.7464 --lon 121.7457 --radius 2.0 --format json
```

### 給老師／Demo 腳本

下列與口頭 demo 對齊：綜合排序、最少評論數過濾、半徑拉大才出現遠距範例、Streamlit。

```powershell
cd python程式期末實作
$env:PYTHONPATH = "src"

# 1) 宜大校門口 1km 內，綜合排序
python -m foodmap search --lat 24.7464 --lon 121.7457 --radius 1.0 --sort composite

# 2) 設「最少評論 100」→ 範例中的「只有三則評論的網紅店」會被濾掉
python -m foodmap search --lat 24.7464 --lon 121.7457 --radius 1.0 --min-reviews 100

# 3) 拉到 5km 才會看到「羅東夜市牛排館」（驗證半徑過濾）
python -m foodmap search --lat 24.7464 --lon 121.7457 --radius 5.0 --sort distance

# 4) 網頁版（側欄已預設宜大座標）
streamlit run src/streamlit_app.py
```

`--data` 可指向自訂 JSON（UTF-8、**最外層為陣列**）。每筆物件欄位：

| 欄位 | 必填 | 說明 |
|------|------|------|
| `id` | ✓ | 字串 ID |
| `name` | ✓ | 店名 |
| `lat` / `lon` | ✓ | WGS84 緯經度 |
| `rating` | ✓ | 平均星等 0～5 |
| `review_count` | ✓ | 評論數（整數 ≥0） |
| `category` | | 字串，可空 |
| `price_level` | | 1～4 或省略 |

`json` 輸出每筆含 `distance_km`、`bayesian_rating`、`huang_rating`、`composite_score`、`maps_url`（Google Maps 以座標開啟）。

### Streamlit

```powershell
$env:PYTHONPATH = "src"
streamlit run src/streamlit_app.py
```

側欄可改中心點、半徑、排序；「自訂 JSON 路徑」留空則用內建範例。

### 進階：真實 API 與上千筆資料

**架構原則（不要每次查詢都打 API）**

1. **離線快取**：`scripts/fetch_places_to_json.py` 用 Google Places API (New) 抓一次 → 存 JSON。
2. **查詢時**：`MockRestaurantProvider(json_path=快取檔)` + `FoodMapService.rank_nearby`（bbox 粗篩 → haversine → `heapq` top-k）。
3. **上千筆**：API 分頁抓滿（`--max-pages`）；若仍不夠，擴大半徑或多次抓取合併 JSON。

**啟用 Google API（一次性）**

1. [Google Cloud Console](https://console.cloud.google.com/) 建立專案 → 啟用 **Places API (New)** → 建立 API Key。
2. 計費帳戶需開啟（有免費額度，超出才收費）。
3. 金鑰限制建議：HTTP referrer（網頁）或 IP（伺服器），勿 commit 到 Git。

```powershell
$env:PYTHONPATH = "src"
$env:GOOGLE_MAPS_API_KEY = "你的金鑰"
python scripts/fetch_places_to_json.py --lat 24.7464 --lon 121.7457 --radius-m 3000 --max-pages 10 --out data/places_cache.json
python -m foodmap search --lat 24.7464 --lon 121.7457 --radius 2.0 --data data/places_cache.json --sort huang --limit 20
streamlit run src/streamlit_app.py
```

`data/places_cache.json` 存在時，Streamlit 側欄會自動帶入該路徑（`.gitignore` 已排除，勿 commit 金鑰或快取）。

**程式內直接接 live API（較少建議）**

```python
from foodmap.providers import GooglePlacesProvider
from foodmap.service import FoodMapService

svc = FoodMapService(GooglePlacesProvider(center_lat=24.7464, center_lon=121.7457, radius_m=2000))
rows = svc.rank_nearby(center_lat=24.7464, center_lon=121.7457, radius_km=2.0, limit=20)
```

**效能路徑（已實作）**

| 步驟 | 複雜度 | 說明 |
|------|--------|------|
| bbox 粗篩 | O(n) | `approx_in_radius_bbox` 排除明顯超出半徑的點 |
| haversine | O(候選) | 中心弧度預計算 `HaversineCenter` |
| top-k | O(n log k) | `heapq.nlargest` / `nsmallest`，k=`limit` |

若 n > 1 萬且常查同一區域，下一步可做 **geohash 網格索引** 或 SQLite R-tree（仍不改 `FoodMapService` 介面）。

---

## project_bootstrap（範本說明）

可一鍵建立新專案：**PRD + TDD（`src/`/`tests/`）+ CI Gate + `slo.config.json` 單一 SLO 來源**。

### 快速建立新專案（推薦）

**工作區根目錄：**

```powershell
.\new-project.ps1 my_app -Title "My App" -Verify
```

**或從本目錄：**

```powershell
python scripts/scaffold.py my_app --title "My App" --verify
```

產物目錄：`..\my_app\`（與 `code/` 同層）

### 建立後目錄

| 類別 | 檔案 |
|------|------|
| SLO 單一來源 | `slo.config.json` |
| 規格 | `PRD.md`, `TASKS.md`, `KPI.md`, `CI_GATES.md`, `AGENTS.md` |
| TDD | `src/app.py`, `src/foodmap/`, `tests/` |
| Gate 腳本 | `scripts/run_benchmark.py`, `evaluate_gates.py`, `slo_sync.py` |
| CI | `.github/workflows/ci-gate.yml` |
| 決策留痕 | `scripts/record_decision.py` → `artifacts/decision_*.md` |

### Day1 驗證（新專案內）

```powershell
cd ..\my_app
python -m pip install -U pytest pytest-cov
pytest -q
python scripts/run_benchmark.py --out artifacts
python scripts/evaluate_gates.py --baseline artifacts/baseline_metrics.json --optimized artifacts/optimized_metrics.json --out artifacts/gate_result.json
```

### 改 SLO（三處門檻一次同步）

1. 只改 `slo.config.json`（`kpi` / `gate` / `benchmark`）
2. 執行：

```powershell
python scripts/slo_sync.py
```

會更新 `PRD.md` 第 4 節、`KPI.md`、`CI_GATES.md`、`AGENTS.md`。  
`evaluate_gates.py` / `run_benchmark.py` **直接讀** `slo.config.json`，不需手改腳本。

### 自訂 SLO 建立

```powershell
.\new-project.ps1 my_app -Slo "D:\path\my-slo.json"
```

`my-slo.json` 只需包含要覆寫的欄位（會與 `slo.defaults.json` 合併）。

### 向後相容

`python scripts/init_project.py <name>` 等同 `scaffold.py`。

### 規格模板（單一來源）

`PRD.md`、`TASKS.md`、`BENCHMARK.md` 即開案模板（原 `templates_模板` 已併入）。

### 新專案 7 天 SOP

- D1: 鎖規格 + 調 `slo.config.json` + `slo_sync` + `pytest -q`
- D2: TDD 紅綠燈（`tests/` → `src/`）
- D3: 指標管線（benchmark artifacts）
- D4: Gate GO/NO-GO
- D5: reliability drill
- D6: CI
- D7: `weekly_review.md` / `risk_register.md` / `next_actions.md`
