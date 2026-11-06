"""Spec008 review regressions; browser cascade is additionally checked in the gallery harness."""
import re


def test_categorical_marks_have_light_and_dark_theme_tokens():
    from fathom.palette import CATEGORICAL, THEMES, contrast, theme_css, tokens
    css=theme_css()
    for colour in CATEGORICAL:
        for attr in ('fill','stroke'):
            matches=re.findall(r'svg \['+attr+r'="'+colour+r'"\]\{'+attr+r':var\((--[\w-]+)\)\}',css)
            assert matches, (colour,attr)
            for mode in ('light','dark'):
                declaration=dict(part.split(':',1) for part in tokens(mode).split(';'))
                resolved=declaration[matches[-1]]
                assert resolved==colour if mode=='light' else contrast(resolved,THEMES[mode]['panel'])>=3
    assert contrast('#222222','#162427')<3  # Failing-contrast decoy.


def test_print_palette_overrides_system_and_explicit_dark_selectors():
    from fathom.palette import theme_css,THEMES
    css=theme_css();before,printing=css.split('@media print{',1)
    # Dark root selectors must have equally specific later light-print counterparts.
    selectors=re.findall(r'([^{}]+)\{color-scheme:dark;',before)
    assert selectors
    print_selector=printing.split('{',1)[0].split(',')
    assert all(selector in print_selector for selector in selectors)
    assert '--panel:'+THEMES['light']['panel'] in printing


def test_temporal_stem_marks_follow_the_theme():
    """Merged spec011 stem plots: band and faint-stem colours come from the palette and are themed in dark mode."""
    from fathom.palette import THEMES, contrast, theme_css
    from fathom import temporal_view
    css=theme_css();source=open(temporal_view.__file__).read()
    assert not re.findall(r'#[0-9a-fA-F]{6}\b',source)
    for name in ('band','accent_faint','accent','border'):
        assert f'svg [stroke="{THEMES["light"][name]}"]{{stroke:var(--{name.replace("_","-")})}}' in css, name
    assert contrast(THEMES['dark']['band'],THEMES['dark']['panel'])>=3 and contrast(THEMES['dark']['accent_faint'],THEMES['dark']['panel'])>=3
    assert contrast(THEMES['dark']['grid'],THEMES['dark']['panel'])<3  # Decoy: the light band colour would fail on the dark panel.
