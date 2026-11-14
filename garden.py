"""Animated isometric garden for the Home page: a plot of land that grows with the player's XP.

Pure SVG + CSS animations (no JavaScript), rendered with st.markdown(..., unsafe_allow_html=True).

How XP drives the scene (FULL_XP = the "Stacker" rank, i.e. the whole learning path):
- progress p = xp / FULL_XP, clamped to 0..1
- p = 0: bare brown earth, dry cracks, a tumbleweed and dust. No gardener.
- the ground turns from brown to green, grass tufts and flowers spread around the beds
- 36 vegetable beds (6 x 6): each one sprouts, grows, then bears fruit, one after the other
- trees appear around the plot, a fence goes up, butterflies and birds come along
- gardeners are hired at GARDENER_XP thresholds and walk circular paths across the plot
- p = 1: every bed is full grown (tomatoes, corn, pumpkins...), all trees have apples
"""
import math
import random

FULL_XP = 4000
GARDENER_XP = [100, 250, 500, 1300, 2500, 4000]   # 1st gardener at 100 XP ... 6th at 4000 XP

# Scene geometry (SVG user units). The plot is a 2:1 isometric diamond.
VB_W, VB_H = 800, 480
CX, TOP, W, H = 400, 112, 640, 320     # diamond centre x, top y, full width, full height
DEPTH = 26                             # thickness of the soil block
N = 6                                  # beds per side
LO, HI = 0.15, 0.85                    # beds area inside the plot (u, v in 0..1)
CELL = (HI - LO) / N
CROPS = ["lettuce", "tomato", "carrot", "corn", "cabbage", "pumpkin"]   # one crop per row

GARDENERS = [  # shirt, overalls, skin, tool, path (centre u, centre v, radius, direction)
    ("#e9724c", "#3d6fb6", "#f1c7a0", "can", (0.50, 0.50, 0.22, 1)),
    ("#f4d35e", "#5a7d3a", "#8d5a3b", "hoe", (0.34, 0.63, 0.13, -1)),
    ("#7ec4cf", "#8a5a3c", "#e0ac7e", "basket", (0.64, 0.36, 0.14, 1)),
    ("#d987c1", "#3b5a8c", "#c58c5c", "can", (0.32, 0.32, 0.12, -1)),
    ("#f2efe6", "#b8543a", "#f3d2b3", "hoe", (0.68, 0.68, 0.12, 1)),
    ("#9ad17a", "#4b4f8c", "#6b4429", "basket", (0.50, 0.50, 0.335, -1)),
]


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
def progress(xp):
    return max(0.0, min(1.0, xp / FULL_XP))


def gardener_count(xp):
    return sum(xp >= t for t in GARDENER_XP)


def next_gardener_xp(xp):
    return next((t for t in GARDENER_XP if xp < t), None)


# ---------------------------------------------------------------------------
# Geometry and colour helpers
# ---------------------------------------------------------------------------
def iso(u, v, h=0.0):
    """Plot coordinates (u, v in 0..1, height h in units) -> SVG point."""
    return CX + (u - v) * W / 2, TOP + (u + v) * H / 2 - h


def pts(*points):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def mix(a, b, t):
    """Blend two #rrggbb colours (t = 0 -> a, 1 -> b)."""
    t = max(0.0, min(1.0, t))
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def ramp(p, start, end):
    """0 before `start`, 1 after `end`, linear in between."""
    return max(0.0, min(1.0, (p - start) / (end - start)))


def in_ring(u, v, margin=0.03):
    """True when (u, v) is on the grass ring around the beds (and not on the shed corner)."""
    beds = LO - margin <= u <= HI + margin and LO - margin <= v <= HI + margin
    shed = u < 0.16 and v < 0.16
    return not beds and not shed and 0.02 < u < 0.98 and 0.02 < v < 0.98


# ---------------------------------------------------------------------------
# Static art (each drawn with its base at 0,0)
# ---------------------------------------------------------------------------
def sprout():
    return ('<path d="M0 0V-6" stroke="#6fbf4a" stroke-width="1.6"/>'
            '<ellipse cx="-3" cy="-7" rx="3.4" ry="1.8" fill="#8fd65e" transform="rotate(-25 -3 -7)"/>'
            '<ellipse cx="3" cy="-7.5" rx="3.4" ry="1.8" fill="#7cc94f" transform="rotate(25 3 -7.5)"/>')


