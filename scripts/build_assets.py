"""Generate the animated SVG assets used by the profile README.

Run from the repo root:  python3 scripts/build_assets.py
Edit the data near the bottom of this file, then re-run to refresh assets/.
"""

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"

SANS = "'Segoe UI', Ubuntu, 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
MONO_W = 0.61  # approximate advance of one monospace glyph, in em

CYAN, VIOLET, PINK = "#22D3EE", "#A78BFA", "#F472B6"
LIME, AMBER, BLUE = "#A3E635", "#FBBF24", "#60A5FA"
INK, MUTED, DIM = "#F1F5F9", "#9FB0C8", "#64748B"


def esc(text):
    return escape(text, {'"': "&quot;"})


def svg(w, h, body, label):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{esc(label)}">\n'
        f"<title>{esc(label)}</title>\n{body}\n</svg>\n"
    )


def write(name, content):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print("wrote", path.relative_to(OUT.parent))


def mono_width(text, size):
    return len(text) * size * MONO_W


def frame_defs(w, h, rx, a, b):
    """Dark panel background, grid texture, glow and gradient border."""
    return f"""
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0B1024"/><stop offset="1" stop-color="#05070F"/>
  </linearGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/>
  </linearGradient>
  <radialGradient id="halo" cx="0.85" cy="0" r="0.8">
    <stop offset="0" stop-color="{a}" stop-opacity="0.28"/><stop offset="1" stop-color="{a}" stop-opacity="0"/>
  </radialGradient>
  <pattern id="grid" width="22" height="22" patternUnits="userSpaceOnUse">
    <path d="M22 0H0V22" fill="none" stroke="#FFFFFF" stroke-opacity="0.035"/>
  </pattern>
  <clipPath id="clip"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>
</defs>
<g clip-path="url(#clip)">
  <rect width="{w}" height="{h}" fill="url(#bg)"/>
  <rect width="{w}" height="{h}" fill="url(#grid)"/>
  <rect width="{w}" height="{h}" fill="url(#halo)"/>
</g>
<rect x="0.75" y="0.75" width="{w - 1.5}" height="{h - 1.5}" rx="{rx}" fill="none" stroke="url(#edge)" stroke-opacity="0.55" stroke-width="1.5"/>"""


def comet(w, h, rx, color, dur=7):
    """A spot of light that travels around the panel border."""
    perim = 2 * (w + h)
    return f"""
<rect x="0.75" y="0.75" width="{w - 1.5}" height="{h - 1.5}" rx="{rx}" fill="none" stroke="{color}" stroke-width="2.5"
      stroke-linecap="round" stroke-dasharray="90 {perim}" opacity="0.9">
  <animate attributeName="stroke-dashoffset" from="0" to="-{perim + 90}" dur="{dur}s" repeatCount="indefinite"/>
</rect>"""


def corners(w, h, inset, size, color, opacity=0.8):
    i, s = inset, size
    paths = [
        f"M{i} {i + s}V{i}H{i + s}",
        f"M{w - i - s} {i}H{w - i}V{i + s}",
        f"M{i} {h - i - s}V{h - i}H{i + s}",
        f"M{w - i - s} {h - i}H{w - i}V{h - i - s}",
    ]
    return "".join(
        f'<path d="{p}" fill="none" stroke="{color}" stroke-width="2" opacity="{opacity}"/>' for p in paths
    )


def typing_steps(n, start, step):
    """(time, chars) pairs that reveal n characters one at a time."""
    return [(start + k * step, k) for k in range(n + 1)]


def discrete(attr, events, dur, value, begin="0s", repeat=True, freeze=False):
    times = ";".join(f"{t / dur:.5f}" for t, _ in events)
    values = ";".join(f"{value(v):.1f}" for _, v in events)
    extra = ' repeatCount="indefinite"' if repeat else ""
    extra += ' fill="freeze"' if freeze else ""
    return (
        f'<animate attributeName="{attr}" calcMode="discrete" dur="{dur}s" begin="{begin}" '
        f'keyTimes="{times}" values="{values}"{extra}/>'
    )


# ---------------------------------------------------------------- hero


