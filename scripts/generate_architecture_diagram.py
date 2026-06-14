"""Generate polished system architecture diagram PNG."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images" / "architecture_diagram.png"

NAVY = "#1A365D"
ORANGE = "#E86C00"
WHITE = "#FFFFFF"
LIGHT_BG = "#F5F7FA"
BLUE_LIGHT = "#E8F0FE"
BLUE_MID = "#4A7FC1"
GREEN_LIGHT = "#E6F4EA"
GREEN_MID = "#3D8B5F"
PURPLE_LIGHT = "#F3E8FF"
PURPLE_MID = "#7C5CBF"
GRAY_BORDER = "#CBD5E1"
TEXT_DARK = "#1E293B"
TEXT_MUTED = "#64748B"
FONT = ["Microsoft JhengHei", "Microsoft YaHei", "SimHei", "sans-serif"]

LANE_LABELS: list[tuple[str, float, float]] = []


def _box(ax, x, y, w, h, face, edge, *, lw=1.5, zorder=2, rs=0.1):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad=0.012,rounding_size={rs}",
        linewidth=lw, edgecolor=edge, facecolor=face, zorder=zorder,
    ))


def _txt(ax, x, y, text, *, size=11, bold=True, color=TEXT_DARK, ha="center", va="center", zorder=10):
    ax.text(
        x, y, text, ha=ha, va=va, fontsize=size,
        fontweight="bold" if bold else "normal", color=color, zorder=zorder,
    )


def _arrow(ax, x1, y1, x2, y2, *, color=GRAY_BORDER, rad=0.0, zorder=1):
    style = "arc3,rad=0" if rad == 0 else f"arc3,rad={rad}"
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13,
        linewidth=2.0, color=color, zorder=zorder,
        shrinkA=0, shrinkB=0,
        connectionstyle=style,
    ))


def _card(ax, cx, cy, w, h, face, edge, title, subtitle="", title_size=11, sub_size=8.5):
    x, y = cx - w / 2, cy - h / 2
    _box(ax, x, y, w, h, face, edge)
    if subtitle:
        _txt(ax, cx, cy + h * 0.14, title, size=title_size)
        _txt(ax, cx, cy - h * 0.18, subtitle, size=sub_size, bold=False, color=TEXT_MUTED)
    else:
        _txt(ax, cx, cy, title, size=title_size)
    return cx, cy, w, h


def _lane(ax, y, h, title):
    _box(ax, 0.5, y, 17.0, h, WHITE, GRAY_BORDER, lw=1.0, zorder=0, rs=0.16)
    LANE_LABELS.append((title, y + h - 0.08))


def _draw_lane_labels(ax):
    for title, label_y in LANE_LABELS:
        ax.text(
            0.9, label_y, title,
            ha="left", va="top", fontsize=10, fontweight="bold", color=TEXT_MUTED,
            zorder=30,
            bbox=dict(boxstyle="round,pad=0.25", facecolor=WHITE, edgecolor=GRAY_BORDER, linewidth=0.8),
        )


def build() -> Path:
    global LANE_LABELS
    LANE_LABELS = []

    fig, ax = plt.subplots(figsize=(18, 12), dpi=220)
    fig.patch.set_facecolor(LIGHT_BG)
    ax.set_facecolor(LIGHT_BG)
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 12)
    ax.axis("off")

    _box(ax, 0.5, 10.85, 17.0, 0.95, NAVY, NAVY)
    _txt(ax, 9, 11.45, "校園附近美食地圖 — 系統架構與資料流", size=22, color=WHITE)
    _txt(ax, 9, 11.05, "國立宜蘭大學 · Python 期末專題", size=11, bold=False, color="#AACCFF")

    _lane(ax, 8.25, 2.45, "資料來源層")
    _lane(ax, 5.05, 3.05, "核心服務層")
    _lane(ax, 1.05, 3.75, "呈現層")

    src_w, src_h = 4.0, 0.72
    google_y = 9.72
    cache_y = 8.62
    cache_h = 0.58

    _card(ax, 3.2, google_y, src_w, src_h, BLUE_LIGHT, BLUE_MID,
          "Google Places API", "fetch 一次")
    _card(ax, 3.2, cache_y, 4.2, cache_h, "#FFF7ED", ORANGE,
          "data/places_cache.json", "本機 ~100 筆", title_size=10, sub_size=8)

    _arrow(ax, 3.2, google_y - src_h / 2 - 0.02, 3.2, cache_y + cache_h / 2 + 0.02, color=ORANGE)

    _card(ax, 9.0, google_y, src_w, src_h, GREEN_LIGHT, GREEN_MID,
          "places_cache.public.json", "雲端快取")
    _card(ax, 14.8, google_y, src_w, src_h, PURPLE_LIGHT, PURPLE_MID,
          "sample_restaurants.json", "Mock 15 筆")

    prov_y = 7.55
    _card(ax, 9.0, prov_y, 6.5, 0.72, "#DBEAFE", NAVY,
          "MockRestaurantProvider", "統一讀取 JSON 陣列", title_size=12)

    _arrow(ax, 3.2, cache_y - cache_h / 2 - 0.02, 6.2, prov_y + 0.38, rad=-0.08)
    _arrow(ax, 9.0, google_y - src_h / 2 - 0.02, 9.0, prov_y + 0.38)
    _arrow(ax, 14.8, google_y - src_h / 2 - 0.02, 11.8, prov_y + 0.38, rad=0.08)

    svc_y = 6.45
    svc_w = 9.8
    svc_cx = 8.0
    _card(ax, svc_cx, svc_y, svc_w, 0.72, "#EFF6FF", NAVY,
          "FoodMapService.rank_nearby()", "依中心座標 + 半徑篩選，回傳排序後餐廳清單", title_size=12.5)
    _arrow(ax, 9.0, prov_y - 0.38, svc_cx, svc_y + 0.38)

    pipe_y = 5.55
    pipe_w, pipe_h = 1.55, 0.82
    steps = ["bbox\n粗篩", "haversine\n距離", "評分\n算法", "heapq\ntop-k"]
    xs = [2.8, 5.6, 8.4, 11.2]

    for x, label in zip(xs, steps):
        _card(ax, x, pipe_y, pipe_w, pipe_h, WHITE, BLUE_MID, label, title_size=9.5)

    gap = 0.28
    for i in range(3):
        _arrow(
            ax,
            xs[i] + pipe_w / 2 + gap / 2, pipe_y,
            xs[i + 1] - pipe_w / 2 - gap / 2, pipe_y,
            color=BLUE_MID,
        )

    score_y = 4.15
    score_h = 0.72
    _card(ax, 8.4, score_y, 2.9, score_h, "#FFF7ED", ORANGE,
          "scoring.py", "貝氏 · 黃氏 · 綜合分", title_size=10)
    _arrow(ax, 8.4, pipe_y - pipe_h / 2 - 0.02, 8.4, score_y + score_h / 2 + 0.02, color=ORANGE)

    _arrow(ax, svc_cx, svc_y - 0.38, svc_cx, pipe_y + pipe_h / 2 + 0.02, color=BLUE_MID)

    ui_y = 3.05
    _card(ax, 4.5, ui_y, 5.0, 1.05, "#F0FDF4", GREEN_MID, "CLI", "table / json 輸出", title_size=15)
    _card(ax, 12.5, ui_y, 7.5, 1.05, "#FAF5FF", PURPLE_MID,
          "Streamlit 雙分頁", "Web 互動介面", title_size=15)

    tab_y = 1.75
    _card(ax, 10.8, tab_y, 3.2, 0.78, PURPLE_LIGHT, PURPLE_MID,
          "美食地圖", "表格 + PyDeck 地圖", title_size=11)
    _card(ax, 14.8, tab_y, 3.2, 0.78, PURPLE_LIGHT, PURPLE_MID,
          "轉盤選擇", "綜合分 Top 30", title_size=11)

    _arrow(ax, xs[0], pipe_y - pipe_h / 2 - 0.02, 4.5, ui_y + 0.55, rad=-0.16)
    _arrow(ax, xs[3], pipe_y - pipe_h / 2 - 0.02, 12.5, ui_y + 0.55)
    _arrow(ax, 11.0, ui_y - 0.55, 10.8, tab_y + 0.42, rad=-0.12)
    _arrow(ax, 14.0, ui_y - 0.55, 14.8, tab_y + 0.42, rad=0.12)

    _box(ax, 0.75, 1.48, 6.2, 0.88, "#FFF7ED", ORANGE, lw=1.5)
    _txt(ax, 3.85, 1.96, "原則：只抓取 Google Cloud API", size=9.5, color=ORANGE)
    _txt(ax, 3.85, 1.66, "一次 100 筆資料，以 Json 儲存為主", size=9.5, color=ORANGE)

    _draw_lane_labels(ax)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.sans-serif"] = FONT
    plt.rcParams["axes.unicode_minus"] = False
    fig.savefig(OUT, bbox_inches="tight", facecolor=LIGHT_BG, pad_inches=0.12)
    plt.close(fig)
    return OUT


if __name__ == "__main__":
    print(f"Generated: {build()}")
