"""Generates the animated pixel-art SVGs in assets/. Run: python3 scripts/build.py"""

import math
import os
import random
from html import escape

from pixelfont import HEIGHT, fmt, text_path, text_width

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

C = {
    "bg": "#0d0b1e", "panel": "#141130", "edge": "#2e2a5c", "shadow": "#07051a",
    "purple": "#a855f7", "pink": "#f472b6", "cyan": "#22d3ee", "yellow": "#facc15",
    "green": "#4ade80", "orange": "#fb923c", "red": "#f87171", "white": "#f5f3ff", "dim": "#8b85b8",
}
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"


# MARK: helpers

def svg(width, height, body, style="", label=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}" shape-rendering="crispEdges">'
            f"<title>{escape(label)}</title><style>{style}</style>{body}</svg>")


def save(name, content):
    os.makedirs(ASSETS, exist_ok=True)
    with open(os.path.join(ASSETS, name), "w") as f:
        f.write(content)
    print(f"assets/{name}  {len(content) // 1024} KB")


def notch(x, y, w, h, p):
    """Rectangle with one-pixel stepped corners."""
    return (f"M{fmt(x + p)} {fmt(y)}h{fmt(w - 2 * p)}v{fmt(p)}h{fmt(p)}v{fmt(h - 2 * p)}h{fmt(-p)}v{fmt(p)}"
            f"h{fmt(-(w - 2 * p))}v{fmt(-p)}h{fmt(-p)}v{fmt(-(h - 2 * p))}h{fmt(p)}z")


def frame(x, y, w, h, p=4, fill=None, edge=None, shadow=True):
    fill, edge = fill or C["panel"], edge or C["edge"]
    out = ""
    if shadow:
        out += f'<path d="{notch(x + p, y + p, w - p, h - p, p)}" fill="{C["shadow"]}"/>'
        w, h = w - p, h - p
    out += f'<path d="{notch(x, y, w, h, p)}" fill="{edge}"/>'
    out += f'<path d="{notch(x + p, y + p, w - 2 * p, h - 2 * p, p)}" fill="{fill}"/>'
    return out


def pixels(rows, x, y, p, palette):
    """Draw an ASCII sprite. Each character maps to a color in `palette` ('.' is empty)."""
    paths = {}
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in palette:
                paths.setdefault(ch, []).append(f"M{fmt(x + i * p)} {fmt(y + j * p)}h{fmt(p)}v{fmt(p)}h{fmt(-p)}z")
    return "".join(f'<path d="{"".join(d)}" fill="{palette[ch]}"/>' for ch, d in paths.items())


def ptext(text, x, y, scale, fill, extra=""):
    return f'<path d="{text_path(text, x, y, scale)}" fill="{fill}" {extra}/>'


def mono(text, x, y, size, fill, anchor="start", weight="normal", extra=""):
    return (f'<text x="{fmt(x)}" y="{fmt(y)}" font-family="{MONO}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" {extra}>{escape(text)}</text>')


def wrap(text, width):
    lines, line = [], ""
    for word in text.split():
        if len(line) + len(word) + 1 > width and line:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def discrete(times, values, cycle):
    """keyTimes/values strings for a discrete SMIL animation over `cycle` seconds."""
    pairs = sorted(zip(times, values))
    if pairs[0][0] > 0:
        pairs.insert(0, (0, pairs[0][1]))
    key_times = ";".join(f"{min(t / cycle, 1):.4f}" for t, _ in pairs)
    return key_times, ";".join(str(v) for _, v in pairs)


# MARK: banner

CAT_SIT = [
    "#.....#.....",
    "##...##.....",
    "#######.....",
    "#e##e##.....",
    "#######.....",
    ".#####......",
    "#######.....",
    "########....",
    "########....",
    "#########...",
    "########....",
    ".#.##.#.....",
]
TAIL_UP = [(8, 4), (9, 5), (9, 6), (10, 6), (10, 7), (9, 8)]
TAIL_DOWN = [(8, 9), (9, 9), (10, 9), (11, 8), (11, 7), (11, 6)]


