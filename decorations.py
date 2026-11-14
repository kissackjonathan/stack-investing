"""Flat SVG illustrations for the Journey map.

Every entry is a complete <svg> drawn on a 120x120 canvas, using the app palette.
Edit, add or remove entries freely; UNIT_DECOR picks which ones appear in each unit
(by unit index, 0 = Unit 1). Names missing from DECOR are simply skipped.
"""

G1, G2, AMBER, BLUE = "#7df59b", "#b6ffb9", "#ffcf6b", "#7cc4ff"
INK = "#0b3a1f"        # dark detail colour that reads on the light fills
AMBER_D, BLUE_D, G_D = "#d9a845", "#4f9fe0", "#4fcf78"


def _svg(body):
    return f'<svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">{body}</svg>'


DECOR = {
    "plant": _svg(
        f'<path d="M60 74V40" stroke="{G1}" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="M60 56c-22 2-32-10-32-26 18 0 30 9 32 26z" fill="{G1}"/>'
        f'<path d="M60 46c3-19 18-28 34-26-2 17-15 28-34 26z" fill="{G2}"/>'
        f'<rect x="32" y="72" width="56" height="11" rx="3" fill="{AMBER_D}"/>'
        f'<path d="M37 83h46l-6 26H43z" fill="{AMBER}"/>'
    ),
    "piggy": _svg(
        f'<circle cx="60" cy="22" r="12" fill="{AMBER}"/><circle cx="60" cy="22" r="6.5" fill="none" stroke="{AMBER_D}" stroke-width="3"/>'
        f'<path d="M22 66c-7 0-9-9-2-11" stroke="{G1}" stroke-width="4" fill="none" stroke-linecap="round"/>'
        f'<rect x="38" y="86" width="11" height="18" rx="3" fill="{G_D}"/><rect x="68" y="86" width="11" height="18" rx="3" fill="{G_D}"/>'
        f'<ellipse cx="58" cy="68" rx="38" ry="27" fill="{G1}"/>'
        f'<path d="M36 47l5-15 13 9z" fill="{G2}"/>'
        f'<rect x="88" y="58" width="16" height="19" rx="6" fill="{G2}"/>'
        f'<circle cx="96" cy="64" r="2" fill="{INK}"/><circle cx="96" cy="71" r="2" fill="{INK}"/>'
        f'<circle cx="76" cy="58" r="3.5" fill="{INK}"/><rect x="48" y="43" width="22" height="5" rx="2.5" fill="{INK}"/>'
    ),
    "coins": _svg(
        "".join(
            f'<rect x="30" y="{y}" width="60" height="14" rx="7" fill="{AMBER_D}"/>'
            f'<ellipse cx="60" cy="{y}" rx="30" ry="7" fill="{AMBER}"/>'
            for y in (96, 82, 68, 54, 40)
        )
        + f'<ellipse cx="60" cy="40" rx="16" ry="3.5" fill="none" stroke="{AMBER_D}" stroke-width="2.5"/>'
    ),
    "tree": _svg(
        f'<path d="M55 110V70h10v40z" fill="{AMBER_D}"/>'
        f'<path d="M60 80l-16-12M60 74l14-12" stroke="{AMBER_D}" stroke-width="5" stroke-linecap="round"/>'
        f'<circle cx="60" cy="42" r="28" fill="{G1}"/><circle cx="38" cy="58" r="18" fill="{G_D}"/>'
        f'<circle cx="84" cy="56" r="19" fill="{G2}"/><circle cx="50" cy="34" r="6" fill="{G2}"/>'
    ),
    "hourglass": _svg(
        f'<rect x="30" y="12" width="60" height="9" rx="4" fill="{AMBER}"/><rect x="30" y="99" width="60" height="9" rx="4" fill="{AMBER}"/>'
        f'<path d="M38 21h44c0 22-16 28-16 39s16 17 16 39H38c0-22 16-28 16-39S38 43 38 21z" fill="{BLUE}" fill-opacity=".35" stroke="{BLUE}" stroke-width="3"/>'
        f'<path d="M46 32h28c-4 10-10 14-14 18-4-4-10-8-14-18zM60 70l17 25H43z" fill="{AMBER}"/>'
    ),
    "pie": _svg(
        f'<circle cx="60" cy="62" r="42" fill="{BLUE}"/>'
        f'<path d="M60 62V20a42 42 0 0 1 40 29z" fill="{G1}"/>'
        f'<path d="M60 62l40-13a42 42 0 0 1-21 51z" fill="{AMBER}"/>'
        f'<path d="M60 62L79 100" stroke="#0b100d" stroke-width="3"/><path d="M60 62V20M60 62l40-13" stroke="#0b100d" stroke-width="3"/>'
    ),
    "candles": _svg(
        "".join(
            f'<path d="M{x} {top - 10}V{bot + 10}" stroke="{c}" stroke-width="3" stroke-linecap="round"/>'
            f'<rect x="{x - 8}" y="{top}" width="16" height="{bot - top}" rx="3" fill="{c}"/>'
            for x, top, bot, c in ((24, 62, 90, G1), (48, 50, 76, BLUE), (72, 34, 64, G1), (96, 20, 46, G2))
        )
    ),
    "rising": _svg(
        f'<path d="M16 14v90h92" stroke="#3b5244" stroke-width="4" fill="none" stroke-linecap="round"/>'
        f'<path d="M24 90l20-22 16 10 22-30 18 6" stroke="{G1}" stroke-width="7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M84 32l22-6-6 22z" fill="{G1}"/>'
        f'<circle cx="44" cy="68" r="5" fill="{G2}"/><circle cx="60" cy="78" r="5" fill="{G2}"/>'
    ),
    "globe": _svg(
        f'<circle cx="60" cy="60" r="44" fill="{BLUE}"/>'
        f'<path d="M34 34c10 2 14 10 10 18s4 14 12 12 6 12-2 20c-10-2-26-14-28-30 1-8 4-14 8-20z" fill="{G1}"/>'
        f'<path d="M70 22c8 6 4 12 12 14s14 8 10 20c-6 2-12-4-16 2s2 16-6 20c-4-10-10-14-8-24s-4-14 8-32z" fill="{G2}"/>'
        f'<ellipse cx="60" cy="60" rx="20" ry="44" fill="none" stroke="#0b100d" stroke-opacity=".35" stroke-width="2.5"/>'
        f'<path d="M16 60h88" stroke="#0b100d" stroke-opacity=".35" stroke-width="2.5"/>'
    ),
    "bank": _svg(
        f'<path d="M60 12l46 24H14z" fill="{AMBER}"/><rect x="14" y="36" width="92" height="8" fill="{AMBER_D}"/>'
        + "".join(f'<rect x="{x}" y="48" width="10" height="44" rx="2" fill="{AMBER}"/>' for x in (22, 42, 68, 88))
        + f'<rect x="10" y="94" width="100" height="12" rx="3" fill="{AMBER_D}"/><circle cx="60" cy="27" r="5" fill="#0b100d" fill-opacity=".4"/>'
    ),
    "centralbank": _svg(
        f'<path d="M60 4v14" stroke="{BLUE}" stroke-width="3"/><path d="M60 5h16l-4 5 4 5H60z" fill="{G1}"/>'
        f'<path d="M26 46a34 30 0 0 1 68 0z" fill="{BLUE}"/><rect x="20" y="44" width="80" height="8" fill="{BLUE_D}"/>'
        + "".join(f'<rect x="{x}" y="56" width="9" height="36" rx="2" fill="{BLUE}"/>' for x in (26, 44, 67, 85))
        + f'<rect x="14" y="94" width="92" height="12" rx="3" fill="{BLUE_D}"/>'
    ),
    "magnifier": _svg(
        f'<rect x="18" y="62" width="12" height="30" rx="3" fill="{BLUE}"/><rect x="36" y="46" width="12" height="46" rx="3" fill="{BLUE}"/>'
        f'<rect x="54" y="56" width="12" height="36" rx="3" fill="{BLUE}"/>'
        f'<circle cx="68" cy="46" r="26" fill="{G2}" fill-opacity=".25" stroke="{G1}" stroke-width="7"/>'
        f'<path d="M86 64l20 20" stroke="{AMBER}" stroke-width="11" stroke-linecap="round"/>'
    ),
    "shield": _svg(
        f'<path d="M60 10l40 14v30c0 28-18 46-40 56-22-10-40-28-40-56V24z" fill="{G1}"/>'
        f'<path d="M60 10l40 14v30c0 28-18 46-40 56z" fill="{G2}"/>'
        f'<path d="M42 58l13 13 25-27" stroke="{INK}" stroke-width="8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    ),
    "safe": _svg(
        f'<rect x="16" y="16" width="88" height="84" rx="10" fill="{BLUE}"/><rect x="26" y="26" width="68" height="64" rx="6" fill="{BLUE_D}"/>'
        f'<circle cx="60" cy="58" r="18" fill="{AMBER}"/><circle cx="60" cy="58" r="6" fill="{AMBER_D}"/>'
        f'<path d="M60 40v8M60 68v8M42 58h8M70 58h8" stroke="{AMBER_D}" stroke-width="3"/>'
        f'<rect x="26" y="100" width="14" height="8" rx="2" fill="{BLUE_D}"/><rect x="80" y="100" width="14" height="8" rx="2" fill="{BLUE_D}"/>'
    ),
    "banknote": _svg(
        f'<rect x="14" y="40" width="96" height="54" rx="7" fill="{G_D}" transform="rotate(-8 60 66)"/>'
        f'<rect x="10" y="32" width="96" height="54" rx="7" fill="{G1}"/>'
        f'<rect x="18" y="40" width="80" height="38" rx="4" fill="none" stroke="{INK}" stroke-opacity=".35" stroke-width="2.5"/>'
        f'<circle cx="58" cy="59" r="13" fill="{G2}"/>'
        f'<text x="58" y="64" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="800" fill="{INK}">CHF</text>'
    ),
    "percent": _svg(
        f'<circle cx="34" cy="34" r="16" fill="none" stroke="{AMBER}" stroke-width="10"/>'
        f'<circle cx="86" cy="86" r="16" fill="none" stroke="{AMBER}" stroke-width="10"/>'
        f'<path d="M92 20L28 100" stroke="{AMBER}" stroke-width="11" stroke-linecap="round"/>'
    ),
    "basket": _svg(
        f'<path d="M36 50c0-22 48-22 48 0" stroke="{AMBER_D}" stroke-width="6" fill="none"/>'
        f'<circle cx="44" cy="46" r="11" fill="{G1}"/><circle cx="64" cy="40" r="12" fill="{BLUE}"/><circle cx="80" cy="48" r="10" fill="{G2}"/>'
        f'<path d="M14 52h92l-10 50H24z" fill="{AMBER}"/>'
        f'<path d="M24 66h72M28 84h64M44 52v50M60 52v50M76 52v50" stroke="{AMBER_D}" stroke-width="3"/>'
    ),
    "coaster": _svg(
        f'<path d="M24 92V70M48 92V40M72 92V64M96 92V34" stroke="#3b5244" stroke-width="4"/>'
        f'<path d="M8 80C20 80 26 60 36 48s18-14 24 6 16 28 26 4 20-22 30-22" stroke="{BLUE}" stroke-width="7" fill="none" stroke-linecap="round"/>'
        f'<rect x="80" y="16" width="26" height="16" rx="5" fill="{AMBER}" transform="rotate(-24 93 24)"/>'
        f'<path d="M8 100h104" stroke="#3b5244" stroke-width="4" stroke-linecap="round"/>'
    ),
    "mountains": _svg(
        f'<path d="M4 104l36-60 22 34 16-22 38 48z" fill="{BLUE}"/>'
        f'<path d="M40 44l10 16-10-4-8 6z" fill="#eaf6ff"/><path d="M78 56l8 11-8-3-6 4z" fill="#eaf6ff"/>'
        f'<path d="M4 104l36-60 10 16" fill="none" stroke="{BLUE_D}" stroke-width="3"/>'
    ),
    "dice": _svg(
        f'<rect x="16" y="20" width="62" height="62" rx="12" fill="{BLUE}" transform="rotate(-10 47 51)"/>'
        f'<rect x="54" y="52" width="50" height="50" rx="10" fill="{G1}" transform="rotate(12 79 77)"/>'
        f'<circle cx="34" cy="38" r="5" fill="#0b100d"/><circle cx="48" cy="50" r="5" fill="#0b100d"/><circle cx="60" cy="62" r="5" fill="#0b100d"/>'
        f'<circle cx="72" cy="70" r="4.5" fill="{INK}"/><circle cx="86" cy="84" r="4.5" fill="{INK}"/>'
    ),
    "newspaper": _svg(
        f'<rect x="14" y="18" width="84" height="88" rx="6" fill="#eaf6ff"/><rect x="98" y="34" width="10" height="66" rx="4" fill="{BLUE}"/>'
        f'<rect x="24" y="28" width="64" height="12" rx="2" fill="{BLUE}"/><rect x="24" y="48" width="28" height="24" rx="2" fill="{G1}"/>'
        f'<path d="M60 52h28M60 62h28M60 72h20M24 82h64M24 92h50" stroke="#9db4c8" stroke-width="4" stroke-linecap="round"/>'
    ),
    "warning": _svg(
        f'<path d="M60 12l52 92H8z" fill="{AMBER}" stroke="{AMBER}" stroke-width="8" stroke-linejoin="round"/>'
        f'<path d="M60 44v30" stroke="#0b100d" stroke-width="10" stroke-linecap="round"/><circle cx="60" cy="90" r="6" fill="#0b100d"/>'
    ),
    "megaphone": _svg(
        f'<path d="M22 50h16l46-26v72L38 70H22z" fill="{AMBER}"/><rect x="14" y="48" width="14" height="24" rx="4" fill="{AMBER_D}"/>'
        f'<path d="M40 70l8 30h12l-6-26" fill="{AMBER_D}"/>'
        f'<path d="M96 46c6 4 6 24 0 28M104 38c10 8 10 36 0 44" stroke="{G1}" stroke-width="5" fill="none" stroke-linecap="round"/>'
    ),
    "hook": _svg(
        f'<path d="M64 4v52" stroke="#3b5244" stroke-width="3"/>'
        f'<path d="M64 56v24a16 16 0 0 1-32 0v-8" stroke="{BLUE}" stroke-width="8" fill="none" stroke-linecap="round"/>'
        f'<path d="M24 76l8-10 8 10z" fill="{BLUE}"/>'
        f'<circle cx="80" cy="96" r="12" fill="{AMBER}"/><circle cx="80" cy="96" r="6" fill="none" stroke="{AMBER_D}" stroke-width="3"/>'
    ),
    "rocket": _svg(
        f'<path d="M48 84c-6 10-6 20-4 28 8-4 14-10 16-18M72 84c6 10 6 20 4 28-8-4-14-10-16-18" fill="{AMBER}"/>'
        f'<path d="M60 8c20 14 26 40 18 76H42C34 48 40 22 60 8z" fill="{G2}"/>'
        f'<path d="M42 62L26 82l16 2zM78 62l16 20-16 2z" fill="{BLUE}"/>'
        f'<circle cx="60" cy="44" r="10" fill="{BLUE}" stroke="{INK}" stroke-opacity=".3" stroke-width="3"/>'
        f'<path d="M52 92h16l-8 22z" fill="{AMBER}"/>'
    ),
    "bulb": _svg(
        f'<path d="M60 10a32 32 0 0 1 18 58c-4 4-6 8-6 14H48c0-6-2-10-6-14a32 32 0 0 1 18-58z" fill="{AMBER}"/>'
        f'<path d="M52 82V60l8 8 8-8v22" stroke="{AMBER_D}" stroke-width="3" fill="none"/>'
        f'<rect x="46" y="84" width="28" height="8" rx="3" fill="{BLUE}"/><rect x="48" y="94" width="24" height="8" rx="3" fill="{BLUE_D}"/>'
        f'<path d="M54 104h12" stroke="{BLUE_D}" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="M14 40h-8M24 16l-6-6M106 40h8M96 16l6-6" stroke="{G1}" stroke-width="4" stroke-linecap="round"/>'
    ),
    "gear": _svg(
        "".join(f'<rect x="52" y="10" width="16" height="22" rx="3" fill="{G1}" transform="rotate({a} 60 60)"/>' for a in range(0, 360, 45))
        + f'<circle cx="60" cy="60" r="34" fill="{G1}"/><circle cx="60" cy="60" r="14" fill="#0b100d"/>'
    ),
}

# Which illustrations each unit uses (unit index -> names). Order = order of appearance, cycled.
UNIT_DECOR = [
    ["plant", "piggy", "coins", "tree", "hourglass", "pie"],                 # 1 Foundations
    ["candles", "bank", "rising", "coins", "banknote", "globe"],             # 2 Markets & assets
    ["basket", "percent", "coins", "pie", "magnifier", "banknote"],          # 3 Funds & costs
    ["shield", "coaster", "mountains", "dice", "safe", "rising"],            # 4 Risk & psychology
    ["globe", "centralbank", "percent", "newspaper", "banknote", "bank"],    # 5 Macro & money
    ["magnifier", "warning", "megaphone", "hook", "shield", "safe"],         # 6 Scams & red flags
    ["rocket", "bulb", "gear", "rising", "pie", "coins"],                    # 7 Startups & VC
]