def hero(name, kicker, tagline, phrases, left_hud, right_hud):
    w, h, horizon = 1200, 450, 330
    slot, cycle = 4.0, 4.0 * len(phrases)
    size, x0 = 21, 0.0
    longest = max(mono_width("> " + p, size) for p in phrases)
    x0 = (w - longest) / 2
    tx = x0 + mono_width("> ", size)
    char = size * MONO_W

    # one shared timeline: type, hold, erase each phrase in turn
    events, clips, texts = [(0.0, 0)], [], []
    for i, phrase in enumerate(phrases):
        n, start = len(phrase), i * slot
        mine = typing_steps(n, start + 0.05, 0.045)
        erase = 0.5 / n
        mine += [(start + 3.2 + j * erase, n - j) for j in range(1, n + 1)]
        events += mine
        own = [(0.0, 0)] + mine
        clips.append(
            f'<clipPath id="t{i}"><rect x="{tx:.1f}" y="{horizon - 70}" height="40" width="0">'
            + discrete("width", own, cycle, lambda c: c * char)
            + "</rect></clipPath>"
        )
        texts.append(
            f'<text x="{tx:.1f}" y="{horizon - 43}" clip-path="url(#t{i})" fill="{CYAN}" '
            f'font-family="{MONO}" font-size="{size}">{esc(phrase)}</text>'
        )
    timeline = sorted(events)
    cursor = (
        f'<rect y="{horizon - 61}" width="11" height="23" fill="{CYAN}" x="{tx:.1f}">'
        + discrete("x", timeline, cycle, lambda c: tx + c * char)
        + '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="0.9s" repeatCount="indefinite"/>'
        "</rect>"
    )

    floor_lines = []
    for k in range(-16, 17):
        floor_lines.append(
            f'<line x1="{600 + k * 22}" y1="{horizon}" x2="{600 + k * 150}" y2="{h}" stroke="{VIOLET}" stroke-opacity="0.35"/>'
        )
    lanes, lane_dur = 7, 3.5
    for i in range(lanes):
        b = -i * lane_dur / lanes
        floor_lines.append(
            f'<line x1="0" x2="{w}" y1="{horizon}" y2="{horizon}" stroke="{CYAN}" stroke-opacity="0">'
            f'<animate attributeName="y1" values="{horizon};{h}" dur="{lane_dur}s" begin="{b:.2f}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;1" keySplines="0.55 0 1 0.45"/>'
            f'<animate attributeName="y2" values="{horizon};{h}" dur="{lane_dur}s" begin="{b:.2f}s" repeatCount="indefinite" calcMode="spline" keyTimes="0;1" keySplines="0.55 0 1 0.45"/>'
            f'<animate attributeName="stroke-opacity" values="0;0.7" dur="{lane_dur}s" begin="{b:.2f}s" repeatCount="indefinite"/>'
            "</line>"
        )

    body = f"""
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#04050D"/><stop offset="0.72" stop-color="#0B0F2A"/><stop offset="1" stop-color="#120A2A"/>
  </linearGradient>
  <radialGradient id="gv" cx="0.18" cy="0.3" r="0.55">
    <stop offset="0" stop-color="#7C3AED" stop-opacity="0.55"/><stop offset="1" stop-color="#7C3AED" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="gc" cx="0.84" cy="0.25" r="0.55">
    <stop offset="0" stop-color="#06B6D4" stop-opacity="0.45"/><stop offset="1" stop-color="#06B6D4" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="name" gradientUnits="userSpaceOnUse" x1="150" y1="0" x2="1050" y2="0" spreadMethod="repeat">
    <stop offset="0" stop-color="{CYAN}"/><stop offset="0.33" stop-color="{VIOLET}"/>
    <stop offset="0.66" stop-color="{PINK}"/><stop offset="1" stop-color="{CYAN}"/>
    <animateTransform attributeName="gradientTransform" type="translate" from="0 0" to="900 0" dur="8s" repeatCount="indefinite"/>
  </linearGradient>
  <linearGradient id="hz" x1="0" x2="1">
    <stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset="0.5" stop-color="{PINK}"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#fff" stop-opacity="0.15"/><stop offset="1" stop-color="#fff"/>
  </linearGradient>
  <mask id="floor"><rect y="{horizon}" width="{w}" height="{h - horizon}" fill="url(#fade)"/></mask>
  <linearGradient id="sweep" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.05"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" fill-opacity="0.03"/></pattern>
  <filter id="blur" x="-10%" y="-50%" width="120%" height="200%"><feGaussianBlur stdDeviation="9"/></filter>
  <clipPath id="frame"><rect width="{w}" height="{h}" rx="26"/></clipPath>
  {''.join(clips)}
</defs>
<g clip-path="url(#frame)">
  <rect width="{w}" height="{h}" fill="url(#sky)"/>
  <rect width="{w}" height="{h}" fill="url(#gv)"><animate attributeName="opacity" values="0.7;1;0.7" dur="7s" repeatCount="indefinite"/></rect>
  <rect width="{w}" height="{h}" fill="url(#gc)"><animate attributeName="opacity" values="1;0.65;1" dur="9s" repeatCount="indefinite"/></rect>
  <g mask="url(#floor)">{''.join(floor_lines)}</g>
  <rect y="{horizon - 1}" width="{w}" height="2" fill="url(#hz)"/>
  <rect y="{horizon - 6}" width="{w}" height="12" fill="url(#hz)" opacity="0.35" filter="url(#blur)"/>

  <g font-family="{MONO}" font-size="14" letter-spacing="2">
    <circle cx="58" cy="52" r="5" fill="{LIME}"><animate attributeName="opacity" values="1;0.25;1" dur="1.6s" repeatCount="indefinite"/></circle>
    <text x="74" y="57" fill="{LIME}">{esc(left_hud)}</text>
    <text x="{w - 48}" y="57" fill="{DIM}" text-anchor="end">{esc(right_hud)}</text>
  </g>

  <text x="600" y="150" text-anchor="middle" font-family="{SANS}" font-size="70" font-weight="800" letter-spacing="7"
        fill="url(#name)" opacity="0.55" filter="url(#blur)">{esc(name)}</text>
  <text x="600" y="150" text-anchor="middle" font-family="{SANS}" font-size="70" font-weight="800" letter-spacing="7"
        fill="url(#name)">{esc(name)}</text>
  <text x="600" y="192" text-anchor="middle" font-family="{MONO}" font-size="17" letter-spacing="4" fill="{MUTED}">{esc(kicker)}</text>
  <text x="600" y="240" text-anchor="middle" font-family="{SANS}" font-size="25" fill="{INK}">{esc(tagline)}</text>

  <text x="{x0:.1f}" y="{horizon - 43}" fill="{PINK}" font-family="{MONO}" font-size="{size}">&gt;</text>
  {''.join(texts)}
  {cursor}

  <rect width="{w}" height="140" fill="url(#sweep)">
    <animate attributeName="y" values="-140;{h}" dur="6s" repeatCount="indefinite"/>
  </rect>
  <rect width="{w}" height="{h}" fill="url(#scan)"/>
  {corners(w, h, 22, 26, CYAN, 0.7)}
</g>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="26" fill="none" stroke="{VIOLET}" stroke-opacity="0.35" stroke-width="2"/>"""
    return svg(w, h, body, f"{name}: {tagline}")