def crop(kind, fruit):
    if kind == "lettuce":
        return ('<circle cx="-5" cy="-4" r="5" fill="#4f9e42"/><circle cx="5" cy="-4" r="5" fill="#5aaa48"/>'
                '<circle cx="0" cy="-7" r="6.2" fill="#8fd36b"/><circle cx="0" cy="-6" r="3" fill="#c3ef9c"/>')
    if kind == "cabbage":
        return ('<ellipse cx="0" cy="-5" rx="9.5" ry="6" fill="#3f8a4a"/><circle cx="0" cy="-7.5" r="6.5" fill="#a9dc8d"/>'
                '<path d="M0 -13V-3M-3.5 -10.5 0 -6.5 3.5 -10.5" stroke="#78b866" stroke-width="1" fill="none"/>')
    if kind == "carrot":
        top = '<path d="M-3 0H3L0 6Z" fill="#f08a2c"/>' if fruit else '<path d="M-1.5 0H1.5L0 3Z" fill="#f0a35c"/>'
        return (top + '<g stroke="#5cb84a" stroke-width="1.8" fill="none" stroke-linecap="round">'
                '<path d="M0 0C-2 -7 -6 -11 -8 -15"/><path d="M0 0C0 -8 1 -13 0 -18"/><path d="M0 0C2 -7 6 -11 8 -14"/></g>'
                '<g fill="#7bd05e"><circle cx="-8" cy="-15" r="2.2"/><circle cx="0" cy="-18" r="2.4"/><circle cx="8" cy="-14" r="2.2"/></g>')
    if kind == "tomato":
        fruits = ('<g fill="#e5483b"><circle cx="-4.5" cy="-9" r="2.8"/><circle cx="4" cy="-14" r="2.6"/>'
                  '<circle cx="-2" cy="-20" r="2.4"/><circle cx="3.5" cy="-6" r="2.2"/></g>'
                  '<g fill="#ffb3a8"><circle cx="-5.3" cy="-9.8" r=".8"/><circle cx="3.2" cy="-14.8" r=".8"/></g>') if fruit else ""
        return ('<rect x="-.8" y="-27" width="1.6" height="27" fill="#9a7148"/>'
                '<ellipse cx="-3" cy="-10" rx="6" ry="8" fill="#3f8a3e"/><ellipse cx="3" cy="-16" rx="6" ry="8" fill="#55a64a"/>'
                '<ellipse cx="-1" cy="-21" rx="4.5" ry="5" fill="#64b455"/>' + fruits)
    if kind == "corn":
        cob = ('<ellipse cx="3.5" cy="-20" rx="2.6" ry="6" fill="#f2d25c"/>'
               '<path d="M3.5 -14C1 -16 1 -22 2.5 -26" stroke="#8cc65a" stroke-width="1.6" fill="none"/>') if fruit else ""
        return ('<path d="M0 0V-34" stroke="#7fb24a" stroke-width="2.4"/>'
                '<g stroke="#6aa845" stroke-width="2" fill="none" stroke-linecap="round">'
                '<path d="M0 -8C-6 -10 -10 -9 -13 -5"/><path d="M0 -16C6 -18 10 -17 13 -13"/>'
                '<path d="M0 -24C-5 -27 -9 -27 -11 -24"/><path d="M0 -31C3 -35 6 -36 8 -35"/></g>'
                '<path d="M0 -34l-1.5 -5M0 -34l1.5 -5" stroke="#d8c06a" stroke-width="1.2"/>' + cob)
    if kind == "pumpkin":
        body = ('<ellipse cx="0" cy="-5" rx="8" ry="5.5" fill="#f0892e"/><ellipse cx="0" cy="-5" rx="3.5" ry="5.5" fill="#f7a04a"/>'
                '<path d="M-4 -9.5C-5 -6 -5 -3 -4 -.5M4 -9.5C5 -6 5 -3 4 -.5" stroke="#d06f1f" fill="none"/>'
                '<rect x="-.8" y="-13" width="1.8" height="4" rx=".8" fill="#6b8a2f"/>') if fruit else ""
        return ('<ellipse cx="-8" cy="-3" rx="6" ry="4" fill="#3f8a3e"/><ellipse cx="8" cy="-4" rx="6" ry="4" fill="#4f9a47"/>'
                '<path d="M-12 0C-6 2 6 2 12 -1" stroke="#5aa64a" stroke-width="1.4" fill="none"/>' + body)
    return sprout()