def banner():
    random.seed(7)
    W, H, P = 960, 300, 4
    style = """
    .tw{animation:tw 3s steps(3) infinite}
    @keyframes tw{0%,100%{opacity:1}50%{opacity:.15}}
    .win{animation:win 9s steps(1) infinite}
    @keyframes win{0%,70%{opacity:1}71%,85%{opacity:.1}86%{opacity:1}}
    .shoot{animation:shoot 9s linear infinite;opacity:0}
    @keyframes shoot{0%{transform:translate(0,0);opacity:0}2%{opacity:1}14%{transform:translate(420px,130px);opacity:0}100%{transform:translate(420px,130px);opacity:0}}
    .glow{animation:glow 4s ease-in-out infinite}
    @keyframes glow{0%,100%{opacity:.18}50%{opacity:.35}}
    .eye{animation:blink 5s steps(1) infinite}
    @keyframes blink{0%,90%{opacity:1}91%,95%{opacity:0}96%{opacity:1}}
    .tailA{animation:tailA 1.6s steps(1) infinite}.tailB{animation:tailB 1.6s steps(1) infinite}
    @keyframes tailA{0%,49%{opacity:1}50%,100%{opacity:0}}@keyframes tailB{0%,49%{opacity:0}50%,100%{opacity:1}}
    .shine{animation:shine 6s ease-in-out infinite}
    @keyframes shine{0%,55%{transform:translateX(-120px)}85%,100%{transform:translateX(760px)}}
    """
    body = []
    # Sky in dithered bands.
    bands = ["#07051a", "#0b0726", "#120a33", "#1b0d40", "#26104c", "#341457", "#45185f", "#57195f"]
    band_h = 36
    for i, color in enumerate(bands):
        body.append(f'<rect x="0" y="{i * band_h}" width="{W}" height="{band_h}" fill="{color}"/>')
        if i + 1 < len(bands):
            d = "".join(f"M{x} {(i + 1) * band_h - P}h{P}v{P}h-{P}z" for x in range(0, W, 2 * P))
            d += "".join(f"M{x + P} {(i + 1) * band_h - 2 * P}h{P}v{P}h-{P}z" for x in range(0, W, 4 * P))
            body.append(f'<path d="{d}" fill="{bands[i + 1]}"/>')

    # Stars.
    for _ in range(80):
        x, y = random.randrange(0, W, P), random.randrange(0, 200, P)
        delay, duration = random.uniform(0, 4), random.uniform(2, 5)
        color = random.choice([C["white"], C["white"], "#c4b5fd", "#a5f3fc", "#fde68a"])
        if random.random() < 0.15:
            d = f"M{x} {y - P}h{P}v{3 * P}h-{P}zM{x - P} {y}h{3 * P}v{P}h-{3 * P}z"
        else:
            d = f"M{x} {y}h{P}v{P}h-{P}z"
        body.append(f'<path class="tw" style="animation-delay:{delay:.1f}s;animation-duration:{duration:.1f}s" d="{d}" fill="{color}"/>')

    # Moon with a soft pixel glow.
    mx, my, r = 820, 36, 9
    glow = "".join(f"M{mx + i * P} {my + j * P}h{P}v{P}h-{P}z"
                   for i in range(-4, 2 * r + 4) for j in range(-4, 2 * r + 4)
                   if (i - r + .5) ** 2 + (j - r + .5) ** 2 <= (r + 4) ** 2 and (i + j) % 2 == 0)
    body.append(f'<path class="glow" d="{glow}" fill="#fde68a"/>')
    moon = [[".", "#"][(i - r + .5) ** 2 + (j - r + .5) ** 2 <= r * r] for j in range(2 * r) for i in range(2 * r)]
    rows = ["".join(moon[j * 2 * r:(j + 1) * 2 * r]) for j in range(2 * r)]
    for cx, cy in [(5, 4), (6, 4), (5, 5), (11, 9), (12, 9), (11, 10), (12, 10), (7, 13), (13, 4)]:
        rows[cy] = rows[cy][:cx] + "c" + rows[cy][cx + 1:]
    body.append(pixels(rows, mx, my, P, {"#": "#fef3c7", "c": "#fcd34d"}))

    # Shooting star.
    trail = "".join(f'<rect x="{-i * P}" y="{-i * P * 0.3:.0f}" width="{P}" height="{P}" fill="#fff" opacity="{1 - i / 7:.2f}"/>'
                    for i in range(7))
    body.append(f'<g class="shoot"><g transform="translate(180 24)">{trail}</g></g>')

    # Skyline: a lighter back row and a darker front row, with lit windows.
    def skyline(seed, base_color, roof_color, max_left, max_right, lit_chance):
        random.seed(seed)
        x = 0
        out, windows, blinking = [], [], []
        while x < W:
            w = random.randrange(32, 84, P)
            limit = max_left if x < 640 else max_right
            h = random.randrange(28, limit, P)
            top = H - h
            out.append(f'<rect x="{x}" y="{top}" width="{w}" height="{h}" fill="{base_color}"/>')
            out.append(f'<rect x="{x}" y="{top}" width="{w}" height="{P}" fill="{roof_color}"/>')
            for wy in range(top + 3 * P, H - 2 * P, 3 * P):
                for wx in range(x + 2 * P, x + w - 2 * P, 3 * P):
                    if random.random() < lit_chance:
                        color = random.choice(["#facc15", "#fde68a", "#fde68a", "#67e8f9"])
                        cell = f"M{wx} {wy}h{P}v{P}h-{P}z"
                        (blinking if random.random() < 0.12 else windows).append((cell, color))
            x += w + random.choice([0, 0, P, 2 * P])
        for color in {c for _, c in windows}:
            out.append(f'<path d="{"".join(d for d, c in windows if c == color)}" fill="{color}"/>')
        for d, color in blinking:
            out.append(f'<path class="win" style="animation-delay:{random.uniform(0, 9):.1f}s" d="{d}" fill="{color}"/>')
        return out

    body += skyline(3, "#1a0f3d", "#2a1a5c", 84, 132, 0.18)
    body += skyline(11, "#0b0618", "#1d1240", 56, 92, 0.25)

    # Cat sitting on a roof, tail swishing.
    cat_x, cat_y = 868, H - 92 - 12 * P
    body.append(f'<rect x="{cat_x - 24}" y="{cat_y + 12 * P}" width="96" height="92" fill="#0b0618"/>')
    body.append(f'<rect x="{cat_x - 24}" y="{cat_y + 12 * P}" width="96" height="{P}" fill="#1d1240"/>')
    body.append(pixels([row.replace("e", "#") for row in CAT_SIT], cat_x, cat_y, P, {"#": "#05030f"}))
    eyes = [row.replace("#", ".") for row in CAT_SIT]
    body.append(f'<g class="eye">{pixels(eyes, cat_x, cat_y, P, {"e": C["yellow"]})}</g>')
    for cls, tail in (("tailA", TAIL_UP), ("tailB", TAIL_DOWN)):
        d = "".join(f"M{cat_x + i * P} {cat_y + j * P}h{P}v{P}h-{P}z" for i, j in tail)
        body.append(f'<path class="{cls}" d="{d}" fill="#05030f"/>')

    # Name with hard shadow, banded gradient and a shine sweep.
    name, nx, ny, ns = "YAKSH DALWADI", 56, 64, 8
    name_path = text_path(name, nx, ny, ns)
    body.append('<defs><linearGradient id="nameFill" x1="0" y1="0" x2="0" y2="1">'
                '<stop offset="0" stop-color="#fbcfe8"/><stop offset=".29" stop-color="#fbcfe8"/>'
                '<stop offset=".29" stop-color="#f472b6"/><stop offset=".58" stop-color="#f472b6"/>'
                '<stop offset=".58" stop-color="#c084fc"/><stop offset="1" stop-color="#a855f7"/></linearGradient>'
                f'<clipPath id="nameClip"><path d="{name_path}"/></clipPath></defs>')
    body.append(f'<path d="{text_path(name, nx + ns, ny + ns, ns)}" fill="#1b0b3a"/>')
    body.append(f'<path d="{name_path}" fill="url(#nameFill)"/>')
    body.append(f'<g clip-path="url(#nameClip)"><rect class="shine" x="{nx}" y="{ny}" width="48" height="{7 * ns}" '
                f'fill="#fff" opacity=".45" transform="skewX(-20)"/></g>')

    # Typing tagline.
    phrases = ["APP DEVELOPER", "CLOUD-FOCUSED ENGINEER", "RECENT GRADUATE", "MAC & MOBILE APP BUILDER"]
    ts, ty = 4, ny + 7 * ns + 28
    body.append(ptext(">", nx, ty, ts, C["cyan"]))
    start_x = nx + text_width("> ", ts)
    per_phrase, type_step, erase_step = 3.6, 0.075, 0.025
    cycle = per_phrase * len(phrases)
    cursor_events = []
    defs = []
    for k, phrase in enumerate(phrases):
        t0 = k * per_phrase
        widths = [text_width(phrase[:n], ts) + (ts if n else 0) for n in range(len(phrase) + 1)]
        times, values = [0.0], [0]
        for n in range(1, len(phrase) + 1):
            times.append(t0 + n * type_step)
            values.append(widths[n])
        erase_start = t0 + per_phrase - erase_step * len(phrase) - 0.15
        for n in range(len(phrase) - 1, -1, -1):
            times.append(erase_start + (len(phrase) - n) * erase_step)
            values.append(widths[n])
        cursor_events += [(t, v) for t, v in zip(times[1:], values[1:])]
        key_times, vals = discrete(times + [cycle], values + [0], cycle)
        defs.append(f'<clipPath id="tp{k}"><rect x="{start_x}" y="{ty - 4}" height="{7 * ts + 8}" width="0">'
                    f'<animate attributeName="width" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete" '
                    f'keyTimes="{key_times}" values="{vals}"/></rect></clipPath>')
        body.append(f'<g clip-path="url(#tp{k})">{ptext(phrase, start_x, ty, ts, C["yellow"])}</g>')
    body.append(f'<defs>{"".join(defs)}</defs>')
    times = [t for t, _ in cursor_events] + [cycle]
    values = [start_x + v for _, v in cursor_events] + [start_x]
    key_times, vals = discrete(times, values, cycle)
    body.append(f'<rect y="{ty}" width="{ts * 3}" height="{7 * ts}" fill="{C["cyan"]}" x="{start_x}">'
                f'<animate attributeName="x" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete" '
                f'keyTimes="{key_times}" values="{vals}"/>'
                f'<animate attributeName="opacity" dur=".8s" repeatCount="indefinite" calcMode="discrete" values="1;0"/></rect>')

    body.append(ptext("SWIFT · FLUTTER · AWS · FIREBASE · PYTHON", nx, ty + 7 * ts + 22, 2, "#c4b5fd", 'opacity=".85"'))
    save("banner.svg", svg(W, H, "".join(body), style, "Yakshraj Dalwadi: App Developer, Cloud-Focused Engineer"))


