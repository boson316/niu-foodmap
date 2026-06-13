from __future__ import annotations

import html
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import pydeck as pdk
import streamlit as st
import streamlit.components.v1 as components

from foodmap.providers import MockRestaurantProvider
from foodmap.integrity import CoreIntegrityError, author_notice, verify_core_modules
from foodmap.service import FoodMapService, SortMode
from foodmap.wheel import build_wheel_html

_TIER_LABEL = {"low": "低", "medium": "普通", "high": "高"}
_WHEEL_TOP_N = 30

_MOBILE_CSS = """
<style>
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1100px; }
@media (max-width: 768px) {
  .block-container { padding-left: 0.85rem; padding-right: 0.85rem; }
  [data-testid="stSidebar"] { min-width: 280px !important; }
  h1 { font-size: 1.45rem !important; }
  h2, h3 { font-size: 1.1rem !important; }
}
div[data-testid="stTabs"] button { min-height: 44px; font-size: 0.95rem; }
</style>
"""


def _default_data_path() -> str:
    data_dir = _ROOT.parent / "data"
    for filename in ("places_cache.json", "places_cache.public.json"):
        cache = data_dir / filename
        if cache.is_file():
            return str(cache)
    return ""


def _default_campus() -> tuple[float, float]:
    lat = float(os.environ.get("CAMPUS_LAT", "24.7464"))
    lon = float(os.environ.get("CAMPUS_LON", "121.7457"))
    return lat, lon