def tree(apples, sway_delay):
    fruit = ('<g fill="#e5483b"><circle cx="-8" cy="-30" r="2.6"/><circle cx="7" cy="-38" r="2.6"/>'
             '<circle cx="10" cy="-25" r="2.4"/><circle cx="-2" cy="-44" r="2.4"/><circle cx="-12" cy="-22" r="2.2"/></g>') if apples else ""
    return ('<ellipse cx="0" cy="0" rx="16" ry="6" fill="#000" opacity=".18"/>'
            '<path d="M-3 0 -2 -24H2L3 0Z" fill="#7a5233"/><path d="M0 -16 7 -22" stroke="#7a5233" stroke-width="2.4"/>'
            f'<g class="g-sway g-slow" style="animation-delay:-{sway_delay:.1f}s">'
            '<circle cx="0" cy="-34" r="16" fill="#3f8d45"/><circle cx="-11" cy="-26" r="11" fill="#357a3c"/>'
            '<circle cx="11" cy="-27" r="11" fill="#4a9e4c"/><circle cx="-4" cy="-41" r="8.5" fill="#5db35a"/>'
            f'<circle cx="6" cy="-36" r="5" fill="#6cc266" opacity=".7"/>{fruit}</g>')


def shed():
    """Small wooden shed on the back corner of the plot."""
    u, v, du, dv, h, roof = 0.035, 0.035, 0.085, 0.085, 44, 20
    left = pts(iso(u, v + dv), iso(u + du, v + dv), iso(u + du, v + dv, h), iso(u, v + dv, h))
    right = pts(iso(u + du, v), iso(u + du, v + dv), iso(u + du, v + dv, h), iso(u + du, v, h))
    gable = pts(iso(u, v + dv, h), iso(u + du, v + dv, h), iso(u + du / 2, v + dv, h + roof))
    slope = pts(iso(u + du / 2, v, h + roof), iso(u + du / 2, v + dv, h + roof), iso(u + du, v + dv, h - 2), iso(u + du, v, h - 2))
    back_slope = pts(iso(u + du / 2, v, h + roof), iso(u + du / 2, v + dv, h + roof), iso(u, v + dv, h - 2), iso(u, v, h - 2))
    dx0, dy0 = iso(u + du * 0.38, v + dv)
    dx1, _ = iso(u + du * 0.72, v + dv)
    door = pts((dx0, dy0), (dx1, dy0 + (dx1 - dx0) / 2), (dx1, dy0 + (dx1 - dx0) / 2 - 26), (dx0, dy0 - 26))
    wx, wy = iso(u + du, v + dv * 0.5, h * 0.62)
    return (f'<polygon points="{back_slope}" fill="#8a3f2f"/>'
            f'<polygon points="{left}" fill="#a8774a"/><polygon points="{right}" fill="#8c5f38"/>'
            f'<polygon points="{gable}" fill="#b98656"/><polygon points="{door}" fill="#6a4426"/>'
            f'<polygon points="{slope}" fill="#b4513b"/>'
            f'<polygon points="{pts((wx - 4, wy - 7), (wx + 6, wy - 2), (wx + 6, wy + 7), (wx - 4, wy + 2))}" fill="#f6dd8a" opacity=".85"/>')


def fence_posts(edge, p):
    """Fence along one edge: 'back_u' (v=0), 'back_v' (u=0), 'front_u' (v=1), 'front_v' (u=1)."""
    if p < 0.1:
        return ""
    count = 12
    shown = max(2, round(count * ramp(p, 0.1, 0.3)))        # the fence goes up post by post
    posts, tops = [], []
    for k in range(shown):
        t = 0.02 + k * 0.96 / (count - 1)
        u, v = {"back_u": (t, 0.0), "back_v": (0.0, t), "front_u": (t, 1.0), "front_v": (1.0, t)}[edge]
        x, y = iso(u, v)
        posts.append(f'<rect x="{x - 1.6:.1f}" y="{y - 15:.1f}" width="3.2" height="15" rx="1" fill="#a07448"/>')
        tops.append((x, y))
    rails = "".join(f'<polyline points="{pts(*[(x, y - d) for x, y in tops])}" fill="none" stroke="#b88a57" stroke-width="1.6"/>'
                    for d in (5, 11))
    return rails + "".join(posts)


