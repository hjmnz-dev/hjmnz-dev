"""Turn source-prepped.png into an animated ASCII portrait SVG.

Each row is revealed by a clip that wipes left to right, with a block cursor
riding the edge. Rows are staggered top to bottom; it prints once and freezes.

Usage: python scripts/make_ascii_svg.py   (set STATIC=1 for a frozen frame)
Writes: hamsell-ascii.svg
"""
import os
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
MASK = ROOT / "source-mask.png"
MODE = os.environ.get("MODE", "positive")  # positive | ink
OUT = ROOT / os.environ.get("OUT", "hamsell-ascii.svg")

RAMP = " .`:-=+*cs#%@"  # sparse -> dense; the leading space clears the background
COLS = 100
CW, CH = 6.0, 11.0  # character cell in SVG units
PAD = 16
BAR = 30  # title bar height
ROW_DUR = 0.22
ROW_STAGGER = 0.055
BEGIN = 0.3

BG, BAR_BG, FG, CURSOR = "#0d1117", "#161b22", "#c9d1d9", "#39d353"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"


def to_ascii() -> list[str]:
    img = Image.open(SRC).convert("L")
    rows = round(img.height / img.width * COLS * CW / CH)
    small = np.asarray(img.resize((COLS, rows), Image.LANCZOS), dtype=np.float32) / 255.0
    if MODE == "positive" and MASK.exists():
        # Light glyphs on a dark terminal: bright pixels get dense glyphs,
        # and the rembg mask (not brightness) decides what is background.
        mask = np.asarray(Image.open(MASK).convert("L").resize((COLS, rows), Image.LANCZOS)) / 255.0
        level = (0.1 + 0.74 * small ** 1.15) * (mask > 0.5)
    else:
        level = np.clip((1.0 - small - 0.04) / 0.96, 0, 1) ** 0.85
    idx = np.rint(level * (len(RAMP) - 1)).astype(int)
    lines = ["".join(RAMP[i] for i in row) for row in idx]
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def build(lines: list[str], static: bool) -> str:
    w = PAD * 2 + COLS * CW
    h = BAR + PAD + len(lines) * CH + PAD
    row_w = COLS * CW
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" '
        f'width="{w:g}" height="{h:g}" role="img" aria-label="ASCII portrait of Hamsell">',
        f"<style>text{{font-family:{FONT};font-size:10px;fill:{FG};white-space:pre}}"
        f".t{{font-size:12px;fill:#8b949e}}</style>",
        f'<rect width="{w:g}" height="{h:g}" rx="12" fill="{BG}" stroke="#30363d"/>',
        f'<path d="M0 12a12 12 0 0 1 12-12h{w - 24:g}a12 12 0 0 1 12 12v{BAR - 12}h-{w:g}z" fill="{BAR_BG}"/>',
        '<circle cx="20" cy="15" r="5" fill="#ff5f57"/>'
        '<circle cx="37" cy="15" r="5" fill="#febc2e"/>'
        '<circle cx="54" cy="15" r="5" fill="#28c840"/>',
        f'<text class="t" x="{w / 2:g}" y="19" text-anchor="middle">hamsell@github: ~/portrait</text>',
    ]
    defs, body = [], []
    for i, line in enumerate(lines):
        y = BAR + PAD + i * CH
        text = (
            f'<text x="{PAD}" y="{y + CH - 2.5:g}" textLength="{row_w:g}" '
            f'lengthAdjust="spacing" xml:space="preserve"{{clip}}>{line}</text>'
        )
        if static or not line.strip():
            body.append(text.format(clip=""))
            continue
        t0 = BEGIN + i * ROW_STAGGER
        defs.append(
            f'<clipPath id="r{i}"><rect x="{PAD}" y="{y:g}" width="0" height="{CH:g}">'
            f'<animate attributeName="width" from="0" to="{row_w:g}" begin="{t0:.3f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
        )
        body.append(text.format(clip=f' clip-path="url(#r{i})"'))
        body.append(
            f'<rect x="{PAD}" y="{y + 1:g}" width="{CW:g}" height="{CH - 2:g}" fill="{CURSOR}" opacity="0">'
            f'<set attributeName="opacity" to="1" begin="{t0:.3f}s"/>'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + row_w:g}" begin="{t0:.3f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{t0 + ROW_DUR:.3f}s"/></rect>'
        )
    if defs:
        out.append("<defs>" + "".join(defs) + "</defs>")
    out.extend(body)
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    lines = to_ascii()
    OUT.write_text(build(lines, os.environ.get("STATIC") == "1"), encoding="utf-8")
    print(f"wrote {OUT.name} ({COLS}x{len(lines)} chars)")
