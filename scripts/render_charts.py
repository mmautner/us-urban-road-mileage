"""Render the two chart cards (1080x1350 PNG) from data/us-metro-road-per-resident-2023.csv.

Requires: pip install playwright pillow && playwright install chromium
Fonts (SIL OFL) are bundled in fonts/."""
import csv
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "charts"
OUT.mkdir(exist_ok=True)

T = {
    "paper": "#FAF8F4", "ink": "#1C1A17", "muted": "#55514B", "rule": "#E1DFDB",
    "accent": "#B6723B", "bar": "#D9D2C7", "serif": "Crimson Pro", "sans": "IBM Plex Sans",
}
W, H = 1080, 1350
PAD = 64
FONTS = [("Crimson Pro", "crimson-pro", (400, 600, 700)),
         ("IBM Plex Sans", "ibm-plex-sans", (400, 500, 600, 700))]
HI = {"Los Angeles": "accent", "Kansas City": "ink"}

rows = list(csv.DictReader(open(ROOT / "data" / "us-metro-road-per-resident-2023.csv")))
SOURCE = ("Source: FHWA, <i>Highway Statistics 2023</i>, Table HM-71. Urbanized areas over "
          "1 million people; population from the 2020 Census. Centerline miles only; "
          "FHWA does not record road width.")


def bars_svg(data, fmt, plot_h, xmax):
    """data: list of (label, value), already sorted. Returns an SVG string."""
    PW = W - 2 * PAD
    LAB_W = 292            # label column, right-aligned
    GAP = 14
    VAL_W = 86             # room for value text after the longest bar
    x0 = LAB_W + GAP
    bar_max = PW - x0 - VAL_W
    n = len(data)
    step = plot_h / n
    bh = step * 0.64
    g = [f'<line x1="{x0}" y1="0" x2="{x0}" y2="{plot_h:.1f}" stroke="{T["rule"]}" stroke-width="2"/>']
    for i, (lab, v) in enumerate(data):
        yc = step * i + step / 2
        wbar = v / xmax * bar_max
        role = HI.get(lab)
        fill = T[role] if role else T["bar"]
        cls = "hi" if role else "lab"
        vcls = f"v{role}" if role else "val"
        g.append(f'<rect x="{x0 + 1}" y="{yc - bh / 2:.1f}" width="{wbar:.1f}" height="{bh:.1f}" '
                 f'rx="2" fill="{fill}"/>')
        g.append(f'<text class="{cls}" x="{LAB_W}" y="{yc + 7:.1f}" text-anchor="end">{lab}</text>')
        g.append(f'<text class="{vcls}" x="{x0 + wbar + 9:.1f}" y="{yc + 7:.1f}">{fmt(v)}</text>')
    return (f'<svg width="{PW}" height="{plot_h:.0f}" viewBox="0 0 {PW} {plot_h:.0f}" '
            f'xmlns="http://www.w3.org/2000/svg">' + "".join(g) + "</svg>")


def fontfaces():
    return "".join(
        f"@font-face{{font-family:'{fam}';font-weight:{w};"
        f"src:url('../fonts/{slug}-latin-{w}-normal.woff2') format('woff2');}}"
        for fam, slug, weights in FONTS for w in weights)


CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{W}px;height:{H}px}}
body{{font-family:'{T['sans']}',sans-serif;background:{T['paper']};color:{T['ink']};
  font-variant-numeric:lining-nums tabular-nums;display:flex;flex-direction:column;
  padding:{PAD - 8}px {PAD}px 0}}
h1{{font-family:'{T['serif']}',serif;font-weight:700;font-size:56px;line-height:1.04;
  letter-spacing:-0.3px;text-wrap:balance}}
.sub{{font-size:24px;font-weight:500;color:{T['muted']};margin-top:14px;line-height:1.35}}
.plot{{flex:1;min-height:0;display:flex;align-items:center;padding:26px 0 18px}}
.foot{{flex:none;display:flex;align-items:flex-end;gap:32px;border-top:2px solid {T['rule']};
  padding:16px 0 30px}}
.src{{flex:1;font-size:19px;line-height:1.45;color:{T['muted']}}}
.wm{{flex:none;font-size:21px;font-weight:500;color:{T['muted']}}}
text{{font-family:'{T['sans']}',sans-serif}}
.lab{{font-size:21px;fill:{T['ink']}}}
.hi{{font-size:21px;font-weight:700;fill:{T['ink']}}}
.val{{font-size:20px;fill:{T['muted']}}}
.vaccent{{font-size:21px;font-weight:700;fill:{T['accent']}}}
.vink{{font-size:21px;font-weight:700;fill:{T['ink']}}}
"""

PLOT_H = 930


def card(title, sub, svg, source):
    body = (f'<h1>{title}</h1><div class="sub">{sub}</div>'
            f'<div class="plot">{svg}</div>'
            f'<div class="foot"><div class="src">{source}</div><div class="wm">maxmautner.com</div></div>')
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{fontfaces()}{CSS}</style>'
            f'</head><body>{body}</body></html>')


CARDS = [
    ("road-per-resident",
     "Los Angeles has less road per person than any big American city",
     "Meters of public road per resident, US urbanized areas over 1 million people, 2023",
     sorted([(r["label"], float(r["road_m_per_resident"])) for r in rows], key=lambda t: -t[1]),
     lambda v: f"{v:.1f}", 10.5, SOURCE),
    ("traffic-per-road-mile",
     "Los Angeles roads carry more traffic per mile than any other big city&#8217;s",
     "Vehicle-miles driven per day on each mile of public road, same urbanized areas, 2023",
     sorted([(r["label"], float(r["daily_vmt_per_road_mile"])) for r in rows], key=lambda t: -t[1]),
     lambda v: f"{v:,.0f}", 10300,
     "Source: FHWA, <i>Highway Statistics 2023</i>, Table HM-71. Urbanized areas over 1 million "
     "people. Daily vehicle-miles include through traffic. Centerline miles only; FHWA does not "
     "record road width."),
]

if __name__ == "__main__":
    with sync_playwright() as p:
        br = p.chromium.launch()
        for slug, title, sub, data, fmt, xmax, src in CARDS:
            f = OUT / f"{slug}.html"
            f.write_text(card(title, sub, bars_svg(data, fmt, PLOT_H, xmax), src))
            pg = br.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
            pg.goto(f.as_uri())
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(300)
            over = pg.evaluate("document.documentElement.scrollHeight > innerHeight")
            tmp = OUT / f"_{slug}_2x.png"
            pg.screenshot(path=str(tmp))
            pg.close()
            Image.open(tmp).resize((W, H), Image.LANCZOS).save(OUT / f"{slug}.png")
            print(slug, "OVERFLOW" if over else "ok")
        br.close()
