# -*- coding: utf-8 -*-
"""Rend les fichiers .mmd en PNG haute définition (Playwright + Mermaid CDN)."""

from pathlib import Path
import sys

DIR = Path(__file__).resolve().parent
OUT = DIR


def render_one(page, mmd: Path, scale: int = 3):
    source = mmd.read_text(encoding="utf-8")
    tmp = DIR / f"_tmp_{mmd.stem}.html"
    tmp.write_text(
        f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"/>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
  mermaid.initialize({{
    startOnLoad: false,
    securityLevel: 'loose',
    theme: 'base',
    er: {{ useMaxWidth: false }},
    flowchart: {{ useMaxWidth: false }},
    sequence: {{ useMaxWidth: false }}
  }});
  window.__ready = false;
  await mermaid.run();
  window.__ready = true;
</script>
<style>
  html, body {{ margin: 0; background: #ffffff; }}
  #wrap {{
    display: inline-block;
    background: #ffffff;
    padding: 40px;
  }}
  .mermaid, .mermaid svg {{
    max-width: none !important;
  }}
  .mermaid svg {{
    height: auto !important;
  }}
</style>
</head>
<body>
<div id="wrap">
<pre class="mermaid">
{source}
</pre>
</div>
</body></html>""",
        encoding="utf-8",
    )
    page.goto(tmp.as_uri(), wait_until="networkidle", timeout=120000)
    page.wait_for_function("() => window.__ready === true", timeout=120000)
    page.wait_for_timeout(600)

    # Agrandir le SVG dans le DOM pour un rendu net
    page.evaluate(
        """() => {
          const svg = document.querySelector('#wrap svg');
          if (!svg) return;
          svg.removeAttribute('width');
          svg.removeAttribute('height');
          svg.style.maxWidth = 'none';
          const box = svg.getBBox();
          const pad = 40;
          svg.setAttribute('viewBox', `${box.x - pad} ${box.y - pad} ${box.width + pad * 2} ${box.height + pad * 2}`);
          svg.setAttribute('width', String(Math.ceil(box.width + pad * 2)));
          svg.setAttribute('height', String(Math.ceil(box.height + pad * 2)));
        }"""
    )
    page.wait_for_timeout(200)

    wrap = page.query_selector("#wrap")
    png_path = OUT / f"{mmd.stem}.png"
    wrap.screenshot(path=str(png_path), type="png")
    print(f"OK {png_path.name} ({png_path.stat().st_size // 1024} Ko)")
    tmp.unlink(missing_ok=True)


def render_all(only: str | None = None):
    from playwright.sync_api import sync_playwright

    files = sorted(DIR.glob("*.mmd"))
    if only:
        files = [f for f in files if f.stem == only or f.name == only]
    if not files:
        raise SystemExit("Aucun fichier .mmd trouvé.")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 3200, "height": 2400},
            device_scale_factor=3,
        )
        for mmd in files:
            render_one(page, mmd)
        browser.close()
    print(f"Terminé : {len(files)} diagramme(s) HD dans {DIR}")


if __name__ == "__main__":
    cible = sys.argv[1] if len(sys.argv) > 1 else None
    render_all(cible)
