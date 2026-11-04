"""Recorded report palette (spec 008, DEC-043): the one source of colour for every renderer.

The light theme is Fathom's existing teal palette. Renderers read colours only from
here: HTML through CSS custom properties, SVG/PDF/PowerPoint marks through the light
values. Kept apart from renderers.py only to avoid a renderers/charts import cycle.
"""

THEMES = {
    "light": {"surface": "#f5f8f7", "panel": "#ffffff", "ink": "#193e42", "muted": "#4d676b",
              "link": "#12656b", "rule": "#28777c", "border": "#d5e1df", "grid": "#cbd9d7",
              "accent": "#216e73", "accent_soft": "#c3ded8", "tint": "#e9f2ee", "soft_border": "#b9d3cf"},
    "dark": {"surface": "#0f1b1d", "panel": "#162427", "ink": "#dce9e7", "muted": "#a3b8b6",
             "link": "#7fd3d6", "rule": "#4fa3a7", "border": "#2d4347", "grid": "#2a3f43",
             "accent": "#5cb8bd", "accent_soft": "#24484c", "tint": "#1b3135", "soft_border": "#3b5b5f"},
}

# Finding kinds (DG-RA). Roles follow the salvage memo: observation blue, interpretation
# purple, hypothesis amber, action green, question red; each passes WCAG AA on the panel.
KIND_COLOURS = {
    "light": {"observation": "#2f6aa3", "interpretation": "#6a4f9e", "hypothesis": "#8a5a12",
              "action": "#2f6f3e", "question": "#a43a3a"},
    "dark": {"observation": "#8cbbe8", "interpretation": "#bba7e6", "hypothesis": "#e2b664",
             "action": "#86cc9f", "question": "#efa0a0"},
}

# Categorical series for multi-level marks (target rate bars and legends).
CATEGORICAL = ["#216e73", "#ab5130", "#7564a3", "#397db5", "#6d8430", "#b34867", "#5b777e", "#9d7428", "#5974bd", "#906a75",
               "#248b81", "#bd6440", "#79538a", "#427448", "#a64d4d", "#507e99", "#8c852e", "#7b657f", "#468568", "#967454"]

# Dark HTML series preserve hue families while clearing the3:1 graphics review floor.
# Fixed exports and portable SVG attributes retain CATEGORICAL above.
DARK_CATEGORICAL = ["#5cb8bd", "#d1a18d", "#b3a9cc", "#92b7d6", "#afbb8d", "#d59aac", "#a5b4b8", "#c9b38a", "#a4b3db", "#c2adb3",
                    "#87bfb9", "#dba995", "#b59fc0", "#97b39b", "#ce9d9d", "#9fb8c7", "#c0bc8c", "#b6aaba", "#99bcac", "#c5b29e"]

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
