# Copyright (c) 2026 Boson Huang. All rights reserved. Unauthorized modification prohibited.
from __future__ import annotations

import json
import math
from typing import Any, Mapping, Sequence

_WHEEL_COLORS = (
    "#FF6B6B",
    "#4ECDC4",
    "#FFE66D",
    "#A8E6CF",
    "#DDA0DD",
    "#87CEEB",
    "#F4A460",
    "#98D8C8",
    "#F7DC6F",
    "#BB8FCE",
)


def _short_label(name: str, *, max_len: int = 10) -> str:
    compact = name.strip()
    if len(compact) <= max_len:
        return compact
    return f"{compact[: max_len - 1]}…"


def spin_alignment_degrees(winner_index: int, segment_count: int) -> float:
    """Absolute rotation (mod 360) placing segment ``winner_index`` under the top pointer."""
    if segment_count <= 0 or not 0 <= winner_index < segment_count:
        raise ValueError("invalid wheel spin indices")
    slice_angle = 360.0 / segment_count
    return (360.0 - winner_index * slice_angle) % 360.0


def spin_delta_degrees(
    current_rotation: float,
    winner_index: int,
    segment_count: int,
    *,
    extra_turns: int = 0,
) -> float:
    """Clockwise delta from ``current_rotation`` so the winner ends under the pointer."""
    current_mod = current_rotation % 360.0
    if current_mod < 0:
        current_mod += 360.0
    target_mod = spin_alignment_degrees(winner_index, segment_count)
    delta = target_mod - current_mod
    if delta <= 0:
        delta += 360.0
    return extra_turns * 360.0 + delta