# MARK: terminal

def terminal():
    W, H = 960, 330
    lines = [
        ("whoami", "Yakshraj Dalwadi · App Developer · Cloud-Focused Engineer"),
        ("cat about.txt", "I build scalable, real-world apps: clean UI + smart backends + cloud."),
        ("ls ~/projects", "TaskMaster  ARFit  CampusCrave  StuTrack  NotiBar  BeatBar  DisplayDial"),
        ("echo $NOW", "Recent graduate · going deeper into cloud architecture & backend systems"),
    ]
    size, char_w, x0, y0, gap = 16, 9.8, 36, 82, 30
    prompt = "yaksh@mac:~$ "
    prompt_w = len(prompt) * char_w
    cycle, t = 20.0, 0.6
    body = [frame(0, 0, W, H, fill="#0f0d24")]
    body.append(f'<rect x="8" y="8" width="{W - 20}" height="32" fill="#1b1740"/>')
    for i, color in enumerate([C["red"], C["yellow"], C["green"]]):
        body.append(f'<rect x="{24 + i * 22}" y="18" width="12" height="12" fill="{color}"/>')
    body.append(mono("yaksh@macbook — zsh", W / 2, 30, 13, C["dim"], "middle"))

    defs = []
    for i, (command, output) in enumerate(lines):
        cy = y0 + i * 2 * gap
        oy = cy + gap
        appear = t
        type_end = t + len(command) * 0.07
        out_at = type_end + 0.35
        t = out_at + 0.9
        widths, times = [0], [0.0]
        for n in range(1, len(command) + 1):
            times.append(appear + n * 0.07)
            widths.append(round(n * char_w + 2))
        key_times, vals = discrete(times + [cycle - 0.6, cycle], widths + [widths[-1], 0], cycle)
        defs.append(f'<clipPath id="cmd{i}"><rect x="{x0 + prompt_w}" y="{cy - 20}" height="28" width="0">'
                    f'<animate attributeName="width" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete" '
                    f'keyTimes="{key_times}" values="{vals}"/></rect></clipPath>')
        show = lambda at: discrete([0, at, cycle - 0.6, cycle], [0, 1, 0, 0], cycle)
        kt, vv = show(appear)
        body.append(f'<g opacity="0"><animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" '
                    f'calcMode="discrete" keyTimes="{kt}" values="{vv}"/>'
                    + mono("yaksh@mac", x0, cy, size, C["green"], weight="bold")
                    + mono(":~$", x0 + 9 * char_w, cy, size, C["cyan"], weight="bold") + "</g>")
        body.append(f'<g clip-path="url(#cmd{i})">{mono(command, x0 + prompt_w, cy, size, C["white"])}</g>')
        kt, vv = show(out_at)
        body.append(f'<g opacity="0"><animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" '
                    f'calcMode="discrete" keyTimes="{kt}" values="{vv}"/>'
                    + mono(output, x0, oy, size, "#c4b5fd") + "</g>")
    # Final prompt with a blinking cursor.
    fy = y0 + len(lines) * 2 * gap
    kt, vv = discrete([0, t, cycle - 0.6, cycle], [0, 1, 0, 0], cycle)
    body.append(f'<g opacity="0"><animate attributeName="opacity" dur="{cycle}s" repeatCount="indefinite" '
                f'calcMode="discrete" keyTimes="{kt}" values="{vv}"/>'
                + mono("yaksh@mac", x0, fy, size, C["green"], weight="bold")
                + mono(":~$", x0 + 9 * char_w, fy, size, C["cyan"], weight="bold")
                + f'<rect x="{x0 + prompt_w}" y="{fy - 15}" width="10" height="19" fill="{C["white"]}">'
                  f'<animate attributeName="opacity" dur="1s" repeatCount="indefinite" calcMode="discrete" values="1;0"/></rect></g>')
    body.insert(1, f'<defs>{"".join(defs)}</defs>')
    save("terminal.svg", svg(W, H, "".join(body), "", "Terminal: whoami — Yakshraj Dalwadi, App Developer and Cloud-Focused Engineer"))