# ---------------------------------------------------------------------------
# Moving things
# ---------------------------------------------------------------------------
def gardener_svg(shirt, pants, skin, tool):
    if tool == "can":
        held = ('<g transform="translate(5,-15)"><rect x="0" y="0" width="7" height="6" rx="1.6" fill="#6aa9d8"/>'
                '<path d="M6.5 1.5 11 -2" stroke="#6aa9d8" stroke-width="1.6" stroke-linecap="round"/>'
                '<path d="M1 0Q3.5 -4 6 0" stroke="#4f8fc0" stroke-width="1.1" fill="none"/>'
                '<g fill="#9fd4ff"><circle class="g-drop" cx="11.5" cy="0" r=".9"/>'
                '<circle class="g-drop" cx="12.5" cy="0" r=".8" style="animation-delay:-.3s"/>'
                '<circle class="g-drop" cx="10.8" cy="0" r=".8" style="animation-delay:-.6s"/></g></g>')
    elif tool == "hoe":
        held = ('<path d="M3 -18 13 2" stroke="#8a6238" stroke-width="1.6" stroke-linecap="round"/>'
                '<path d="M11.5 1.5 16 -.5" stroke="#9aa3a8" stroke-width="2.4" stroke-linecap="round"/>')
    else:
        held = ('<g transform="translate(4,-13)"><path d="M0 0H9L8 6H1Z" fill="#c99a5b"/>'
                '<path d="M1.5 0Q4.5 -5 7.5 0" stroke="#a07448" stroke-width="1.1" fill="none"/>'
                '<circle cx="3" cy="-.5" r="1.8" fill="#e5483b"/><circle cx="6.3" cy="-.8" r="1.7" fill="#f0892e"/></g>')
    return ('<ellipse cx="0" cy="0" rx="8" ry="3" fill="#000" opacity=".25"/>'
            '<g class="g-bob">'
            f'<g class="g-leg"><rect x="-3.6" y="-11" width="3.2" height="11" rx="1.3" fill="{pants}"/>'
            '<rect x="-4.2" y="-1.6" width="4.4" height="2" rx="1" fill="#3a2a1e"/></g>'
            f'<g class="g-leg g-leg2"><rect x=".4" y="-11" width="3.2" height="11" rx="1.3" fill="{pants}"/>'
            '<rect x="0" y="-1.6" width="4.4" height="2" rx="1" fill="#3a2a1e"/></g>'
            f'<rect x="-5" y="-23.5" width="10" height="13.5" rx="3.2" fill="{shirt}"/>'
            f'<rect x="-4" y="-19" width="8" height="9" rx="1.6" fill="{pants}"/>'
            f'<rect x="-6.5" y="-22" width="2.8" height="9" rx="1.4" fill="{shirt}" transform="rotate(12 -5 -22)"/>'
            f'{held}'
            f'<rect x="3.2" y="-22" width="2.8" height="9" rx="1.4" fill="{shirt}" transform="rotate(-28 4.5 -22)"/>'
            f'<circle cx="0" cy="-28" r="4.7" fill="{skin}"/><circle cx="2.1" cy="-28.4" r=".75" fill="#2b1d14"/>'
            '<ellipse cx="0" cy="-31" rx="8.2" ry="2.3" fill="#e8c56a"/><path d="M-4.3 -31Q0 -38 4.3 -31Z" fill="#d9b04f"/>'
            '<path d="M-4 -32H4" stroke="#b5483a" stroke-width="1.2"/>'
            '</g>')


def walk_keyframes(name, cu, cv, r, direction, steps=32):
    """Keyframes that move a gardener around an iso circle, facing the way they walk. Returns (css, duration, start)."""
    frames, prev, length = [], None, 0.0
    pts_ = []
    for k in range(steps + 1):
        a = direction * 2 * math.pi * k / steps
        x, y = iso(cu + r * math.cos(a), cv + r * math.sin(a))
        dx = direction * (-math.sin(a) - math.cos(a))            # sign of the screen x-velocity
        pts_.append((x, y, 1 if dx >= 0 else -1))
        if prev:
            length += math.hypot(x - prev[0], y - prev[1])
        prev = (x, y)
    for k, (x, y, face) in enumerate(pts_):
        frames.append(f"{k * 100 / steps:.2f}%{{transform:translate({x:.1f}px,{y:.1f}px) scaleX({face})}}")
    duration = max(14.0, length / 20)                            # ~20 units per second, a calm walk
    return f"@keyframes {name}{{{''.join(frames)}}}", duration, pts_[0]