def _geocode_place_name(query: str) -> tuple[float, float] | None:
    """OpenStreetMap Nominatim（免 API Key；請勿高頻呼叫）。"""
    q = query.strip()
    if not q:
        return None
    params = urllib.parse.urlencode(
        {"q": q, "format": "json", "limit": 1, "countrycodes": "tw"}
    )
    req = urllib.request.Request(
        f"https://nominatim.openstreetmap.org/search?{params}",
        headers={"User-Agent": "niu-foodmap-streamlit/1.0 (school project demo)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            rows = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return None
    if not isinstance(rows, list) or not rows:
        return None
    return float(rows[0]["lat"]), float(rows[0]["lon"])


@st.cache_data(show_spinner=False)
def _build_service(data_path_str: str) -> FoodMapService:
    json_path = Path(data_path_str) if data_path_str else None
    provider = MockRestaurantProvider(json_path=json_path) if json_path else MockRestaurantProvider()
    return FoodMapService(provider)


_DISPLAY_COLUMNS = (
    "店名",
    "距離",
    "Google 評分",
    "評論數",
    "平均消費",
    "貝氏星等",
    "黃氏星等",
    "綜合分數",
    "星等分級",
    "Google Maps",
    "分類",
)

_MAP_STYLE = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"
_GOOGLE_PIN = [234, 67, 53, 220]
_CAMPUS_PIN = [26, 115, 232, 235]
_HIGHLIGHT_PIN = [251, 188, 5, 255]


def _ordered_rows(df: pd.DataFrame, *, sort_by: str) -> pd.DataFrame:
    if sort_by == "distance":
        return df.sort_values("distance_m", ascending=True, kind="mergesort")
    if sort_by == "huang":
        return df.sort_values("huang_rating", ascending=False, kind="mergesort")
    if sort_by == "rating":
        return df.sort_values("bayesian_rating", ascending=False, kind="mergesort")
    return df.sort_values("composite_score", ascending=False, kind="mergesort")


def _build_display_table(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "店名": df["name"],
            "距離": df["distance_display"],
            "Google 評分": df["rating"],
            "評論數": df["review_count"],
            "平均消費": df["avg_spend_display"],
            "貝氏星等": df["bayesian_rating"],
            "黃氏星等": df["huang_rating"],
            "綜合分數": df["composite_score"],
            "星等分級": df["rating_tier"].map(lambda t: _TIER_LABEL.get(str(t), str(t))),
            "Google Maps": df["maps_url"],
            "分類": df["category"],
        }
    )


def _pick_focus_row(ordered: pd.DataFrame) -> pd.Series | None:
    options = ["（點選表格列或此處選店）", *ordered["name"].tolist()]
    selected_name = st.selectbox(
        "在地圖查看",
        options=options,
        key="map_focus_select",
    )
    if selected_name == options[0]:
        return None
    match = ordered.index[ordered["name"] == selected_name]
    if len(match) == 0:
        return None
    return ordered.loc[match[0]]


def _render_list_table(df: pd.DataFrame, *, sort_by: str) -> pd.DataFrame:
    ordered = _ordered_rows(df, sort_by=sort_by).reset_index(drop=True)
    table = _build_display_table(ordered)
    st.caption("點選表格某一列 → 下方地圖定位並顯示 Google 評分；📖 可開啟 Google Maps 看完整評價。")
    pick_event = st.dataframe(
        table,
        column_order=list(_DISPLAY_COLUMNS),
        column_config={
            "店名": st.column_config.TextColumn("店名", width="medium"),
            "距離": st.column_config.TextColumn("距離", width="small"),
            "Google 評分": st.column_config.NumberColumn("Google 評分", format="%.1f", width="small"),
            "評論數": st.column_config.NumberColumn("評論數", format="%d", width="small"),
            "平均消費": st.column_config.TextColumn("平均消費", width="small"),
            "貝氏星等": st.column_config.NumberColumn("貝氏星等", format="%.2f", width="small"),
            "黃氏星等": st.column_config.NumberColumn("黃氏星等", format="%.2f", width="small"),
            "綜合分數": st.column_config.NumberColumn("綜合分數", format="%.4f", width="small"),
            "星等分級": st.column_config.TextColumn("星等分級", width="small"),
            "Google Maps": st.column_config.LinkColumn(
                "Google Maps",
                display_text="📖 開啟",
                width="small",
            ),
            "分類": st.column_config.TextColumn("分類", width="small"),
        },
        on_select="rerun",
        selection_mode="single-row",
        width="stretch",
        hide_index=True,
        key="restaurant_table_pick",
    )
    if pick_event.selection.rows:
        return ordered.iloc[int(pick_event.selection.rows[0])]
    return _pick_focus_row(ordered)


def _render_focus_card(row: pd.Series) -> None:
    st.markdown(
        f"""
<div style="padding:0.9rem 1rem;border:1px solid #dadce0;border-radius:12px;background:#fff;
box-shadow:0 1px 3px rgba(60,64,67,.15);margin-bottom:0.75rem;">
  <div style="font-size:1.05rem;font-weight:700;color:#202124;">{html.escape(str(row["name"]))}</div>
  <div style="margin-top:0.35rem;color:#5f6368;font-size:0.92rem;">
    Google 評分 <strong style="color:#f4b400;">★ {row["rating"]:.1f}</strong>
    （{int(row["review_count"])} 則評論）　平均消費 {row["avg_spend_display"]}　距離 {row["distance_display"]}
  </div>
  <div style="margin-top:0.25rem;color:#5f6368;font-size:0.88rem;">
    黃氏星等 {row["huang_rating"]:.2f}　綜合分數 {row["composite_score"]:.4f}
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button("在 Google Maps 查看評價與導航", row["maps_url"], type="primary")


def _render_map(
    *,
    restaurants: pd.DataFrame,
    center_lat: float,
    center_lon: float,
    focus_row: pd.Series | None,
) -> None:
    map_df = restaurants.copy()
    if focus_row is not None:
        map_df["selected"] = map_df["id"] == focus_row["id"]
        map_center_lat = float(focus_row["lat"])
        map_center_lon = float(focus_row["lon"])
        zoom = 15
    else:
        map_df["selected"] = False
        map_center_lat = center_lat
        map_center_lon = center_lon
        zoom = 13

    map_df["tooltip_html"] = map_df.apply(
        lambda r: (
            f"<b>{r['name']}</b><br/>"
            f"★ {r['rating']:.1f}（{int(r['review_count'])} 則）<br/>"
            f"{r['distance_display']}"
        ),
        axis=1,
    )

    base_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df[~map_df["selected"]],
        get_position=["lon", "lat"],
        get_fill_color=_GOOGLE_PIN,
        get_radius=80,
        pickable=True,
    )
    focus_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df[map_df["selected"]],
        get_position=["lon", "lat"],
        get_fill_color=_HIGHLIGHT_PIN,
        get_radius=130,
        pickable=True,
    )
    center_layer = pdk.Layer(
        "ScatterplotLayer",
        data=pd.DataFrame({"lat": [center_lat], "lon": [center_lon], "name": ["宜大校本部"]}),
        get_position=["lon", "lat"],
        get_fill_color=_CAMPUS_PIN,
        get_radius=100,
        pickable=True,
    )
    layers = [base_layer, center_layer]
    if focus_row is not None and not map_df[map_df["selected"]].empty:
        layers.insert(1, focus_layer)
    elif focus_row is not None:
        layers.append(focus_layer)

    view = pdk.ViewState(latitude=map_center_lat, longitude=map_center_lon, zoom=zoom, pitch=0)
    deck = pdk.Deck(
        map_style=_MAP_STYLE,
        layers=layers,
        initial_view_state=view,
        tooltip={"html": "{tooltip_html}", "style": {"color": "white", "fontSize": "12px"}},
    )
    st.pydeck_chart(deck, width="stretch")


def _render_score_guide() -> None:
    st.subheader("綜合分數")
    st.markdown(
        """
**預設排序依據** — 兩段相乘：

```
綜合分數 = 黃氏星等 × exp(-距離_km / 0.6)
```

**黃氏星等**（Reputation）：

```
huang = rating × 分級係數 × (0.5 + 0.5×rating/5) × (0.4 + 0.6×log1p(評論數)/log1p(500))
```

- 星越高、評論越多 → 黃氏越高（500 則評論飽和）
- 例：Muze 4.8 / 13128 則 → 黃氏 **5.88**；復興路炸醬麵 宜蘭 4.9 / 394 則 → 黃氏 **5.92**（星高但評論少，黃氏略低）

**距離衰減**（decay_km = 0.6）：

- 369 m → `exp(-0.369/0.6) ≈ 0.54` → Muze 綜合 **3.18**
- 361 m、黃氏 5.92 → 綜合 **2.97**

同樣高星，**近 + 評論多**的店會排前面。側欄可改排序；表格欄位標題也可再點擊重排。
        """
    )
    with st.expander("其他指標：貝氏星等、星等分級"):
        st.markdown(
            """
**貝氏星等** — 把 Google 評分與評論數一起算「較可信」平均；評論越少，極端分數越往整體平均拉。側欄選「貝氏星等」排序時使用。

**星等分級** — 依 Google 評分分三檔，作為黃氏公式的係數：低（&lt;2.5，×0.65）、普通（2.5～4.0，×1.0）、高（≥4.0，×1.25）。
            """
        )


def _render_wheel_selector(df: pd.DataFrame) -> None:
    wheel_df = (
        df.sort_values("composite_score", ascending=False, kind="mergesort")
        .head(_WHEEL_TOP_N)
        .reset_index(drop=True)
    )
    if wheel_df.empty:
        st.warning("沒有符合條件的餐廳可放入轉盤。")
        return

    st.caption(f"候選名單：綜合分數 Top {len(wheel_df)}（評價 + 距離，依側欄半徑與評論門檻）")
    with st.expander("查看候選清單", expanded=False):
        st.dataframe(
            wheel_df[
                [
                    "name",
                    "composite_score",
                    "huang_rating",
                    "avg_spend_display",
                    "distance_display",
                    "rating",
                    "review_count",
                ]
            ].rename(
                columns={
                    "name": "店名",
                    "composite_score": "綜合分數",
                    "huang_rating": "黃氏星等",
                    "avg_spend_display": "平均消費",
                    "distance_display": "距離",
                    "rating": "Google 評分",
                    "review_count": "評論數",
                }
            ),
            hide_index=True,
            width="stretch",
        )

    wheel_items = wheel_df[
        ["name", "composite_score", "huang_rating", "distance_display", "maps_url"]
    ].to_dict(orient="records")
    components.html(build_wheel_html(wheel_items), height=920, scrolling=True)


def run() -> None:
    st.set_page_config(
        page_title="宜大美食地圖",
        page_icon="🍜",
        layout="wide",
        initial_sidebar_state="auto",
    )
    try:
        verify_core_modules()
    except CoreIntegrityError as exc:
        st.error(str(exc))
        st.caption(author_notice())
        st.stop()
    st.markdown(_MOBILE_CSS, unsafe_allow_html=True)
    default_data = _default_data_path()
    using_cache = bool(default_data)
    lat0, lon0 = _default_campus()

    if "campus_lat" not in st.session_state:
        st.session_state.campus_lat = lat0
    if "campus_lon" not in st.session_state:
        st.session_state.campus_lon = lon0

    st.title("國立宜蘭大學 校園美食地圖")
    st.caption(
        "中心點預設：宜大校本部（24.7464, 121.7457）。"
        "綜合分 = 黃氏星等（分級×星分×評論量）× 距離衰減。"
        + ("已載入 Google Places 快取。" if using_cache else "使用內建範例 JSON。")
    )

    with st.sidebar:
        st.header("條件")
        with st.expander("用地名設定中心（可選）", expanded=False):
            st.caption("使用 OpenStreetMap 查座標，免 Google API；網路需連線，約 1 秒 1 次。")
            place_query = st.text_input("輸入地名", placeholder="例：國立宜蘭大學")
            if st.button("查詢並設為中心", key="geocode_btn"):
                coords = _geocode_place_name(place_query)
                if coords is None:
                    st.error("找不到地點，請換關鍵字（可加「宜蘭」）。")
                else:
                    st.session_state.campus_lat = coords[0]
                    st.session_state.campus_lon = coords[1]
                    st.success(f"已設定：{place_query} → ({coords[0]:.6f}, {coords[1]:.6f})")
                    st.rerun()

        lat = st.number_input("校園中心緯度", format="%.6f", key="campus_lat")
        lon = st.number_input("校園中心經度", format="%.6f", key="campus_lon")
        radius = st.slider("搜尋半徑（公里）", min_value=0.3, max_value=5.0, value=2.0, step=0.1)
        min_reviews = st.number_input("最少評論數", min_value=0, value=0, step=1)
        sort_by = st.selectbox(
            "排序方式",
            options=("huang", "composite", "rating", "distance"),
            format_func=lambda x: {
                "huang": "黃氏星等（高到低）",
                "composite": "綜合（推薦）",
                "rating": "貝氏星等（高到低）",
                "distance": "距離（近到遠）",
            }[x],
        )
        limit = st.slider("最多顯示筆數", min_value=5, max_value=100, value=50, step=5)
        data_path = st.text_input("自訂 JSON 路徑（可留空）", value=default_data)

    service = _build_service(data_path.strip())
    sort_mode: SortMode = sort_by  # type: ignore[assignment]

    rows = service.rank_nearby(
        center_lat=float(lat),
        center_lon=float(lon),
        radius_km=float(radius),
        min_reviews=int(min_reviews),
        sort_by=sort_mode,
        limit=int(limit),
    )
    payload = FoodMapService.to_public_dict(rows)

    if not payload:
        st.warning("沒有符合條件的餐廳，請放寬半徑或減少最少評論數。")
        return

    df = pd.DataFrame(payload)
    tab_map, tab_wheel = st.tabs(["🗺️ 美食地圖", "🎡 轉盤選擇"])

    with tab_map:
        st.subheader("清單")
        focus_row = _render_list_table(df, sort_by=sort_by)

        st.subheader("地圖")
        st.caption("淺色街道圖 · 🔵 宜大校本部 · 🔴 餐廳 · 🟡 你選的店")
        if focus_row is not None:
            _render_focus_card(focus_row)
        map_df = df[
            ["id", "name", "lat", "lon", "rating", "review_count", "distance_display"]
        ].copy()
        _render_map(
            restaurants=map_df,
            center_lat=float(lat),
            center_lon=float(lon),
            focus_row=focus_row,
        )
        _render_score_guide()

    with tab_wheel:
        _render_wheel_selector(df)

    st.divider()
    st.caption(author_notice())


if __name__ == "__main__":
    run()
