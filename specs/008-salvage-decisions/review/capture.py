"""FT-R17 pass for spec 008: actual offline HTML in light, dark and data-theme override, at 1280/390.

Run from the repository root after generating reports:
  guide profile tests/fixtures/salvage/planted-missingness.csv --config specs/008-salvage-decisions/review/planted.yaml --out reports/s8-planted
  guide profile tests/fixtures/salvage/tiny.csv --out reports/s8-tiny
The report HTML has no script; the override is set on <html> by this harness only.
"""
import hashlib
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

MODES = {"light": ("light", None), "dark": ("dark", None),
         "override-light-on-dark": ("dark", "light"), "override-dark-on-light": ("light", "dark")}
VIEWS = {"planted": [("findings", "#findings"), ("target-chart", "figure.target-chart"), ("kinds", "h3.kind-hypothesis"), ("quality", "details:has(> summary:text-is('Quality rules and screening coverage'))")],
         "tiny": [("column", "details.column-entry")]}


def main():
    out = Path(__file__).parent; manifest = {}
    for old in out.glob("*.png"): old.unlink()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True, args=["--no-sandbox"])
        for report, views in VIEWS.items():
            html = Path(f"reports/s8-{report}/report.html").read_text()
            for mode, (scheme, theme) in MODES.items():
                if mode.startswith("override") and report == "tiny": continue
                for width in (1280, 390):
                    page = browser.new_page(viewport={"width": width, "height": 900}, color_scheme=scheme)
                    page.context.set_offline(True); page.set_content(html)
                    if theme: page.evaluate("(t)=>document.documentElement.setAttribute('data-theme',t)", theme)
                    for topic, selector in views:
                        node = page.locator(selector).first
                        if topic in ("column", "quality"): node.evaluate("(x)=>x.open=true")
                        node.scroll_into_view_if_needed()
                        page.evaluate("(y)=>scrollTo(0,y)", node.bounding_box()["y"] + page.evaluate("scrollY") - 8)
                        file = f"{report}-{topic}-{mode}-{width}.png"; page.screenshot(path=str(out / file))
                        manifest[file] = {"report": report, "view": topic, "mode": mode, "width": width,
                                          "document_width": page.evaluate("document.documentElement.scrollWidth"),
                                          "background": page.evaluate("getComputedStyle(document.body).backgroundColor")}
                    page.close()
        browser.close()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (out / "image-hashes.json").write_text(json.dumps({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob("*.png"))}, indent=2) + "\n")
    print("screenshots", len(manifest))


if __name__ == "__main__":
    main()