def flyer_keyframes(name, cx, cy, rx, ry, steps=12, seed=0):
    """A wandering loop (butterflies)."""
    rng = random.Random(seed)
    frames = []
    for k in range(steps + 1):
        a = 2 * math.pi * k / steps
        j = 0 if k in (0, steps) else rng.uniform(-8, 8)
        x, y = cx + rx * math.cos(a) + j, cy + ry * math.sin(2 * a) + j / 2
        frames.append(f"{k * 100 / steps:.1f}%{{transform:translate({x:.1f}px,{y:.1f}px)}}")
    return f"@keyframes {name}{{{''.join(frames)}}}"


def butterfly(color):
    return (f'<g class="g-wing"><ellipse cx="-3" cy="0" rx="3.4" ry="2.4" fill="{color}"/></g>'
            f'<g class="g-wing g-wing2"><ellipse cx="3" cy="0" rx="3.4" ry="2.4" fill="{color}"/></g>'
            '<rect x="-.5" y="-2" width="1" height="4.5" rx=".5" fill="#3a2a1e"/>')


# ---------------------------------------------------------------------------
# The scene
# ---------------------------------------------------------------------------
CSS = (
    ".garden{position:relative;border-radius:20px;overflow:hidden;border:1px solid var(--line);margin:0 0 6px}"
    ".garden svg{display:block;width:100%;height:auto}"
    ".g-sway{transform-box:fill-box;transform-origin:50% 100%;animation:g-sway 3.2s ease-in-out infinite alternate}"
    ".g-slow{animation-duration:5.5s}"
    "@keyframes g-sway{from{transform:rotate(-3deg)}to{transform:rotate(3deg)}}"
    ".g-leg{transform-box:fill-box;transform-origin:50% 0;animation:g-step .45s ease-in-out infinite alternate}"
    ".g-leg2{animation-direction:alternate-reverse}"
    "@keyframes g-step{from{transform:rotate(24deg)}to{transform:rotate(-24deg)}}"
    ".g-bob{animation:g-bob .45s ease-in-out infinite alternate}"
    "@keyframes g-bob{from{transform:translateY(0)}to{transform:translateY(-1.3px)}}"
    ".g-drop{animation:g-drop .9s linear infinite}"
    "@keyframes g-drop{0%{transform:translate(0,0);opacity:1}100%{transform:translate(1.5px,12px);opacity:0}}"
    ".g-cloud{animation:g-drift linear infinite}"
    "@keyframes g-drift{from{transform:translateX(-260px)}to{transform:translateX(1060px)}}"
    ".g-sun{transform-box:fill-box;transform-origin:50% 50%;animation:g-pulse 4s ease-in-out infinite alternate}"
    "@keyframes g-pulse{from{transform:scale(1);opacity:.55}to{transform:scale(1.12);opacity:.85}}"
    ".g-wing{transform-box:fill-box;transform-origin:100% 50%;animation:g-flap .16s ease-in-out infinite alternate}"
    ".g-wing2{transform-origin:0 50%}"
    "@keyframes g-flap{from{transform:scaleX(1)}to{transform:scaleX(.25)}}"
    ".g-dust{animation:g-dust linear infinite}"
    "@keyframes g-dust{0%{transform:translate(0,0);opacity:0}15%{opacity:.7}100%{transform:translate(140px,-30px);opacity:0}}"
    ".g-tumble{animation:g-tumble 13s linear infinite}"
    "@keyframes g-tumble{0%{transform:translate(150px,272px)}25%{transform:translate(290px,266px)}"
    "50%{transform:translate(430px,272px)}75%{transform:translate(570px,266px)}100%{transform:translate(690px,272px)}}"
    ".g-roll{transform-box:fill-box;transform-origin:50% 50%;animation:g-roll 1.6s linear infinite}"
    "@keyframes g-roll{to{transform:rotate(360deg)}}"
    ".g-bird{animation:g-birdfly linear infinite}"
    "@keyframes g-birdfly{from{transform:translate(-60px,0)}to{transform:translate(880px,-40px)}}"
    ".g-birdw{transform-box:fill-box;transform-origin:50% 100%;animation:g-birdw .35s ease-in-out infinite alternate}"
    "@keyframes g-birdw{to{transform:scaleY(-.6)}}"
    ".g-stats{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 2px}"
    ".g-stats span{background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:5px 12px;"
    "font-size:13px;font-weight:700;color:var(--soft)}"
    "@media (prefers-reduced-motion: reduce){.garden *{animation:none !important}}"
)


