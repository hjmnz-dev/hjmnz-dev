"""Render data/contributions.json as an animated contribution heatmap.

Cells drop in along a diagonal once on load, then freeze (no looping glow).

Usage: python scripts/render_heatmap_svg.py   (set STATIC=1 for a frozen frame)
Writes: contrib-heatmap.svg
"""
import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG, BAR_BG, BORDER, FG, MUTED, ACCENT = "#0d1117", "#161b22", "#30363d", "#c9d1d9", "#8b949e", "#39d353"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

W = 860
BAR, PAD, LABEL_W, GAP = 30, 22, 30, 3
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def shade(day: dict, peak: int) -> int:
    if day["level"] >= 4 and peak and day["count"] >= 0.75 * peak:
        return 5  # neon for the very best days
    return day["level"]


def build(data: dict, static: bool) -> str:
    days, st = data["days"], data["stats"]
    first = date.fromisoformat(days[0]["date"])
    start_ord = first.toordinal() - (first.weekday() + 1) % 7  # back up to Sunday
    weeks = (date.fromisoformat(days[-1]["date"]).toordinal() - start_ord) // 7 + 1

    step = (W - 2 * PAD - LABEL_W) / weeks
    cell = step - GAP
    grid_x = PAD + LABEL_W
    grid_y = BAR + 58
    grid_h = 7 * step
    H = round(grid_y + grid_h + 62)
    peak = st["best_day"]["count"]

    anim = "" if static else (
        ".c{opacity:0;animation:drop .5s cubic-bezier(.2,.8,.2,1) forwards}"
        "@keyframes drop{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:none}}"
        + "".join(f".d{k}{{animation-delay:{0.25 + k * 0.022:.3f}s}}" for k in range(weeks + 7))
        + ".f{opacity:0;animation:fade .6s ease-out forwards;animation-delay:%.2fs}"
          "@keyframes fade{to{opacity:1}}" % (0.25 + (weeks + 7) * 0.022)
    )
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{st["total"]} GitHub contributions in the last year">',
        f"<style>text{{font-family:{FONT};fill:{MUTED};font-size:11px}}"
        f".h{{fill:{FG};font-size:14px}}.k{{fill:{ACCENT};font-weight:700}}{anim}</style>",
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M1 12a11 11 0 0 1 11-11h{W - 24}a11 11 0 0 1 11 11v{BAR - 12}H1z" fill="{BAR_BG}"/>',
        '<circle cx="20" cy="15" r="5" fill="#ff5f57"/><circle cx="37" cy="15" r="5" fill="#febc2e"/>'
        '<circle cx="54" cy="15" r="5" fill="#28c840"/>',
        f'<text x="{W / 2}" y="19" text-anchor="middle" font-size="12">hamsell@github: ~ — ./contributions.sh</text>',
        f'<text class="h" x="{PAD}" y="{BAR + 26}"><tspan class="k">{st["total"]:,}</tspan> contributions in the last year</text>',
    ]

    # Month labels: one per column where a new month starts, skipping crowded ones.
    last_x = -99
    for w in range(weeks):
        d = date.fromordinal(start_ord + w * 7)
        if d.day <= 7:
            x = grid_x + w * step
            if x - last_x > 3 * step:
                out.append(f'<text x="{x:.1f}" y="{grid_y - 7}">{MONTHS[d.month - 1]}</text>')
                last_x = x
    for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="{PAD}" y="{grid_y + r * step + cell - 2:.1f}">{name}</text>')

    for day in days:
        o = date.fromisoformat(day["date"]).toordinal() - start_ord
        w, r = divmod(o, 7)
        cls = "" if static else f' class="c d{w + r}"'
        out.append(
            f'<rect{cls} x="{grid_x + w * step:.1f}" y="{grid_y + r * step:.1f}" width="{cell:.1f}" '
            f'height="{cell:.1f}" rx="2.5" fill="{PALETTE[shade(day, peak)]}"/>'
        )

    # Footer: stats on the left, legend on the right.
    fy = grid_y + grid_h + 30
    best = date.fromisoformat(st["best_day"]["date"])
    parts = [
        ("current streak", f'{st["current_streak"]}d'),
        ("longest", f'{st["longest_streak"]}d'),
        ("best day", f'{peak} on {MONTHS[best.month - 1]} {best.day}'),
        ("active days", str(st["active_days"])),
    ]
    stats = '<tspan fill="#484f58">  ·  </tspan>'.join(
        f'{label} <tspan class="k">{value}</tspan>' for label, value in parts
    )
    fcls = "" if static else ' class="f"'
    out.append(f'<g{fcls}><text x="{PAD}" y="{fy}" xml:space="preserve">{stats}</text>')
    lx = W - PAD - len(PALETTE) * 15 - 32
    out.append(f'<text x="{lx - 8}" y="{fy}" text-anchor="end">Less</text>')
    for i, c in enumerate(PALETTE):
        out.append(f'<rect x="{lx + i * 15}" y="{fy - 10}" width="11" height="11" rx="2.5" fill="{c}"/>')
    out.append(f'<text x="{lx + len(PALETTE) * 15 + 4}" y="{fy}">More</text>')
    out.append(f'<text x="{W - PAD}" y="{fy + 20}" text-anchor="end" fill="#484f58" font-size="10">'
               f'updated {data["fetched"]}</text></g>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    data = json.loads(SRC.read_text(encoding="utf-8"))
    OUT.write_text(build(data, os.environ.get("STATIC") == "1"), encoding="utf-8")
    print(f"wrote {OUT.name}")
