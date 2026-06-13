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
- **離線資料**：`src/foodmap/data/sample_restaurants.json`（15 筆範例，名稱虛構）。
- **輸入防護**：自訂 JSON 上限 5 MiB、最多 10,000 筆，欄位與數值範圍驗證（見 `foodmap/validation.py`）。
- **Streamlit**：表格 + 點位圖；中心可由側欄或 `CAMPUS_LAT`／`CAMPUS_LON` 覆寫。

### 安裝與測試

```powershell
cd python程式期末專案_美食系統
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
pytest -q --cov=src --cov-fail-under=70
```

### CLI

```powershell
$env:PYTHONPATH = "src"
python -m foodmap search --lat 24.7464 --lon 121.7457 --radius 2.0 --sort composite --format table
python -m foodmap search --lat 24.7464 --lon 121.7457 --radius 2.0 --format json
```

### Demo 腳本（給老師）

```powershell
cd python程式期末專案_美食系統
$env:PYTHONPATH = "src"

# 1) 宜大校門口 1km 內，綜合排序
python -m foodmap search --lat 24.7464 --lon 121.7457 --radius 1.0 --sort composite

# 2) 最少評論 100 → 濾掉少評論店
python -m foodmap search --lat 24.7464 --lon 121.7457 --radius 1.0 --min-reviews 100

# 3) 半徑 5km 才出現遠距範例
python -m foodmap search --lat 24.7464 --lon 121.7457 --radius 5.0 --sort distance

# 4) 網頁版
streamlit run src/streamlit_app.py
```

### 自訂 JSON 欄位

| 欄位 | 必填 | 說明 |
|------|------|------|
| `id` | ✓ | 字串 ID |
| `name` | ✓ | 店名 |
| `lat` / `lon` | ✓ | WGS84 緯經度 |
| `rating` | ✓ | 平均星等 0～5 |
| `review_count` | ✓ | 評論數（整數 ≥0） |
| `category` | | 字串，可空 |
| `price_level` | | 1～4 或省略 |

`json` 輸出含 `distance_km`、`bayesian_rating`、`huang_rating`、`composite_score`、`maps_url`。

### 進階：Google Places 快取

```powershell
$env:PYTHONPATH = "src"
$env:GOOGLE_MAPS_API_KEY = "你的金鑰"
python scripts/fetch_places_to_json.py --lat 24.7464 --lon 121.7457 --radius-m 3000 --max-pages 10 --out data/places_cache.json
python -m foodmap search --lat 24.7464 --lon 121.7457 --radius 2.0 --data data/places_cache.json --sort huang --limit 20
streamlit run src/streamlit_app.py
```

快取檔存在時 Streamlit 會自動載入 `data/places_cache.json`（已列入 `.gitignore`）。

效能路徑：bbox 粗篩 → haversine → `heapq` top-k。

---

## project_bootstrap（範本說明）

詳見 [README.md](README.md) 英文版「project_bootstrap」章節。