def segment_index_at_rotation(rotation_deg: float, segment_count: int) -> int:
    """Which segment (0-based) sits under the top pointer after ``rotation_deg`` clockwise."""
    if segment_count <= 0:
        raise ValueError("segment_count must be positive")
    slice_angle = 360.0 / segment_count
    norm = rotation_deg % 360.0
    if norm < 0:
        norm += 360.0
    return int((360.0 - norm + slice_angle / 2.0) // slice_angle) % segment_count


def _polar_xy(cx: float, cy: float, radius: float, angle_from_top_deg: float) -> tuple[float, float]:
    """Polar coords with 0° at 12 o'clock, increasing clockwise."""
    rad = math.radians(angle_from_top_deg - 90.0)
    return cx + radius * math.cos(rad), cy + radius * math.sin(rad)


def _svg_wheel_rotor(segment_count: int) -> str:
    cx = cy = 200.0
    outer_r = 190.0
    slice_angle = 360.0 / segment_count
    large_arc = 1 if slice_angle > 180.0 else 0
    parts: list[str] = []
    for index in range(segment_count):
        center = index * slice_angle
        start = center - slice_angle / 2.0
        end = center + slice_angle / 2.0
        color = _WHEEL_COLORS[index % len(_WHEEL_COLORS)]
        x1, y1 = _polar_xy(cx, cy, outer_r, start)
        x2, y2 = _polar_xy(cx, cy, outer_r, end)
        parts.append(
            f'<path d="M{cx:.2f},{cy:.2f} L{x1:.2f},{y1:.2f} '
            f'A{outer_r:.2f},{outer_r:.2f} 0 {large_arc},1 {x2:.2f},{y2:.2f} Z" fill="{color}"/>'
        )
        tx, ty = _polar_xy(cx, cy, outer_r * 0.62, center)
        parts.append(
            f'<text x="{tx:.2f}" y="{ty:.2f}" text-anchor="middle" '
            f'dominant-baseline="middle" class="wheel-svg-label">{index + 1}</text>'
        )
    return "\n".join(parts)


def build_wheel_html(restaurants: Sequence[Mapping[str, Any]]) -> str:
    """產生可嵌入 Streamlit 的轉盤 HTML（綜合分數候選，等機率抽選）。"""
    if not restaurants:
        return '<p class="wheel-empty">目前沒有可抽選的餐廳。</p>'

    payload = [
        {
            "name": str(item["name"]),
            "composite_score": float(item["composite_score"]),
            "huang_rating": float(item["huang_rating"]),
            "distance_display": str(item["distance_display"]),
            "maps_url": str(item["maps_url"]),
            "short_label": _short_label(str(item["name"])),
        }
        for item in restaurants
    ]
    segment_count = len(payload)
    svg_segments = _svg_wheel_rotor(segment_count)
    data_json = json.dumps(payload, ensure_ascii=False)
    legend_rows = "\n".join(
        f'<li data-index="{index}"><span class="wheel-legend-no">{index + 1}</span>'
        f'<span class="wheel-legend-name">{item["short_label"]}</span>'
        f'<span class="wheel-legend-meta">{item["composite_score"]:.2f}</span></li>'
        for index, item in enumerate(payload)
    )

    return f"""
<style>
.wheel-app {{
  font-family: "Segoe UI", "Noto Sans TC", sans-serif;
  max-width: 620px;
  margin: 0 auto;
  padding: 0.5rem 0 2.5rem;
}}
.wheel-head {{
  text-align: center;
  margin-bottom: 1rem;
}}
.wheel-head h3 {{
  margin: 0 0 0.35rem;
  font-size: clamp(1.15rem, 4vw, 1.45rem);
}}
.wheel-head p {{
  margin: 0;
  color: #5f6368;
  font-size: clamp(0.85rem, 3.2vw, 0.95rem);
  line-height: 1.5;
}}
.wheel-stage {{
  position: relative;
  width: min(94vw, 460px);
  aspect-ratio: 1;
  margin: 0 auto 1rem;
}}
.wheel-pointer {{
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 0;
  height: 0;
  border-left: 14px solid transparent;
  border-right: 14px solid transparent;
  border-top: 26px solid #1a73e8;
  z-index: 3;
  filter: drop-shadow(0 2px 2px rgba(0, 0, 0, 0.2));
}}
.wheel-disc-wrap {{
  position: absolute;
  inset: 0;
  border-radius: 50%;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.16);
  overflow: hidden;
}}
.wheel-svg {{
  width: 100%;
  height: 100%;
  display: block;
}}
#wheel-rotor {{
  transition: transform 4.2s cubic-bezier(0.12, 0.75, 0.08, 1);
  transform-origin: 200px 200px;
}}
.wheel-svg-label {{
  font-family: "Segoe UI", "Noto Sans TC", sans-serif;
  font-size: 18px;
  font-weight: 800;
  fill: #111;
  pointer-events: none;
}}
.wheel-hub-svg {{
  fill: #fff;
  stroke: #1a73e8;
  stroke-width: 4;
}}
.wheel-legend {{
  margin: 0 0 1rem;
  padding: 0.75rem 0.9rem;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  background: #fafafa;
  max-height: 220px;
  overflow-y: auto;
}}
.wheel-legend ul {{
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 0.35rem 0.75rem;
}}
.wheel-legend li {{
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.88rem;
  color: #3c4043;
  border-radius: 8px;
  padding: 0.15rem 0.25rem;
}}
.wheel-legend-active {{
  background: #e8f0fe;
  outline: 1px solid #aecbfa;
}}
.wheel-legend-no {{
  display: inline-flex;
  width: 1.35rem;
  height: 1.35rem;
  border-radius: 999px;
  background: #1a73e8;
  color: #fff;
  font-size: 0.72rem;
  font-weight: 700;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}}
.wheel-legend-name {{
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}}
.wheel-legend-meta {{
  color: #5f6368;
  font-size: 0.78rem;
  flex-shrink: 0;
}}
.wheel-actions {{
  display: flex;
  justify-content: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin: 0 0 1rem;
}}
.wheel-actions-top {{
  margin-top: 0.25rem;
}}
.wheel-btn {{
  min-height: 48px;
  min-width: 148px;
  padding: 0.75rem 1.4rem;
  border: none;
  border-radius: 999px;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
.wheel-btn:disabled {{
  opacity: 0.55;
  cursor: not-allowed;
}}
.wheel-btn-primary {{
  background: linear-gradient(135deg, #1a73e8, #4285f4);
  color: #fff;
  box-shadow: 0 6px 16px rgba(26, 115, 232, 0.35);
}}
.wheel-btn-primary:not(:disabled):active {{
  transform: scale(0.98);
}}
.wheel-btn-ghost {{
  background: #f1f3f4;
  color: #3c4043;
}}
.wheel-result {{
  margin: 0 0 1rem;
  padding: 1rem 1.1rem 1.25rem;
  border-radius: 16px;
  background: linear-gradient(180deg, #f8fbff, #eef4ff);
  border: 1px solid #d2e3fc;
  text-align: center;
  min-height: 6.5rem;
}}
.wheel-result h4 {{
  margin: 0 0 0.35rem;
  font-size: clamp(1rem, 4.2vw, 1.2rem);
  color: #174ea6;
  line-height: 1.4;
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}}
.wheel-result p {{
  margin: 0.2rem 0;
  color: #5f6368;
  font-size: 0.92rem;
}}
.wheel-result a {{
  display: inline-block;
  margin-top: 0.65rem;
  padding: 0.55rem 1rem;
  border-radius: 999px;
  background: #1a73e8;
  color: #fff !important;
  text-decoration: none;
  font-weight: 600;
}}
.wheel-maps-btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-top: 0.75rem;
  padding: 0.8rem 1.35rem;
  min-height: 48px;
  min-width: min(100%, 240px);
  border: none;
  border-radius: 999px;
  background: #1a73e8;
  color: #fff;
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.2;
  cursor: pointer;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  box-shadow: 0 4px 12px rgba(26, 115, 232, 0.35);
}}
.wheel-maps-btn:active {{
  transform: scale(0.98);
}}
.wheel-maps-fallback {{
  margin: 0.65rem 0 0;
  font-size: 0.92rem;
}}
.wheel-maps-fallback a {{
  color: #1a73e8;
  font-weight: 600;
  text-decoration: underline;
}}
@media (max-width: 768px) {{
  .wheel-app {{
    padding-bottom: calc(3.5rem + env(safe-area-inset-bottom, 0px));
  }}
  .wheel-legend {{
    max-height: 180px;
  }}
}}
.wheel-empty {{
  text-align: center;
  color: #5f6368;
}}
</style>
<div class="wheel-app" id="foodmap-wheel-app">
  <div class="wheel-head">
    <h3>今天吃什麼？轉一下就知道</h3>
    <p>轉盤顯示編號；對照表為綜合分數 Top {segment_count}（評價＋距離）。</p>
  </div>
  <div class="wheel-actions wheel-actions-top">
    <button class="wheel-btn wheel-btn-primary" id="wheel-spin-btn" type="button">開始轉盤</button>
    <button class="wheel-btn wheel-btn-ghost" id="wheel-reset-btn" type="button">重置</button>
  </div>
  <div class="wheel-stage" aria-label="餐廳轉盤">
    <div class="wheel-pointer" aria-hidden="true"></div>
    <div class="wheel-disc-wrap">
      <svg class="wheel-svg" viewBox="0 0 400 400" role="img" aria-label="餐廳轉盤盤面">
        <g id="wheel-rotor">
          {svg_segments}
        </g>
        <circle class="wheel-hub-svg" cx="200" cy="200" r="34" />
      </svg>
    </div>
  </div>
  <div class="wheel-result" id="wheel-result" aria-live="polite">
    <p>按下「開始轉盤」，讓命運決定午餐／晚餐。</p>
  </div>
  <div class="wheel-legend" aria-label="轉盤編號對照">
    <ul>{legend_rows}</ul>
  </div>
</div>
<script>
(() => {{
  const restaurants = {data_json};
  const segmentCount = restaurants.length;
  const sliceAngle = 360 / segmentCount;
  const rotor = document.getElementById("wheel-rotor");
  const spinBtn = document.getElementById("wheel-spin-btn");
  const resetBtn = document.getElementById("wheel-reset-btn");
  const result = document.getElementById("wheel-result");
  let rotation = 0;
  let spinning = false;

  function escapeHtml(text) {{
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }}

  function openExternalUrl(url) {{
    try {{
      const link = document.createElement("a");
      link.href = url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.style.display = "none";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      return true;
    }} catch (_err) {{
      /* fall through */
    }}
    try {{
      const root = window.top || window.parent || window;
      const opened = root.open(url, "_blank", "noopener,noreferrer");
      if (opened) {{
        opened.opener = null;
        return true;
      }}
    }} catch (_err) {{
      /* fall through */
    }}
    return false;
  }}

  function openMapsUrl(url) {{
    if (!url) return;
    if (openExternalUrl(url)) return;
    result.insertAdjacentHTML(
      "beforeend",
      `<p class="wheel-maps-fallback"><a href="${{escapeHtml(url)}}" target="_blank" rel="noopener noreferrer">若未自動開啟，請點此開啟 Google Maps</a></p>`
    );
  }}

  function applyRotation() {{
    rotor.style.transform = `rotate(${{rotation}}deg)`;
  }}

  function rotationMod(rot) {{
    return ((rot % 360) + 360) % 360;
  }}

  function segmentAtPointer(rot) {{
    const norm = rotationMod(rot);
    const index = Math.floor((360 - norm + sliceAngle / 2) / sliceAngle) % segmentCount;
    return (index + segmentCount) % segmentCount;
  }}

  function renderWinner(item, winnerIndex) {{
    document.querySelectorAll(".wheel-legend li").forEach((row) => {{
      row.classList.remove("wheel-legend-active");
    }});
    const activeRow = document.querySelector(`.wheel-legend li[data-index="${{winnerIndex}}"]`);
    if (activeRow) {{
      activeRow.classList.add("wheel-legend-active");
    }}
    result.innerHTML = `
      <h4>#${{winnerIndex + 1}} ${{item.name}}</h4>
      <p>綜合分數 <strong>${{item.composite_score.toFixed(2)}}</strong>
        　黃氏 <strong>${{item.huang_rating.toFixed(2)}}</strong>
        　距離 <strong>${{item.distance_display}}</strong></p>
      <button type="button" class="wheel-maps-btn" data-maps-url="${{item.maps_url}}">📖 開啟 Google Maps</button>
    `;
    result.scrollIntoView({{ behavior: "smooth", block: "nearest" }});
  }}

  function spin() {{
    if (spinning) return;
    spinning = true;
    spinBtn.disabled = true;
    result.innerHTML = "<p>轉盤旋轉中…</p>";

    const winnerIndex = Math.floor(Math.random() * segmentCount);
    const extraTurns = 4 + Math.floor(Math.random() * 3);
    const currentMod = rotationMod(rotation);
    const targetMod = rotationMod(360 - winnerIndex * sliceAngle);
    let delta = targetMod - currentMod;
    if (delta <= 0) delta += 360;
    rotation += extraTurns * 360 + delta;
    applyRotation();

    window.setTimeout(() => {{
      const actualIndex = segmentAtPointer(rotation);
      renderWinner(restaurants[actualIndex], actualIndex);
      spinning = false;
      spinBtn.disabled = false;
    }}, 4300);
  }}

  function resetWheel() {{
    if (spinning) return;
    rotation = 0;
    rotor.style.transition = "none";
    applyRotation();
    window.requestAnimationFrame(() => {{
      rotor.style.transition = "";
    }});
    result.innerHTML = "<p>按下「開始轉盤」，讓命運決定午餐／晚餐。</p>";
    document.querySelectorAll(".wheel-legend li").forEach((row) => {{
      row.classList.remove("wheel-legend-active");
    }});
  }}

  spinBtn.addEventListener("click", spin);
  resetBtn.addEventListener("click", resetWheel);
  result.addEventListener("click", (event) => {{
    const mapsBtn = event.target.closest(".wheel-maps-btn");
    if (!mapsBtn) return;
    event.preventDefault();
    openMapsUrl(mapsBtn.getAttribute("data-maps-url"));
  }});
}})();
</script>
"""