# ------------------------------------------------------------ terminal


def terminal(session, title):
    """session: list of (prompt_command or None, [output lines])."""
    w, size, lh, top = 1200, 19, 31, 82
    rows = sum(1 + len(out) for _, out in session) + 1
    h = top + rows * lh + 18
    char = size * MONO_W
    px = 44
    body, defs, y, t = [], [], top, 0.6
    for i, (cmd, out) in enumerate(session):
        prompt = "sharvil@usyd:~$ "
        cx = px + mono_width(prompt, size)
        steps = typing_steps(len(cmd), 0, 0.035)
        defs.append(
            f'<clipPath id="c{i}"><rect x="{cx:.1f}" y="{y - 22}" height="30" width="0">'
            + discrete("width", steps, steps[-1][0] + 0.01, lambda c: c * char, begin=f"{t:.2f}s", repeat=False, freeze=True)
            + "</rect></clipPath>"
        )
        body.append(
            f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
            f'<text x="{px}" y="{y}" fill="{LIME}">sharvil@usyd<tspan fill="{DIM}">:</tspan><tspan fill="{BLUE}">~</tspan><tspan fill="{DIM}">$ </tspan></text>'
            f'<text x="{cx:.1f}" y="{y}" fill="{INK}" clip-path="url(#c{i})">{esc(cmd)}</text></g>'
        )
        t += len(cmd) * 0.035 + 0.35
        y += lh
        for line in out:
            body.append(
                f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.25s" begin="{t:.2f}s" fill="freeze"/>'
                f"{line_markup(line, px, y)}</g>"
            )
            t += 0.12
            y += lh
        t += 0.3
    body.append(
        f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
        f'<text x="{px}" y="{y}" fill="{LIME}">sharvil@usyd<tspan fill="{DIM}">:</tspan><tspan fill="{BLUE}">~</tspan><tspan fill="{DIM}">$</tspan></text>'
        f'<rect x="{px + mono_width(prompt, size):.1f}" y="{y - 18}" width="11" height="22" fill="{CYAN}">'
        '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/></rect></g>'
    )
    chrome = f"""
<rect x="0.75" y="0.75" width="{w - 1.5}" height="52" rx="18" fill="#FFFFFF" fill-opacity="0.035"/>
<line x1="0" x2="{w}" y1="52" y2="52" stroke="#FFFFFF" stroke-opacity="0.08"/>
<circle cx="34" cy="27" r="7" fill="#FF5F57"/><circle cx="58" cy="27" r="7" fill="#FEBC2E"/><circle cx="82" cy="27" r="7" fill="#28C840"/>
<text x="{w / 2}" y="32" text-anchor="middle" font-family="{MONO}" font-size="14" fill="{DIM}" letter-spacing="1">{esc(title)}</text>"""
    content = (
        frame_defs(w, h, 18, CYAN, VIOLET)
        + f"<defs>{''.join(defs)}</defs>"
        + chrome
        + f'<g font-family="{MONO}" font-size="{size}" xml:space="preserve">{"".join(body)}</g>'
        + comet(w, h, 18, CYAN, 9)
    )
    return svg(w, h, content, title)