# MARK: section headers, buttons, inventory

def header(name, title, color):
    W, H = 960, 56
    # A dark label keeps the white title readable on GitHub's light theme too.
    label_w = 52 + text_width(title, 3) + 20
    body = [frame(0, 4, label_w, 48, 4, fill=C["panel"], edge=color),
            ptext("▶", 18, 18, 3, color, 'class="b"'),
            ptext(title, 46, 18, 3, C["white"])]
    end = label_w + 12
    dash = "".join(f"M{x} 27h8v4h-8z" for x in range(end, W - 8, 16))
    body.append(f'<path d="{dash}" fill="{color}" opacity=".55"/>')
    style = ".b{animation:b 1.2s steps(1) infinite}@keyframes b{0%,60%{opacity:1}61%,100%{opacity:.2}}"
    save(f"h-{name}.svg", svg(W, H, "".join(body), style, title))


def button(name, label, color):
    W, H = 220, 52
    tw = text_width(label, 3)
    body = frame(0, 0, W, H, 4, fill=C["panel"], edge=color)
    body += ptext(label, (W - 4 - tw) / 2, 16, 3, C["white"])
    save(f"btn-{name}.svg", svg(W, H, body, "", label))


STACK = [
    ("MOBILE", C["cyan"], ["FLUTTER", "DART", "SWIFT", "JAVA", "FIREBASE", "SUPABASE"]),
    ("CLOUD & DATA", C["yellow"], ["AWS", "MONGODB", "PYTHON", "PANDAS", "NUMPY"]),
    ("AI / ML", C["pink"], ["TENSORFLOW", "SCIKIT-LEARN"]),
    ("WEB", C["green"], ["JAVASCRIPT", "HTML5", "CSS3"]),
    ("DESIGN", C["purple"], ["PHOTOSHOP", "PREMIERE PRO", "LIGHTROOM", "CANVA"]),
    ("TOOLS", C["orange"], ["GIT", "GITHUB"]),
]


