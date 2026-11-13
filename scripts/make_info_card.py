"""Hand-authored neofetch-style info card.

Each line fades and slides in on a short stagger. Edit INFO to change the text.

Usage: python scripts/make_info_card.py   (set STATIC=1 for a frozen frame)
Writes: info-card.svg
"""
import os
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"

USER, HOST = "hamsell", "github"
INFO = [
    ("Role", "DevOps Analyst @ Seaboard"),
    ("Now", "Automating business workflows end to end"),
    ("Study", "B.Eng. Software Engineering @ INTEC"),
    ("Prev", "A.S. Software Development @ ITLA"),
    ("Location", "Santo Domingo, Dominican Republic"),
    ("Stack", "PHP · JavaScript · Node · MySQL · Python"),
    ("Also", "C# · .NET · React · Postgres · Azure"),
    ("Power", "Power Apps · Automate · SharePoint"),
    ("Certs", "AZ-900 · DP-900 · PL-900 · Scrum"),
    ("Projects", "Hamsflix: streaming + PayPal subscriptions"),
    ("", "macOS-style portfolio that runs in a browser"),
    ("Web", "hamselljimenez.dev"),
    ("Status", "Open to junior backend & automation roles"),
]

W, H = 490, 391  # H matches the portrait's displayed height (632x667 at width 370)
BAR, PAD = 30, 20
KEY_COL = 11  # characters reserved for the key column
BG, BAR_BG, BORDER = "#0d1117", "#161b22", "#30363d"
FG, MUTED, KEY, USER_C, HOST_C = "#c9d1d9", "#8b949e", "#39d353", "#39d353", "#58a6ff"
BLOCKS = ["#161b22", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
START, STAGGER = 0.35, 0.11


def build(static: bool) -> str:
    title = f"{USER}@{HOST}"
    lines = [
        f'<tspan fill="{USER_C}">{USER}@{HOST}</tspan><tspan fill="{MUTED}"> ~ $ </tspan>neofetch',
        f'<tspan fill="{USER_C}" font-weight="700">{USER}</tspan><tspan fill="{MUTED}">@</tspan>'
        f'<tspan fill="{HOST_C}" font-weight="700">{HOST}</tspan>',
        f'<tspan fill="{MUTED}">{"-" * len(title)}</tspan>',
    ]
    for key, value in INFO:
        label = f"{key}:" if key else ""
        lines.append(
            f'<tspan fill="{KEY}" font-weight="700">{escape(label.ljust(KEY_COL))}</tspan>{escape(value)}'
        )
    lines.append("")  # the colour blocks go on this row

    lh = (H - BAR - PAD * 2) / (len(lines) + 1)  # +1 for the closing prompt
    anim = "" if static else (
        ".l{opacity:0;animation:in .45s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
        ".c{animation:blink 1s steps(1) infinite}"
        "@keyframes blink{50%{opacity:0}}"
    )
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Hamsell Jimenez, about me">',
        f"<style>text{{font-family:{FONT};font-size:12.5px;fill:{FG};white-space:pre}}"
        f".t{{font-size:12px;fill:{MUTED}}}{anim}</style>",
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M1 12a11 11 0 0 1 11-11h{W - 24}a11 11 0 0 1 11 11v{BAR - 12}H1z" fill="{BAR_BG}"/>',
        '<circle cx="20" cy="15" r="5" fill="#ff5f57"/><circle cx="37" cy="15" r="5" fill="#febc2e"/>'
        '<circle cx="54" cy="15" r="5" fill="#28c840"/>',
        f'<text class="t" x="{W / 2}" y="19" text-anchor="middle">{title}: ~ — neofetch</text>',
    ]

    def group(i: int, inner: str) -> str:
        delay = "" if static else f' style="animation-delay:{START + i * STAGGER:.2f}s"'
        return f'<g class="l"{delay}>{inner}</g>'

    for i, line in enumerate(lines):
        y = BAR + PAD + (i + 0.75) * lh
        if line:
            out.append(group(i, f'<text x="{PAD}" y="{y:.1f}" xml:space="preserve">{line}</text>'))
        else:
            blocks = "".join(
                f'<rect x="{PAD + j * 22}" y="{y - lh * 0.62:.1f}" width="20" height="{lh * 0.75:.1f}" rx="2" fill="{c}"/>'
                for j, c in enumerate(BLOCKS)
            )
            out.append(group(i, blocks))

    i = len(lines)
    y = BAR + PAD + (i + 0.75) * lh
    prompt = (
        f'<text x="{PAD}" y="{y:.1f}" xml:space="preserve"><tspan fill="{USER_C}">{USER}@{HOST}</tspan>'
        f'<tspan fill="{MUTED}"> ~ $ </tspan></text>'
        f'<rect class="c" x="{PAD + 18 * 7.53:.1f}" y="{y - lh * 0.62:.1f}" width="8" height="{lh * 0.75:.1f}" fill="{KEY}"/>'
    )
    out.append(group(i, prompt))
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    OUT.write_text(build(os.environ.get("STATIC") == "1"), encoding="utf-8")
    print(f"wrote {OUT.name}")