def line_markup(line, x, y):
    """Lines are plain text, or a list of (text, colour) segments."""
    if isinstance(line, str):
        line = [(line, MUTED)]
    spans = "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in line)
    return f'<text x="{x}" y="{y}">{spans}</text>'


# --------------------------------------------------------------- cards


def chip_row(items, x, y, color, size=12.5, max_w=None, gap=8):
    out, cx = [], x
    for item in items:
        cw = mono_width(item, size) + 22
        if max_w and cx + cw > x + max_w:
            break
        out.append(
            f'<rect x="{cx:.1f}" y="{y}" width="{cw:.1f}" height="26" rx="13" fill="{color}" fill-opacity="0.1" stroke="{color}" stroke-opacity="0.4"/>'
            f'<text x="{cx + cw / 2:.1f}" y="{y + 17.5}" text-anchor="middle" font-family="{MONO}" font-size="{size}" fill="{color}">{esc(item)}</text>'
        )
        cx += cw + gap
    return "".join(out)


def project_card(p):
    w, h, rx = 500, 300, 20
    a, b = p["colors"]
    tag_w = mono_width(p["tag"], 11.5) + 40
    desc = "".join(
        f'<text x="30" y="{128 + i * 25}" font-family="{SANS}" font-size="17" fill="{MUTED}">{esc(t)}</text>'
        for i, t in enumerate(p["desc"])
    )
    metrics = "".join(
        f'<text x="{30 + i * 235}" y="{218}" font-family="{SANS}" font-size="27" font-weight="700" fill="{a}">{esc(v)}</text>'
        f'<text x="{30 + i * 235}" y="{240}" font-family="{MONO}" font-size="11.5" letter-spacing="1.3" fill="{DIM}">{esc(l)}</text>'
        for i, (v, l) in enumerate(p["metrics"])
    )
    body = f"""{frame_defs(w, h, rx, a, b)}
<text x="30" y="44" font-family="{MONO}" font-size="12.5" letter-spacing="1.8" fill="{a}">{esc(p['index'])} // {esc(p['category'])}</text>
<rect x="{w - 30 - tag_w:.1f}" y="27" width="{tag_w:.1f}" height="24" rx="12" fill="{a}" fill-opacity="0.12" stroke="{a}" stroke-opacity="0.45"/>
<circle cx="{w - 30 - tag_w + 14:.1f}" cy="39" r="3.5" fill="{a}"><animate attributeName="opacity" values="1;0.2;1" dur="1.8s" repeatCount="indefinite"/></circle>
<text x="{w - 30 - tag_w + 24:.1f}" y="43.5" font-family="{MONO}" font-size="11.5" letter-spacing="1" fill="{a}">{esc(p['tag'])}</text>
<text x="30" y="94" font-family="{SANS}" font-size="31" font-weight="700" fill="{INK}">{esc(p['title'])}</text>
{desc}
<line x1="30" x2="{w - 30}" y1="178" y2="178" stroke="{a}" stroke-opacity="0.25" stroke-dasharray="3 5"/>
{metrics}
{chip_row(p['stack'], 30, 256, b, max_w=w - 60)}
{comet(w, h, rx, a, p.get('speed', 7))}"""
    return svg(w, h, body, f"{p['title']}: {' '.join(p['desc'])}")