def inventory():
    W = 960
    cols, slot_w, slot_h, gap, top = 5, 180, 46, 6, 24
    left = (W - (cols * slot_w + (cols - 1) * gap)) // 2
    items = [(name, color) for _, color, names in STACK for name in names]
    rows = math.ceil(len(items) / cols)
    H = top + rows * (slot_h + gap) + 56
    gem = [".#.", "###", ".#."]
    body = [frame(0, 0, W, H, fill="#100e26")]
    positions = []
    for index, (name, color) in enumerate(items):
        x = left + (index % cols) * (slot_w + gap)
        y = top + (index // cols) * (slot_h + gap)
        positions.append((x, y))
        body.append(frame(x, y, slot_w, slot_h, 3, fill="#1a1638", edge="#2c2760", shadow=False))
        body.append(f'<g class="g" style="animation-delay:{index * 0.37 % 3:.2f}s">'
                    f'{pixels(gem, x + 10, y + 14, 6, {"#": color})}</g>')
        body.append(ptext(name, x + 34, y + 16, 2, C["white"]))
    # Selection cursor hopping from slot to slot.
    step = 0.55
    values = ";".join(f"{x - 4} {y - 4}" for x, y in positions)
    corners = ""
    for cx, cy, dx, dy in [(0, 0, 1, 1), (slot_w + 8, 0, -1, 1), (0, slot_h + 8, 1, -1), (slot_w + 8, slot_h + 8, -1, -1)]:
        corners += (f'<rect x="{cx if dx > 0 else cx - 12}" y="{cy if dy > 0 else cy - 4}" width="12" height="4" fill="{C["white"]}"/>'
                    f'<rect x="{cx if dx > 0 else cx - 4}" y="{cy if dy > 0 else cy - 12}" width="4" height="12" fill="{C["white"]}"/>')
    body.append(f'<g>{corners}<animateTransform attributeName="transform" type="translate" calcMode="discrete" '
                f'dur="{step * len(items)}s" repeatCount="indefinite" values="{values}"/></g>')
    # Legend.
    lx, ly = left, H - 34
    for label, color, _ in STACK:
        body.append(pixels(gem, lx, ly, 4, {"#": color}))
        body.append(ptext(label, lx + 18, ly + 1, 2, C["dim"]))
        lx += 18 + text_width(label, 2) + 30
    style = ".g{animation:g 3s steps(2) infinite}@keyframes g{0%,100%{opacity:1}50%{opacity:.45}}"
    save("inventory.svg", svg(W, H, "".join(body), style, "Tech stack: " + ", ".join(n for n, _ in items)))


# MARK: project cards

def card(name, title, tags, description, accent, art, art_style=""):
    W, H, P = 460, 250, 5
    body = [frame(0, 0, W, H, 4, fill=C["panel"], edge=accent)]
    body.append(ptext(title, 24, 24, 3, C["white"]))
    x = 24
    for tag in tags:
        tw = text_width(tag, 2)
        body.append(f'<rect x="{x}" y="58" width="{tw + 16}" height="22" fill="{accent}" opacity=".18"/>')
        body.append(ptext(tag, x + 8, 63, 2, accent))
        x += tw + 26
    for i, line in enumerate(wrap(description, 34)[:5]):
        body.append(mono(line, 24, 110 + i * 20, 13, "#d4d0f5"))
    body.append(ptext("▶ VIEW REPO", 24, H - 36, 2, C["dim"]))
    body.append(f'<g transform="translate(300 78)">{art}</g>')
    save(f"card-{name}.svg", svg(W, H, "".join(body), art_style, f"{title}: {description}"))


def art_notibar():
    P = 5
    bell = ["..##..", ".####.", ".####.", "######", "......", "..##.."]
    body = f'<g class="bell">{pixels(bell, 52, 4, P, {"#": C["yellow"]})}</g>'
    body += f'<rect class="dot" x="86" y="2" width="10" height="10" fill="{C["red"]}"/>'
    body += '<rect x="0" y="60" width="140" height="34" fill="#000"/><rect x="0" y="60" width="140" height="34" fill="none" stroke="#3f3a6e" stroke-width="2"/>'
    body += f'<rect x="114" y="66" width="20" height="22" fill="{C["purple"]}"/>'
    body += (f'<clipPath id="strip"><rect x="2" y="62" width="108" height="30"/></clipPath>'
             f'<g clip-path="url(#strip)"><g class="pill"><rect x="10" y="66" width="96" height="22" fill="#2a2650"/>'
             f'<rect x="14" y="70" width="14" height="14" fill="{C["green"]}"/>'
             f'<rect x="34" y="74" width="54" height="6" fill="{C["white"]}"/></g></g>')
    style = (".pill{animation:pill 4s steps(8) infinite}@keyframes pill{0%{transform:translateX(130px)}25%,80%{transform:translateX(0)}100%{transform:translateX(130px)}}"
             ".bell{transform-box:fill-box;transform-origin:50% 0;animation:bell 4s steps(2) infinite}"
             "@keyframes bell{0%,20%{transform:rotate(0)}24%{transform:rotate(-14deg)}28%{transform:rotate(14deg)}32%{transform:rotate(-8deg)}36%,100%{transform:rotate(0)}}"
             ".dot{animation:dot 4s steps(1) infinite}@keyframes dot{0%,22%{opacity:0}23%,100%{opacity:1}}")
    return body, style


def art_beatbar():
    random.seed(4)
    body, style = '<defs><linearGradient id="eq" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#22d3ee"/><stop offset=".33" stop-color="#22d3ee"/><stop offset=".33" stop-color="#a855f7"/><stop offset=".66" stop-color="#a855f7"/><stop offset=".66" stop-color="#f472b6"/><stop offset="1" stop-color="#fbcfe8"/></linearGradient></defs>', ""
    for i in range(9):
        x = i * 15
        body += f'<rect class="eq{i}" x="{x}" y="10" width="11" height="90" fill="url(#eq)"/>'
        frames = ";".join(f"{random.choice([0.15, 0.3, 0.5, 0.7, 0.9, 1])}" for _ in range(4))
        stops = frames.split(";")
        style += (f".eq{i}{{transform-box:fill-box;transform-origin:50% 100%;animation:eq{i} {random.uniform(0.9, 1.6):.2f}s steps(3) infinite alternate}}"
                  f"@keyframes eq{i}{{0%{{transform:scaleY({stops[0]})}}33%{{transform:scaleY({stops[1]})}}66%{{transform:scaleY({stops[2]})}}100%{{transform:scaleY({stops[3]})}}}}")
    body += "".join(f'<rect x="0" y="{y}" width="140" height="2" fill="{C["panel"]}"/>' for y in range(10, 100, 9))
    return body, style


def art_displaydial():
    body = '<rect x="10" y="0" width="120" height="74" fill="#2c2760"/><rect x="16" y="6" width="108" height="62" fill="#0b0618"/>'
    body += '<rect class="lit" x="16" y="6" width="108" height="62" fill="#fde68a"/>'
    sun = ["..#.#..", "#.###.#", ".#####.", "#######", ".#####.", "#.###.#", "..#.#.."]
    body += pixels(sun, 53, 20, 5, {"#": C["orange"]})
    body += '<rect x="62" y="74" width="16" height="10" fill="#2c2760"/><rect x="44" y="84" width="52" height="6" fill="#2c2760"/>'
    body += f'<rect x="10" y="106" width="120" height="6" fill="#2c2760"/><rect class="knob" x="10" y="100" width="18" height="18" fill="{C["white"]}"/>'
    style = (".lit{animation:lit 5s steps(6) infinite alternate}@keyframes lit{0%{opacity:.05}100%{opacity:.65}}"
             ".knob{animation:knob 5s steps(6) infinite alternate}@keyframes knob{0%{transform:translateX(0)}100%{transform:translateX(102px)}}")
    return body, style


def art_taskmaster():
    body, style = "", ""
    for i in range(4):
        y = i * 28
        body += f'<rect x="0" y="{y}" width="20" height="20" fill="none" stroke="{C["dim"]}" stroke-width="4"/>'
        body += f'<rect x="34" y="{y + 7}" width="{100 - i * 14}" height="6" fill="#3a3570"/>'
        check = [".....#", "....#.", "#..#..", ".##...", "..#..."]
        body += f'<g class="ck{i}">{pixels(check, 2, y + 2, 3.4, {"#": C["green"]})}</g>'
        style += (f".ck{i}{{animation:ck{i} 6s steps(1) infinite}}"
                  f"@keyframes ck{i}{{0%,{10 + i * 18}%{{opacity:0}}{11 + i * 18}%,92%{{opacity:1}}93%,100%{{opacity:0}}}}")
    return body, style


def art_arfit():
    dumbbell = ["##..........##", "##..........##", "##############", "##..........##", "##..........##"]
    body = f'<g class="lift">{pixels(dumbbell, 0, 30, 10, {"#": C["cyan"]})}</g>'
    body += f'<rect x="20" y="118" width="100" height="6" fill="#3a3570"/>'
    body += "".join(f'<rect class="sp" style="animation-delay:{d}s" x="{x}" y="{y}" width="6" height="6" fill="{C["yellow"]}"/>'
                    for x, y, d in [(4, 6, 0), (128, 14, .5), (66, 0, 1)])
    style = (".lift{animation:lift 1.6s steps(4) infinite alternate}@keyframes lift{0%{transform:translateY(40px)}100%{transform:translateY(0)}}"
             ".sp{animation:sp 1.5s steps(1) infinite}@keyframes sp{0%,50%{opacity:1}51%,100%{opacity:0}}")
    return body, style


def art_campuscrave():
    bowl = ["##############", ".############.", "..##########..", "...########..."]
    food = ["..#.##.#.##...", ".############."]
    body = pixels(food, 0, 50, 10, {"#": C["orange"]}) + pixels(bowl, 0, 70, 10, {"#": C["pink"]})
    for i, x in enumerate([30, 70, 110]):
        body += f'<g class="st" style="animation-delay:{i * 0.5}s">{pixels(["#.", ".#", "#.", ".#"], x, 4, 6, {"#": "#c4b5fd"})}</g>'
    style = ".st{animation:st 1.5s steps(3) infinite}@keyframes st{0%{transform:translateY(16px);opacity:0}40%{opacity:1}100%{transform:translateY(-6px);opacity:0}}"
    return body, style


def art_stutrack():
    r, cx, cy = 52, 70, 64
    ring = "".join(f'<rect x="{cx + math.cos(a) * r - 4:.0f}" y="{cy + math.sin(a) * r - 4:.0f}" width="8" height="8" fill="{C["purple"]}"/>'
                   for a in [i * math.pi / 12 for i in range(24)])
    body = ring + f'<rect x="{cx - 8}" y="0" width="16" height="8" fill="{C["purple"]}"/>'
    body += f'<g class="hand"><rect x="{cx - 3}" y="{cy - 40}" width="6" height="40" fill="{C["yellow"]}"/></g>'
    body += f'<rect x="{cx - 6}" y="{cy - 6}" width="12" height="12" fill="{C["white"]}"/>'
    style = f".hand{{transform-origin:{cx}px {cy}px;animation:hand 6s steps(12) infinite}}@keyframes hand{{to{{transform:rotate(360deg)}}}}"
    return body, style


def art_smarttask():
    grid = "".join(f'<rect x="{x}" y="20" width="2" height="100" fill="#2c2760"/>' for x in range(0, 141, 20))
    grid += "".join(f'<rect x="0" y="{y}" width="140" height="2" fill="#2c2760"/>' for y in range(20, 121, 20))
    pin = [".####.", "##..##", "##..##", ".####.", "..##..", "..##.."]
    body = grid + f'<rect class="ring" x="50" y="88" width="40" height="16" fill="none" stroke="{C["green"]}" stroke-width="4"/>'
    body += f'<g class="pin">{pixels(pin, 52, 30, 6, {"#": C["red"]})}</g>'
    style = (".pin{animation:pin 1.2s steps(3) infinite alternate}@keyframes pin{0%{transform:translateY(0)}100%{transform:translateY(-16px)}}"
             ".ring{transform-box:fill-box;transform-origin:center;animation:ring 1.2s steps(3) infinite}@keyframes ring{0%{transform:scale(.4);opacity:1}100%{transform:scale(1.5);opacity:0}}")
    return body, style


def art_workhive():
    hexes = [(0, 30), (44, 4), (44, 56), (88, 30), (88, 82), (0, 82)]
    shape = [".####.", "######", "######", ".####."]
    body = ""
    for i, (x, y) in enumerate(hexes):
        body += f'<g class="hx" style="animation-delay:{i * 0.4}s">{pixels(shape, x + 10, y, 7, {"#": C["yellow"]})}</g>'
    style = ".hx{animation:hx 2.4s steps(2) infinite}@keyframes hx{0%,100%{opacity:1}50%{opacity:.35}}"
    return body, style


def projects():
    entries = [
        ("notibar", "NOTIBAR", ["SWIFT", "MACOS"], "Your Mac's notifications on the Touch Bar. Tap a sender to read the message, like an Apple Watch.", C["green"], art_notibar),
        ("beatbar", "BEATBAR", ["SWIFT", "MACOS"], "Pixel-art music visualizer for the Touch Bar: bars, waves, fire, stars and plasma that sync to your music.", C["pink"], art_beatbar),
        ("displaydial", "DISPLAYDIAL", ["SWIFT", "MACOS"], "Control an external monitor's real brightness, contrast and colors from the menu bar over DDC/CI.", C["orange"], art_displaydial),
        ("taskmaster", "TASKMASTER", ["FLUTTER", "DART"], "Task assignment for small businesses: delegate work, set deadlines, track status, get notified.", C["green"], art_taskmaster),
        ("arfit", "ARFIT", ["FLUTTER", "AR"], "Fitness app with curated workout and diet plans, plus AR workouts and body tracking for proper form.", C["cyan"], art_arfit),
        ("campuscrave", "CAMPUSCRAVE", ["FLUTTER", "DART"], "Cross-platform canteen ordering for campuses: browse the menu, order in real time, see order history.", C["pink"], art_campuscrave),
        ("stutrack", "STUTRACK", ["MOBILE", "STUDY"], "Study timer and productivity companion: focus sessions, streaks, leaderboards and analytics.", C["purple"], art_stutrack),
        ("smarttask", "SMARTTASK", ["MOBILE", "MAPS"], "Context-aware task manager with location-based reminders and Google Places-powered smart notifications.", C["red"], art_smarttask),
        ("workhive", "WORKHIVE", ["MOBILE", "BIDDING"], "Bidding platform where clients post projects and freelancers bid, with real-time chat and payments.", C["yellow"], art_workhive),
    ]
    for name, title, tags, description, accent, art in entries:
        body, style = art()
        card(name, title, tags, description, accent, body, style)


# MARK: footer

CAT_WALK = [
    ["#...#.......",
     "##.##.......",
     "#####......#",
     "#e#e#.....#.",
     "#####.....#.",
     ".##########.",
     ".##########.",
     ".#.#....#.#.",
     "#..#...#..#."],
    ["#...#.......",
     "##.##.......",
     "#####.....#.",
     "#e#e#......#",
     "#####......#",
     ".##########.",
     ".##########.",
     "..#.#..#.#..",
     "..#.#..#.#.."],
]


def footer():
    W, H, P = 960, 150, 4
    body = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="{C["bg"]}"/>']
    title = "THANKS FOR STOPPING BY!"
    body.append(ptext(title, (W - text_width(title, 4)) / 2, 22, 4, C["white"]))
    sub = "PRESS ★ TO CONTINUE"
    body.append(ptext(sub, (W - text_width(sub, 2)) / 2, 64, 2, C["yellow"], 'class="b"'))
    ground_y = H - 28
    body.append(f'<rect x="0" y="{ground_y}" width="{W}" height="28" fill="#1a0f3d"/>')
    grass = "".join(f"M{x} {ground_y - P}h{P}v{P}h-{P}z" for x in range(0, W, 3 * P))
    body.append(f'<path d="{grass}" fill="{C["green"]}"/><rect x="0" y="{ground_y}" width="{W}" height="{P}" fill="#22c55e"/>')
    cat_y = ground_y - 9 * P
    frames = "".join(
        f'<g class="f{i}">{pixels([r.replace("e", "#") for r in sprite], 0, 0, P, {"#": "#f5f3ff"})}'
        f'{pixels([r.replace("#", ".") for r in sprite], 0, 0, P, {"e": "#0d0b1e"})}</g>'
        for i, sprite in enumerate(CAT_WALK))
    body.append(f'<g class="walk"><g transform="translate(0 {cat_y})">{frames}</g></g>')
    style = (".b{animation:b 1s steps(1) infinite}@keyframes b{0%,60%{opacity:1}61%,100%{opacity:0}}"
             f".walk{{animation:walk 14s linear infinite}}@keyframes walk{{0%{{transform:translateX(-60px)}}100%{{transform:translateX({W + 20}px)}}}}"
             ".f0{animation:f0 .4s steps(1) infinite}.f1{animation:f1 .4s steps(1) infinite}"
             "@keyframes f0{0%,49%{opacity:1}50%,100%{opacity:0}}@keyframes f1{0%,49%{opacity:0}50%,100%{opacity:1}}")
    save("footer.svg", svg(W, H, "".join(body), style, "Thanks for stopping by!"))


if __name__ == "__main__":
    banner()
    terminal()
    inventory()
    projects()
    footer()
    header("about", "ABOUT ME", C["cyan"])
    header("stack", "INVENTORY", C["yellow"])
    header("mac", "MAC APPS", C["pink"])
    header("mobile", "MOBILE APPS", C["green"])
    header("stats", "PLAYER STATS", C["purple"])
    button("linkedin", "LINKEDIN", C["cyan"])
    button("portfolio", "PORTFOLIO", C["pink"])
