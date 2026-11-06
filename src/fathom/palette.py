"""Recorded report palette (spec 008, DEC-043): the one source of colour for every renderer.

The proposed light/dark tool tokens are supplied by the handoff. Renderers read colours only from
here: HTML through CSS custom properties, SVG/PDF/PowerPoint marks through the light
values. Kept apart from renderers.py only to avoid a renderers/charts import cycle.
"""

# Proposed tool palette (HO-DG-20261106-XZSM / relayed DEC-126).
THEMES = {'light': {'surface': '#F2EDE3', 'panel': '#FFFDF8', 'ink': '#182832', 'muted': '#4F6366', 'accent': '#315F87', 'link': '#315F87', 'rule': '#315F87', 'accent_soft': '#D3DFEA', 'tint': '#EAE6DB', 'border': '#D8D1C3', 'soft_border': '#C9C2B4', 'grid': '#C9C2B4', 'band': '#8A4B2A', 'accent_faint': '#6A87A1'}, 'dark': {'surface': '#0B1015', 'panel': '#121B22', 'ink': '#F0F0E9', 'muted': '#96A5A8', 'accent': '#90B4D7', 'link': '#90B4D7', 'rule': '#90B4D7', 'accent_soft': '#22384A', 'tint': '#16222B', 'border': '#2E3B45', 'soft_border': '#3A4A56', 'grid': '#2A3640', 'band': '#D9936A', 'accent_faint': '#55718A'}}

KIND_COLOURS = {'light': {'observation': '#315F87', 'interpretation': '#5C4587', 'hypothesis': '#89500C', 'action': '#23676B', 'question': '#873164'}, 'dark': {'observation': '#90B4D7', 'interpretation': '#AC9DD7', 'hypothesis': '#E5A45D', 'action': '#65C9B7', 'question': '#F29BD1'}}

# Six categorical families nudged away from reserved status hues; labels remain.
CATEGORICAL = ['#315F87', '#9A642B', '#7564a3', '#397db5', '#735B91', '#9D477E', '#5b777e', '#9d7428', '#5974bd', '#876183', '#248b81', '#A26C38', '#79538a', '#427448', '#8B598B', '#507e99', '#8c852e', '#7b657f', '#468568', '#967454']
DARK_CATEGORICAL = ['#90B4D7', '#D2B185', '#b3a9cc', '#92b7d6', '#AAA0C0', '#CC97BE', '#a5b4b8', '#c9b38a', '#a4b3db', '#BEA0BC', '#87bfb9', '#D7B48B', '#b59fc0', '#97b39b', '#C19BC2', '#9fb8c7', '#c0bc8c', '#b6aaba', '#99bcac', '#c5b29e']

LIGHT = THEMES["light"]


def contrast(foreground, background):
    """WCAG 2 contrast ratio between two #rrggbb colours."""
    def luminance(colour):
        channels = [int(colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        r, g, b = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
        return .2126 * r + .7152 * g + .0722 * b
    a, b = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (a + .05) / (b + .05)


def tokens(theme):
    return ";".join(f"--{name.replace('_', '-')}:{value}" for name, value in THEMES[theme].items()) + ";" + \
        ";".join(f"--kind-{kind}:{value}" for kind, value in KIND_COLOURS[theme].items()) + ";" + \
        ";".join(f"--series-{i}:{value}" for i, value in enumerate(CATEGORICAL if theme == "light" else DARK_CATEGORICAL))


def theme_css():
    """Light tokens, dark tokens by system preference unless data-theme=light, forced by data-theme=dark, light for print.

    SVG marks keep light colour attributes (portable in Markdown); HTML maps them to tokens here."""
    marks = "".join(f'svg [{attr}="{value}"]{{{attr}:var(--{name.replace("_", "-")})}}'
                    for name, value in LIGHT.items() for attr in ("fill", "stroke"))
    marks += "".join(f'svg [{attr}="{value}"]{{{attr}:var(--series-{i})}}'
                     for i, value in enumerate(CATEGORICAL) for attr in ("fill", "stroke"))
    return (":root{color-scheme:light dark;" + tokens("light") + "}"
            "@media (prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;" + tokens("dark") + "}}"
            ":root[data-theme=dark]{color-scheme:dark;" + tokens("dark") + "}"
            ":root[data-theme=light]{color-scheme:light}"
            "@media print{:root,:root[data-theme=dark],:root:not([data-theme=light]){" + tokens("light") + "}}" + marks + "svg text{fill:var(--ink)}")


def status_hue_distance(colour):
    """Provisional categorical proximity rule: circular HSV hue distance, degrees."""
    import colorsys
    def hue(c):return colorsys.rgb_to_hsv(*(int(c[i:i+2],16)/255 for i in (1,3,5)))[0]*360
    h=hue(colour)
    return min(min(abs(h-hue(c)),360-abs(h-hue(c))) for c in ['#A9D96F','#4D7220','#F18B86','#A0383A'])
