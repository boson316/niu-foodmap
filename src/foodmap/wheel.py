from __future__ import annotations

import json
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


def _conic_gradient(segment_count: int) -> str:
    if segment_count <= 0:
        return "#eee"
    step = 360.0 / segment_count
    stops: list[str] = []
    for index in range(segment_count):
        start = step * index
        end = step * (index + 1)
        color = _WHEEL_COLORS[index % len(_WHEEL_COLORS)]
        stops.append(f"{color} {start:.4f}deg {end:.4f}deg")
    return f"conic-gradient(from -{step / 2:.4f}deg, {', '.join(stops)})"


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
    gradient = _conic_gradient(segment_count)
    data_json = json.dumps(payload, ensure_ascii=False)
    label_rows = "\n".join(
        f'<span class="wheel-slice-label" style="--i:{index};" title="{item["name"]}">'
        f'{index + 1}</span>'
        for index, item in enumerate(payload)
    )
    legend_rows = "\n".join(
        f'<li><span class="wheel-legend-no">{index + 1}</span>'
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
}}
.wheel-disc {{
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: {gradient};
  transition: transform 4.2s cubic-bezier(0.12, 0.75, 0.08, 1);
  will-change: transform;
}}
.wheel-labels {{
  position: absolute;
  inset: 0;
  transition: transform 4.2s cubic-bezier(0.12, 0.75, 0.08, 1);
  pointer-events: none;
}}
.wheel-slice-label {{
  position: absolute;
  top: 50%;
  left: 50%;
  width: 28%;
  transform-origin: 0 0;
  transform:
    rotate(calc((360deg / {segment_count}) * var(--i)))
    translate(24%, -50%)
    rotate(calc((360deg / {segment_count}) * -0.5));
  font-size: clamp(0.95rem, 3.8vw, 1.15rem);
  font-weight: 800;
  color: #111;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.85);
  line-height: 1;
  text-align: center;
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
.wheel-hub {{
  position: absolute;
  top: 50%;
  left: 50%;
  width: 18%;
  aspect-ratio: 1;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: #fff;
  border: 4px solid #1a73e8;
  z-index: 2;
  box-shadow: inset 0 0 0 2px #e8f0fe;
}}
.wheel-actions {{
  display: flex;
  justify-content: center;
  gap: 0.75rem;
  flex-wrap: wrap;
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
  margin-top: 1rem;
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
  <div class="wheel-stage" aria-label="餐廳轉盤">
    <div class="wheel-pointer" aria-hidden="true"></div>
    <div class="wheel-disc-wrap">
      <div class="wheel-disc" id="wheel-disc"></div>
      <div class="wheel-labels" id="wheel-labels">
        {label_rows}
      </div>
      <div class="wheel-hub" aria-hidden="true"></div>
    </div>
  </div>
  <div class="wheel-legend" aria-label="轉盤編號對照">
    <ul>{legend_rows}</ul>
  </div>
  <div class="wheel-actions">
    <button class="wheel-btn wheel-btn-primary" id="wheel-spin-btn" type="button">開始轉盤</button>
    <button class="wheel-btn wheel-btn-ghost" id="wheel-reset-btn" type="button">重置</button>
  </div>
  <div class="wheel-result" id="wheel-result" aria-live="polite">
    <p>按下「開始轉盤」，讓命運決定午餐／晚餐。</p>
  </div>
</div>
<script>
(() => {{
  const restaurants = {data_json};
  const segmentCount = restaurants.length;
  const sliceAngle = 360 / segmentCount;
  const disc = document.getElementById("wheel-disc");
  const labels = document.getElementById("wheel-labels");
  const spinBtn = document.getElementById("wheel-spin-btn");
  const resetBtn = document.getElementById("wheel-reset-btn");
  const result = document.getElementById("wheel-result");
  let rotation = 0;
  let spinning = false;

  function renderWinner(item, winnerIndex) {{
    result.innerHTML = `
      <h4>#${{winnerIndex + 1}} ${{item.name}}</h4>
      <p>綜合分數 <strong>${{item.composite_score.toFixed(2)}}</strong>
        　黃氏 <strong>${{item.huang_rating.toFixed(2)}}</strong>
        　距離 <strong>${{item.distance_display}}</strong></p>
      <a href="${{item.maps_url}}" target="_blank" rel="noopener">📖 開啟 Google Maps</a>
    `;
  }}

  function spin() {{
    if (spinning) return;
    spinning = true;
    spinBtn.disabled = true;
    result.innerHTML = "<p>轉盤旋轉中…</p>";

    const winnerIndex = Math.floor(Math.random() * segmentCount);
    const extraTurns = 4 + Math.floor(Math.random() * 3);
    const target = extraTurns * 360 + (360 - winnerIndex * sliceAngle - sliceAngle / 2);
    rotation += target;
    const transform = `rotate(${{rotation}}deg)`;
    disc.style.transform = transform;
    labels.style.transform = transform;

    window.setTimeout(() => {{
      renderWinner(restaurants[winnerIndex], winnerIndex);
      spinning = false;
      spinBtn.disabled = false;
    }}, 4300);
  }}

  function resetWheel() {{
    if (spinning) return;
    rotation = 0;
    disc.style.transition = "none";
    labels.style.transition = "none";
    disc.style.transform = "rotate(0deg)";
    labels.style.transform = "rotate(0deg)";
    window.requestAnimationFrame(() => {{
      disc.style.transition = "";
      labels.style.transition = "";
    }});
    result.innerHTML = "<p>按下「開始轉盤」，讓命運決定午餐／晚餐。</p>";
  }}

  spinBtn.addEventListener("click", spin);
  resetBtn.addEventListener("click", resetWheel);
}})();
</script>
"""