def module_card(m):
    w, h, rx = 400, 220, 18
    a, b = m["colors"]
    body = f"""{frame_defs(w, h, rx, a, b)}
<text x="26" y="40" font-family="{MONO}" font-size="12" letter-spacing="1.8" fill="{a}">{esc(m['kicker'])}</text>
<text x="{w - 26}" y="40" text-anchor="end" font-family="{MONO}" font-size="12" fill="{DIM}">SOURCE ↗</text>
<text x="26" y="80" font-family="{SANS}" font-size="23" font-weight="700" fill="{INK}">{esc(m['title'])}</text>
<text x="26" y="146" font-family="{SANS}" font-size="50" font-weight="800" fill="{a}">{esc(m['stat'])}</text>
<text x="{26 + len(m['stat']) * 30 + 12}" y="128" font-family="{MONO}" font-size="12.5" letter-spacing="1.4" fill="{MUTED}">{esc(m['unit'][0])}</text>
<text x="{26 + len(m['stat']) * 30 + 12}" y="146" font-family="{MONO}" font-size="12.5" letter-spacing="1.4" fill="{MUTED}">{esc(m['unit'][1])}</text>
<line x1="26" x2="{w - 26}" y1="168" y2="168" stroke="{a}" stroke-opacity="0.25" stroke-dasharray="3 5"/>
<text x="26" y="195" font-family="{MONO}" font-size="12.5" fill="{DIM}">{esc(m['topics'])}</text>
{comet(w, h, rx, a, 8)}"""
    return svg(w, h, body, f"{m['title']}: {m['stat']} {' '.join(m['unit']).lower()}")


# -------------------------------------------------------------- panels


def capabilities(columns):
    w, col_w, pad = 1200, 360, 40
    rows_needed = []
    layouts = []
    for title, color, items in columns:
        rows, row, cx = [], [], 0
        for item in items:
            cw = mono_width(item, 13.5) + 24
            if cx + cw > col_w and row:
                rows.append(row)
                row, cx = [], 0
            row.append((item, cx, cw))
            cx += cw + 10
        rows.append(row)
        layouts.append((title, color, rows))
        rows_needed.append(len(rows))
    h = 100 + max(rows_needed) * 40 + 20
    out = []
    for i, (title, color, rows) in enumerate(layouts):
        x = pad + i * (col_w + 30)
        out.append(
            f'<rect x="{x}" y="38" width="8" height="8" fill="{color}" transform="rotate(45 {x + 4} 42)"/>'
            f'<text x="{x + 20}" y="47" font-family="{MONO}" font-size="14" letter-spacing="2.5" fill="{color}">{esc(title)}</text>'
            f'<line x1="{x}" x2="{x + col_w}" y1="64" y2="64" stroke="{color}" stroke-opacity="0.3"/>'
        )
        for r, row in enumerate(rows):
            y = 82 + r * 40
            for item, cx, cw in row:
                out.append(
                    f'<rect x="{x + cx:.1f}" y="{y}" width="{cw:.1f}" height="28" rx="6" fill="{color}" fill-opacity="0.08" stroke="{color}" stroke-opacity="0.35"/>'
                    f'<text x="{x + cx + cw / 2:.1f}" y="{y + 19}" text-anchor="middle" font-family="{MONO}" font-size="13.5" fill="{INK}">{esc(item)}</text>'
                )
    body = frame_defs(w, h, 18, VIOLET, CYAN) + "".join(out) + comet(w, h, 18, VIOLET, 10)
    labels = "; ".join(f"{t}: {', '.join(i)}" for t, _, i in columns)
    return svg(w, h, body, labels)