def garden_html(xp):
    p = progress(xp)
    green = ramp(p, 0.0, 0.55) ** 0.9
    rng = random.Random(42)
    parts = []

    # Sky: dusty at the start, fresh and green-blue later.
    sky_top, sky_bot = mix("#2b2118", "#173a33", green), mix("#15110d", "#0d1a14", green)
    parts.append(f'<defs><linearGradient id="g-sky{xp}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{sky_top}"/>'
                 f'<stop offset="1" stop-color="{sky_bot}"/></linearGradient>'
                 f'<radialGradient id="g-sunglow{xp}"><stop offset="0" stop-color="#ffd76a" stop-opacity=".55"/>'
                 '<stop offset="1" stop-color="#ffd76a" stop-opacity="0"/></radialGradient></defs>'
                 f'<rect width="{VB_W}" height="{VB_H}" fill="url(#g-sky{xp})"/>')
    parts.append(f'<circle class="g-sun" cx="700" cy="70" r="70" fill="url(#g-sunglow{xp})"/>'
                 '<circle cx="700" cy="70" r="22" fill="#ffd76a" opacity=".9"/>')
    for k, (y, s, dur) in enumerate(((52, 1.0, 95), (96, 0.75, 120), (30, 0.6, 140))):
        parts.append(f'<g class="g-cloud" style="animation-duration:{dur}s;animation-delay:-{dur * (0.2 + 0.3 * k):.0f}s">'
                     f'<g transform="translate(0,{y}) scale({s})" fill="#e8efe9" opacity="{0.10 + 0.08 * green:.2f}">'
                     '<ellipse cx="0" cy="0" rx="46" ry="14"/><ellipse cx="-20" cy="-8" rx="22" ry="14"/>'
                     '<ellipse cx="16" cy="-12" rx="26" ry="17"/></g></g>')

    # Soil block: brown sides, top goes from dry brown to lush green.
    top_col = mix("#7a5534", "#5c9e52", green)
    strip = mix("#6a4a2d", "#4b8a45", green)
    c0, c1, c2, c3 = iso(0, 0), iso(1, 0), iso(1, 1), iso(0, 1)
    down = lambda q, d=DEPTH: (q[0], q[1] + d)  # noqa: E731
    parts.append(f'<ellipse cx="{CX}" cy="{c2[1] + DEPTH + 4}" rx="{W * 0.42:.0f}" ry="14" fill="#000" opacity=".25"/>')
    parts.append(f'<polygon points="{pts(c3, c2, down(c2), down(c3))}" fill="#5b3b22"/>'
                 f'<polygon points="{pts(c2, c1, down(c1), down(c2))}" fill="#4a2f1b"/>'
                 f'<polygon points="{pts(c3, c2, down(c2, 5), down(c3, 5))}" fill="{strip}"/>'
                 f'<polygon points="{pts(c2, c1, down(c1, 5), down(c2, 5))}" fill="{mix(strip, "#000000", .15)}"/>'
                 f'<polygon points="{pts(c0, c1, c2, c3)}" fill="{top_col}"/>')
    for _ in range(14):                                   # little stones in the soil sides
        t, d = rng.uniform(0.05, 0.95), rng.uniform(9, DEPTH - 4)
        x, y = (c3[0] + (c2[0] - c3[0]) * t, c3[1] + (c2[1] - c3[1]) * t + d) if rng.random() < .5 else \
               (c2[0] + (c1[0] - c2[0]) * t, c2[1] + (c1[1] - c2[1]) * t + d)
        parts.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rng.uniform(1.5, 3):.1f}" ry="1.4" fill="#3d2615" opacity=".7"/>')

    # Dry cracks (only at the start).
    dry = 1 - ramp(p, 0.0, 0.25)
    if dry > 0:
        cracks = []
        for _ in range(16):
            u, v = rng.uniform(0.08, 0.92), rng.uniform(0.08, 0.92)
            seg = [iso(u, v)]
            for _ in range(3):
                u, v = u + rng.uniform(-0.04, 0.04), v + rng.uniform(-0.04, 0.04)
                seg.append(iso(u, v))
            cracks.append(f'<polyline points="{pts(*seg)}"/>')
        parts.append(f'<g fill="none" stroke="#4e321c" stroke-width="1.3" opacity="{dry * .8:.2f}">{"".join(cracks)}</g>')

    # Back of the plot: fence, shed, water barrel, back trees.
    parts.append(fence_posts("back_u", p) + fence_posts("back_v", p))
    parts.append(shed())
    bx, by = iso(0.06, 0.16)
    parts.append(f'<g transform="translate({bx:.1f},{by:.1f})"><ellipse cx="0" cy="0" rx="7" ry="3.5" fill="#5e3d22"/>'
                 '<rect x="-7" y="-14" width="14" height="14" fill="#7a5233"/><ellipse cx="0" cy="-14" rx="7" ry="3.5" fill="#4f8fc0"/>'
                 '<path d="M-7 -4H7M-7 -10H7" stroke="#4a3220" stroke-width="1.2"/></g>')

    # Vegetable beds: tilled soil from day one, crops grow one bed after another.
    order = random.Random(7).sample(range(N * N), N * N)
    rank_of = {cell: r for r, cell in enumerate(order)}
    beds, plants = [], []
    soil, furrow = mix("#5f3f25", "#4a3020", green), mix("#4b311c", "#3a2516", green)
    g = 0.012
    for i in range(N):
        for j in range(N):
            u0, v0 = LO + i * CELL, LO + j * CELL
            beds.append(f'<polygon points="{pts(iso(u0 + g, v0 + g), iso(u0 + CELL - g, v0 + g), iso(u0 + CELL - g, v0 + CELL - g), iso(u0 + g, v0 + CELL - g))}" fill="{soil}"/>')
            for k in (1, 2):
                a, b = iso(u0 + g * 2, v0 + CELL * k / 3), iso(u0 + CELL - g * 2, v0 + CELL * k / 3)
                beds.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{furrow}" stroke-width="1.2"/>')
            s = max(0.0, min(1.0, (p * (N * N + 5) - rank_of[i * N + j]) / 5))
            if s <= 0:
                continue
            x, y = iso(u0 + CELL / 2, v0 + CELL / 2)
            kind = CROPS[j % len(CROPS)]
            art = sprout() if s < 0.35 else crop(kind, s >= 0.9)
            k = 0.7 + 0.5 * s if s < 0.35 else 0.55 + 0.6 * s
            plants.append((u0 + v0, f'<g transform="translate({x:.1f},{y + 2:.1f})">'
                                     f'<ellipse cx="0" cy="0" rx="{9 * k:.1f}" ry="{3.2 * k:.1f}" fill="#000" opacity=".16"/>'
                                     f'<g class="g-sway" style="animation-delay:-{rng.uniform(0, 3):.1f}s">'
                                     f'<g transform="scale({k:.2f})">{art}</g></g></g>'))
    parts.append("".join(beds))

    # Grass tufts and flowers on the ring around the beds.
    ring = []
    for _ in range(round(70 * ramp(p, 0.02, 0.6))):
        while True:
            u, v = rng.uniform(0, 1), rng.uniform(0, 1)
            if in_ring(u, v):
                break
        x, y = iso(u, v)
        c = rng.choice(["#6fbf4a", "#5fae45", "#84cf5a"])
        ring.append((u + v, f'<g transform="translate({x:.1f},{y:.1f})"><g class="g-sway" style="animation-delay:-{rng.uniform(0, 3):.1f}s">'
                            f'<path d="M-3 0-4-6M0 0V-8M3 0 4-6" stroke="{c}" stroke-width="1.6" stroke-linecap="round"/></g></g>'))
    for _ in range(round(45 * ramp(p, 0.25, 0.9))):
        while True:
            u, v = rng.uniform(0, 1), rng.uniform(0, 1)
            if in_ring(u, v):
                break
        x, y = iso(u, v)
        c = rng.choice(["#ff8fb1", "#ffd45c", "#f4f1ea", "#b48cff", "#ff9a5c"])
        ring.append((u + v, f'<g transform="translate({x:.1f},{y:.1f})"><g class="g-sway" style="animation-delay:-{rng.uniform(0, 3):.1f}s">'
                            f'<path d="M0 0V-7" stroke="#5aa64a" stroke-width="1.2"/>'
                            f'<circle cx="0" cy="-8" r="2.6" fill="{c}"/><circle cx="0" cy="-8" r="1" fill="#f6c94a"/></g></g>'))

    # Trees appear one by one around the plot, then bear apples.
    trees = []
    # Back edges and the left/right corners only, so no tree hides a vegetable bed. All are full grown at p = 1.
    for (u, v, start) in ((0.07, 0.45, 0.12), (0.45, 0.07, 0.25), (0.07, 0.8, 0.4), (0.8, 0.07, 0.55),
                          (0.05, 0.97, 0.7), (0.97, 0.05, 0.82)):
        grow = ramp(p, start, start + 0.12)
        if grow <= 0:
            continue
        x, y = iso(u, v)
        k = 0.35 + 0.75 * grow
        trees.append((u + v, f'<g transform="translate({x:.1f},{y:.1f}) scale({k:.2f})">'
                             f'{tree(p >= 0.8 and grow >= 1, rng.uniform(0, 5))}</g>'))

    # Everything standing on the plot, painted back to front.
    parts.append("".join(svg for _, svg in sorted(ring + plants + trees, key=lambda t: t[0])))

    # Bare-earth life: dust and a tumbleweed until the first crops come up.
    if dry > 0.3:
        for k in range(7):
            x, y = rng.uniform(140, 560), rng.uniform(200, 380)
            dur = rng.uniform(5, 9)
            parts.append(f'<circle class="g-dust" cx="{x:.0f}" cy="{y:.0f}" r="{rng.uniform(1.2, 2.4):.1f}" fill="#c9a77a" '
                         f'style="animation-duration:{dur:.1f}s;animation-delay:-{rng.uniform(0, dur):.1f}s"/>')
        parts.append(f'<g class="g-tumble" opacity="{dry:.2f}"><ellipse cx="0" cy="2" rx="8" ry="2.5" fill="#000" opacity=".2"/>'
                     '<g class="g-roll" transform="translate(0,-8)"><circle cx="0" cy="0" r="8" fill="none" stroke="#b08a5a" stroke-width="1.3"/>'
                     '<path d="M-6-4 5 5M-5 5 6-5M0-8V8M-8 0H8M-3-7 4 7" stroke="#9c7748" stroke-width="1.1"/></g></g>')

    # Gardeners walking their rounds.
    css = [CSS]
    for n, (shirt, pants, skin, tool, (cu, cv, r, direction)) in enumerate(GARDENERS[:gardener_count(xp)]):
        kf, dur, (x0, y0, f0) = walk_keyframes(f"gw{n}", cu, cv, r, direction)
        css.append(kf)
        parts.append(f'<g transform="translate({x0:.1f},{y0:.1f}) scale({f0},1)" '
                     f'style="animation:gw{n} {dur:.1f}s linear infinite;animation-delay:-{dur * n / 6:.1f}s">'
                     f'<g transform="scale(1.25)">{gardener_svg(shirt, pants, skin, tool)}</g></g>')

    # Front fence (in front of the gardeners).
    parts.append(fence_posts("front_u", p) + fence_posts("front_v", p))

    # Butterflies and birds once the garden is alive.
    for n in range(round(5 * ramp(p, 0.3, 1.0))):
        css.append(flyer_keyframes(f"gb{n}", rng.uniform(260, 540), rng.uniform(170, 300), rng.uniform(60, 140), rng.uniform(20, 45), seed=n))
        dur = rng.uniform(12, 20)
        parts.append(f'<g style="animation:gb{n} {dur:.1f}s ease-in-out infinite;animation-delay:-{rng.uniform(0, dur):.1f}s">'
                     f'{butterfly(rng.choice(["#ffd45c", "#f4f1ea", "#ff9a5c", "#9fd4ff"]))}</g>')
    for n in range(round(3 * ramp(p, 0.6, 1.0))):
        dur = rng.uniform(22, 34)
        parts.append(f'<g class="g-bird" style="animation-duration:{dur:.1f}s;animation-delay:-{rng.uniform(0, dur):.1f}s">'
                     f'<g transform="translate(0,{rng.uniform(40, 110):.0f})"><g class="g-birdw">'
                     '<path d="M-7 0Q-3.5 -5 0 0Q3.5 -5 7 0" stroke="#d9e4dc" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
                     '</g></g></g>')

    gardeners = gardener_count(xp)
    label = f"Your garden: {round(p * 100)}% grown, {gardeners} gardener{'s' if gardeners != 1 else ''}"
    svg = (f'<svg viewBox="0 0 {VB_W} {VB_H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{label}">'
           f'{"".join(parts)}</svg>')
    return f'<style>{"".join(css)}</style><div class="garden">{svg}</div>'


def garden_stats_html(xp):
    p, n, nxt = progress(xp), gardener_count(xp), next_gardener_xp(xp)
    items = [f"🌱 {round(p * 100)}% grown",
             f"👩‍🌾 {n} gardener{'s' if n != 1 else ''}",
             f"Next gardener at {nxt:,} XP".replace(",", "'") if nxt else "Full crew hired"]
    if p >= 1:
        items[0] = "🌳 Garden fully grown"
    elif p == 0:
        items.insert(0, "Bare earth: earn XP to plant your first seeds")
    return '<div class="g-stats">' + "".join(f"<span>{i}</span>" for i in items) + "</div>"