def stats(tiles):
    w, h = 1200, 200
    tw = (w - 80 - 3 * 20) / 4
    out = []
    for i, (value, label, sub, color) in enumerate(tiles):
        x = 40 + i * (tw + 20)
        out.append(
            f'<rect x="{x:.1f}" y="30" width="{tw:.1f}" height="140" rx="14" fill="{color}" fill-opacity="0.06" stroke="{color}" stroke-opacity="0.35"/>'
            f'<path d="M{x + 14:.1f} 30h40" stroke="{color}" stroke-width="3"/>'
            f'<text x="{x + 22:.1f}" y="95" font-family="{SANS}" font-size="44" font-weight="800" fill="{color}">{esc(value)}</text>'
            f'<text x="{x + 22:.1f}" y="124" font-family="{MONO}" font-size="12.5" letter-spacing="1.6" fill="{INK}">{esc(label)}</text>'
            f'<text x="{x + 22:.1f}" y="148" font-family="{SANS}" font-size="14" fill="{DIM}">{esc(sub)}</text>'
        )
    body = frame_defs(w, h, 18, AMBER, PINK) + "".join(out) + comet(w, h, 18, AMBER, 10)
    return svg(w, h, body, "; ".join(f"{v} {l} — {s}" for v, l, s, _ in tiles))


def section(index, title, note):
    """Transparent heading, readable on both GitHub light and dark themes."""
    w, h = 1200, 76
    tw = len(title) * 19 + 120
    body = f"""
<defs>
  <linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#0891B2"/><stop offset="0.5" stop-color="#7C3AED"/><stop offset="1" stop-color="#DB2777"/></linearGradient>
  <linearGradient id="l" x1="0" x2="1"><stop offset="0" stop-color="#7C3AED" stop-opacity="0.8"/><stop offset="1" stop-color="#7C3AED" stop-opacity="0"/></linearGradient>
</defs>
<rect x="6" y="30" width="16" height="16" fill="url(#g)" transform="rotate(45 14 38)">
  <animateTransform attributeName="transform" type="rotate" values="45 14 38;225 14 38" dur="6s" repeatCount="indefinite"/>
</rect>
<text x="40" y="49" font-family="{MONO}" font-size="20" font-weight="700" fill="#0891B2">{esc(index)}</text>
<text x="76" y="50" font-family="{SANS}" font-size="30" font-weight="800" letter-spacing="3" fill="url(#g)">{esc(title)}</text>
<rect x="{tw}" y="37" width="{w - tw - 260}" height="2" fill="url(#l)"/>
<text x="{w - 8}" y="45" text-anchor="end" font-family="{MONO}" font-size="14" letter-spacing="1.5" fill="#64748B">{esc(note)}</text>"""
    return svg(w, h, body, f"{index} {title}")


def button(label, glyph, color):
    w, h = 280, 64
    body = f"""{frame_defs(w, h, 32, color, VIOLET)}
<text x="{w / 2}" y="40" text-anchor="middle" font-family="{MONO}" font-size="17" font-weight="700" letter-spacing="3" fill="{INK}"><tspan fill="{color}">{esc(glyph)}</tspan>  {esc(label)}</text>
{comet(w, h, 32, color, 5)}"""
    return svg(w, h, body, label)


def divider():
    w, h = 1200, 24
    body = f"""
<defs><linearGradient id="d" x1="0" x2="1">
  <stop offset="0" stop-color="#7C3AED" stop-opacity="0"/><stop offset="0.5" stop-color="#7C3AED"/><stop offset="1" stop-color="#7C3AED" stop-opacity="0"/>
</linearGradient>
<radialGradient id="p"><stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient></defs>
<rect y="11" width="{w}" height="2" fill="url(#d)"/>
<ellipse cy="12" rx="90" ry="6" fill="url(#p)"><animate attributeName="cx" values="-100;1300" dur="4s" repeatCount="indefinite"/></ellipse>"""
    return svg(w, h, body, "divider")


def footer(line):
    w, h, horizon = 1200, 170, 70
    grid = "".join(
        f'<line x1="{600 + k * 24}" y1="{horizon}" x2="{600 + k * 110}" y2="{h}" stroke="{VIOLET}" stroke-opacity="0.3"/>'
        for k in range(-16, 17)
    ) + "".join(
        f'<line x1="0" x2="{w}" y1="{horizon + d}" y2="{horizon + d}" stroke="{CYAN}" stroke-opacity="{0.15 + d / 200:.2f}"/>'
        for d in (8, 20, 37, 60, 90)
    )
    lw = mono_width(line, 17)
    body = f"""
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05070F"/><stop offset="1" stop-color="#140B2E"/></linearGradient>
  <linearGradient id="hz" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset="0.5" stop-color="{PINK}"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>
  <clipPath id="c"><rect width="{w}" height="{h}" rx="22"/></clipPath>
</defs>
<g clip-path="url(#c)">
  <rect width="{w}" height="{h}" fill="url(#bg)"/>
  {grid}
  <rect y="{horizon - 1}" width="{w}" height="2" fill="url(#hz)"/>
  <rect x="{600 - lw / 2 - 30:.1f}" y="18" width="{lw + 60:.1f}" height="36" rx="18" fill="#05070F" stroke="{PINK}" stroke-opacity="0.5"/>
  <text x="600" y="42" text-anchor="middle" font-family="{MONO}" font-size="17" letter-spacing="1" fill="{INK}">{esc(line)}<tspan fill="{CYAN}">▋<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></tspan></text>
</g>"""
    return svg(w, h, body, line)


# ---------------------------------------------------------------- data

PROJECTS = {
    "chargeatlas": dict(
        index="01", category="GEOSPATIAL DATA ENGINEERING", tag="OPEN SOURCE", title="ChargeAtlas NSW",
        desc=["Links NSW EV chargers to ABS regions, Open", "Charge Map and OSM — with evidence for every match."],
        metrics=[("1,956 / 1,956", "SOURCE RECORDS KEPT"), ("24 / 24", "VALIDATION CHECKS")],
        stack=["Python", "GeoPandas", "DuckDB", "RapidFuzz", "Jupyter"], colors=(CYAN, BLUE),
    ),
    "ideajoust": dict(
        index="02", category="AI WORKFLOWS", tag="CASE STUDY", title="IdeaJoust",
        desc=["One rough idea in, competing approaches out —", "ranked in a pairwise tournament, then attacked."],
        metrics=[("Bradley–Terry", "PAIRWISE RANKING"), ("Multi-agent", "AI CRITICS")],
        stack=["Python", "SQLite", "LLM agents", "Claude Code"], colors=(PINK, VIOLET), speed=6,
    ),
    "wakeline": dict(
        index="03", category="DEVELOPER TOOLS", tag="CASE STUDY", title="Wakeline",
        desc=["Local analytics for Claude Code: sessions, tokens,", "estimated cost and coding friction, from your logs."],
        metrics=[("Local-first", "NO CLOUD NEEDED"), ("Tokens · Cost", "FRICTION SIGNALS")],
        stack=["Python", "SQLite", "JavaScript", "GH Actions"], colors=(VIOLET, CYAN), speed=8,
    ),
    "tracelens": dict(
        index="04", category="DEVELOPER ANALYTICS", tag="CASE STUDY", title="TraceLens",
        desc=["Offline Codex analytics with traceable usage,", "validation evidence and memory for next session."],
        metrics=[("Offline", "INTERACTIVE DASHBOARD"), ("Portable", "PYTHON PLUGIN")],
        stack=["Python", "SQLite", "HTML", "JavaScript"], colors=(LIME, CYAN), speed=7.5,
    ),
    "flight-delay": dict(
        index="05", category="MACHINE LEARNING", tag="CASE STUDY", title="Flight Delay Prediction",
        desc=["Three classifiers compared on pre-flight features", "to predict arrival delays of over 15 minutes."],
        metrics=[("93,380", "FLIGHTS MODELLED"), ("3 models", "14 PREDICTORS")],
        stack=["Python", "pandas", "scikit-learn"], colors=(AMBER, PINK), speed=6.5,
    ),
    "price-insights": dict(
        index="06", category="RECOMMENDER SYSTEMS", tag="CASE STUDY", title="Price Insights",
        desc=["Cross-retailer search, price tracking and hybrid", "recommendations across Amazon, Croma & Reliance."],
        metrics=[("3 retailers", "PRICE TRACKING"), ("Hybrid", "CONTENT + COLLAB")],
        stack=["Next.js", "TypeScript", "Flask", "MongoDB"], colors=(BLUE, VIOLET), speed=8.5,
    ),
}

MODULES = {
    "ai-basics": dict(
        kicker="LAB // PYTHON", title="AI Basics", stat="18", unit=("PYTHON", "PROGRAMS"),
        topics="BFS · DFS · A* · TSP · neural gates", colors=(CYAN, VIOLET),
    ),
    "os-algorithms": dict(
        kicker="LAB // C · POSIX", title="OS Algorithms", stat="27", unit=("C", "PROGRAMS"),
        topics="scheduling · paging · deadlock · fork()", colors=(PINK, VIOLET),
    ),
    "modern-algorithms": dict(
        kicker="NOTES // C", title="Modern Algorithms", stat="5", unit=("DESIGN", "STRATEGIES"),
        topics="D&C · greedy · DP · backtracking", colors=(LIME, CYAN),
    ),
}


def main():
    write("hero.svg", hero(
        "SHARVIL PRABHUDESAI",
        "DATA SCIENCE & AI  ·  MCS @ THE UNIVERSITY OF SYDNEY",
        "I build AI tools — and then test whether they actually work.",
        [
            "building LLM agents & evaluation pipelines",
            "engineering reproducible, auditable data pipelines",
            "shipping local-first developer analytics",
            "turning messy data into decisions",
        ],
        "SYSTEM ONLINE",
        "SYDNEY, AU · 33.87°S 151.21°E",
    ))
    write("terminal.svg", terminal([
        ("whoami", [[("Sharvil Prabhudesai", INK), (" — MCS, Data Science & AI @ University of Sydney", MUTED)]]),
        ("cat focus.txt", [
            [("▸ ", PINK), ("LLM agents, multi-agent pipelines and LLM-as-judge evaluation", MUTED)],
            [("▸ ", PINK), ("reproducible data pipelines with auditable, evidence-backed matching", MUTED)],
            [("▸ ", PINK), ("local-first developer analytics for AI coding tools", MUTED)],
        ]),
        ("ls ~/experience", [[("tangentia_project_intern_2023/", BLUE), ("   ", MUTED), ("ieee_idciot_2024_paper.pdf", AMBER)]]),
        ("echo $STATUS", [[("building things — and checking they actually work ", CYAN), ("✓", LIME)]]),
    ], "sharvil@usyd — zsh — 120×24"))
    for name, p in PROJECTS.items():
        write(f"cards/{name}.svg", project_card(p))
    for name, m in MODULES.items():
        write(f"cards/{name}.svg", module_card(m))
    write("capabilities.svg", capabilities([
        ("AI & LLMS", PINK, ["LLM agents", "Multi-agent pipelines", "LLM-as-judge", "Prompt engineering", "Recommenders"]),
        ("DATA", CYAN, ["pandas", "NumPy", "GeoPandas", "DuckDB", "Jupyter", "Feature engineering"]),
        ("EVALUATION", LIME, ["Experiment design", "Hypothesis testing", "Cross-validation", "Bradley–Terry", "pytest"]),
    ]))
    write("stats.svg", stats([
        ("82.37", "WAM · DISTINCTION", "MCS, University of Sydney", CYAN),
        ("9.51", "CGPA / 10", "BE Computer Science", VIOLET),
        ("2×", "SCHOLARSHIPS", "Sydney Scholars · VC Intl", PINK),
        ("IEEE", "PUBLISHED 2024", "Recommendation systems", AMBER),
    ]))
    for slug, idx, title, note in [
        ("whoami", "01", "WHOAMI", "// system profile"),
        ("builds", "02", "FEATURED BUILDS", "// click a card to open"),
        ("foundations", "03", "FOUNDATIONS", "// open-source lab collections"),
        ("stack", "04", "TECH STACK", "// tools of the trade"),
        ("recognition", "05", "RECOGNITION", "// academics & research"),
    ]:
        write(f"sections/{slug}.svg", section(idx, title, note))
    for slug, label, glyph, color in [
        ("portfolio", "PORTFOLIO", "◈", CYAN),
        ("linkedin", "LINKEDIN", "in", BLUE),
        ("email", "EMAIL", "@", PINK),
        ("cv", "RÉSUMÉ", "⇩", LIME),
    ]:
        write(f"buttons/{slug}.svg", button(label, glyph, color))
    write("divider.svg", divider())
    write("footer.svg", footer("// end of transmission — let's build something that actually works "))


if __name__ == "__main__":
    main()
