#!/usr/bin/env python3
"""
Generate a printable 9" x 5.5" two-sided quick-reference checklist card.

Reads efis_checklist.json and outputs build/printable_card.html styled after
classic laminated aviation checklist cards:
  - Front: Normal procedures (light blue sections)
  - Back: Emergency & Abnormal procedures (yellow sections, red title bars)

Print at 100% scale, landscape, double-sided flip on long edge.
"""

import json
from pathlib import Path
from html import escape

JSON_PATH = Path("efis_checklist.json")
BUILD_DIR = Path("build")
BUILD_DIR.mkdir(exist_ok=True)

# ── Which checklists go on which side ─────────────────────────────────
# Front side: key normal procedures (skip big preflight walkaround stuff)
FRONT_CHECKLISTS = [
    "Before Starting Engine",
    "Engine Start",
    "Post Engine Start",
    "Engine Runup",
    "Departure Preparation",
    "Enroute Climb",
    "Cruise",
    "Mountain Crossing",
    "VFR Approach",
    "IFR Approach",
    "Clear Runway",
    "Shutdown",
]

# Back side: all emergency + abnormal
BACK_GROUPS = ["Emergency", "Abnormal"]

# ── CSS ───────────────────────────────────────────────────────────────
STYLE = r"""
@page {
  size: 5.5in 9in portrait;
  margin: 0;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 6.5pt;
  line-height: 1.25;
  color: #000;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

/* Each side is one .page */
.page {
  width: 5.5in;
  height: 9in;
  padding: 0.06in;
  page-break-after: always;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 0.5pt solid #888;
}

/* Horizontal aircraft-name banner */
.sidebar {
  background: #e8922e;
  color: #fff;
  font-weight: 900;
  font-size: 14pt;
  letter-spacing: 1pt;
  text-align: center;
  padding: 3pt 6pt;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8pt;
}
.sidebar .sub {
  font-size: 7pt;
  font-weight: 600;
  letter-spacing: 0;
}

/* Horizontal page title bar */
.page-header {
  background: #1a3a5c;
  color: #fff;
  font-weight: 900;
  font-size: 6pt;
  text-align: center;
  padding: 1.5pt 4pt;
  flex: 0 0 auto;
  letter-spacing: 0.5pt;
  text-transform: uppercase;
}

/* Multi-column flow area */
.columns {
  flex: 1;
  padding: 2pt;
  column-gap: 3pt;
  overflow: hidden;
  /* fill columns left-to-right to their full height, don't balance */
  column-fill: auto;
}
.front-cols { column-count: 3; font-size: 6.5pt; line-height: 1.25; }
.back-cols  { column-count: 3; font-size: 6pt; line-height: 1.22; }

/* Individual checklist box */
.section {
  break-inside: avoid;
  border: 0.75pt solid #336;
  border-radius: 2pt;
  overflow: hidden;
  margin-bottom: 3pt;
}

/* Normal (front) color scheme */
.section.normal { background: #dce9f5; }
.section.normal .section-title { background: #4a7ab5; color: #fff; }

/* Emergency (back) color scheme */
.section.emergency { background: #fef9c3; }
.section.emergency .section-title { background: #c0392b; color: #fff; }

/* Abnormal color scheme */
.section.abnormal { background: #fef3c7; }
.section.abnormal .section-title { background: #d97706; color: #fff; }

.section-title {
  font-size: 6.5pt;
  font-weight: 800;
  text-transform: uppercase;
  text-align: center;
  padding: 1.5pt 2pt;
  letter-spacing: 0.3pt;
}
.back-cols .section-title { font-size: 6pt; padding: 1.2pt 2pt; }

.section-body {
  padding: 1.5pt 3pt 2pt 3pt;
}

/* Single checklist row */
.row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 0.5pt 0;
}

.row .prompt {
  flex: 1 1 auto;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Dot leaders */
.row .dots {
  flex: 1 0 3pt;
  border-bottom: 0.4pt dotted #999;
  margin: 0 1pt;
  min-width: 3pt;
  align-self: baseline;
  position: relative;
  top: -1.5pt;
}

.row .expect {
  flex: 0 0 auto;
  text-align: right;
  font-weight: 700;
  white-space: nowrap;
}

/* Plaintext / note rows */
.note-row {
  font-weight: 800;
  font-style: italic;
  text-align: center;
  padding: 0.5pt 0;
  font-size: 5.5pt;
  color: #444;
}

/* Frequency table */
.freq-section { background: #f0e6d2; }
.freq-section .section-title { background: #6b4c2a; color: #fff; }
.freq-group { font-weight: 800; padding: 1pt 0 0.3pt; font-size: 5.5pt; color: #333; border-bottom: 0.4pt solid #b8a080; margin-top: 1pt; }
.freq-group:first-child { margin-top: 0; }

/* Screen preview helpers */
@media screen {
  body { background: #777; }
  .page {
    background: #fff;
    margin: 10px auto;
    box-shadow: 0 2px 10px rgba(0,0,0,.4);
  }
}

@media print {
  .page { border: none; }
}
"""


def load_data():
    return json.load(JSON_PATH.open(encoding="utf-8"))


def render_item(item):
    """Render a single checklist item as HTML."""
    if item["type"] == "ITEM_PLAINTEXT":
        return f'<div class="note-row">{escape(item["prompt"])}</div>'
    prompt = escape(item.get("prompt", ""))
    expect = escape(item.get("expectation", ""))
    if expect:
        return (
            f'<div class="row">'
            f'<span class="prompt">{prompt}</span>'
            f'<span class="dots"></span>'
            f'<span class="expect">{expect}</span>'
            f'</div>'
        )
    return f'<div class="row"><span class="prompt">{prompt}</span></div>'


def render_section(checklist, css_class="normal"):
    """Render a checklist section box."""
    items_html = "\n".join(render_item(i) for i in checklist["items"])
    return (
        f'<div class="section {css_class}">'
        f'<div class="section-title">{escape(checklist["title"])}</div>'
        f'<div class="section-body">{items_html}</div>'
        f'</div>'
    )


# ── Local frequencies ─────────────────────────────────────────────────
FREQUENCIES = [
    ("KPAE – Paine Field", [
        ("ATIS", "128.650"),
        ("Ground", "121.800"),
        ("Tower E", "120.200"),
        ("Tower W", "132.950"),
        ("Approach", "128.500"),
    ]),
    ("KNUW – NAS Whidbey", [
        ("East", "120.700"),
        ("West", "118.200"),
    ]),
    ("KORS – Island CTAF", [
        ("CTAF", "128.250"),
    ]),
    ("KAWO – Arlington Muni", [
        ("CTAF", "122.725"),
    ]),
    ("KBVS – Skagit Regional", [
        ("CTAF", "123.075"),
    ]),
    ("Seattle Approach", [
        ("South", "119.200"),
        ("North", "128.500"),
    ]),
]


def render_freq_section():
    """Render a local frequencies reference box."""
    rows = []
    for group_name, freqs in FREQUENCIES:
        rows.append(f'<div class="freq-group">{escape(group_name)}</div>')
        for label, freq in freqs:
            rows.append(
                f'<div class="row">'
                f'<span class="prompt">{escape(label)}</span>'
                f'<span class="dots"></span>'
                f'<span class="expect">{escape(freq)}</span>'
                f'</div>'
            )
    return (
        f'<div class="section freq-section">'
        f'<div class="section-title">Local Frequencies</div>'
        f'<div class="section-body">{"".join(rows)}</div>'
        f'</div>'
    )


def build_front(data):
    """Build front page with normal procedures."""
    cl_by_name = {}
    for g in data["groups"]:
        for cl in g["checklists"]:
            cl_by_name[cl["title"]] = cl

    sections = [render_freq_section()]
    for name in FRONT_CHECKLISTS:
        if name in cl_by_name:
            sections.append(render_section(cl_by_name[name], "normal"))
    return sections


def build_back(data):
    """Build back page with emergency & abnormal procedures."""
    sections = []
    for g in data["groups"]:
        if g["title"] in BACK_GROUPS:
            css = "emergency" if g["title"] == "Emergency" else "abnormal"
            for cl in g["checklists"]:
                sections.append(render_section(cl, css))
    return sections


def build_html(data):
    meta = data.get("metadata", {})
    aircraft = meta.get("makeAndModel", "Aircraft")
    name = meta.get("name", "Checklist")

    front_sections = build_front(data)
    back_sections = build_back(data)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(name)} – Printable Card</title>
<style>{STYLE}</style>
</head>
<body>

<!-- FRONT SIDE -->
<div class="page">
  <div class="sidebar">
    {escape(aircraft)}
    <span class="sub">&mdash; {escape(name)}</span>
  </div>
  <div class="page-header">Quick Reference Checklist</div>
  <div class="columns front-cols">
    {"".join(front_sections)}
  </div>
</div>

<!-- BACK SIDE -->
<div class="page">
  <div class="sidebar" style="background:#c0392b;">
    {escape(aircraft)}
    <span class="sub">&mdash; Emergency &amp; Abnormal</span>
  </div>
  <div class="page-header" style="background:#7f1d1d;">Emergency &amp; Abnormal Procedures</div>
  <div class="columns back-cols">
    {"".join(back_sections)}
  </div>
</div>

</body>
</html>"""


def main():
    data = load_data()
    html = build_html(data)
    out = BUILD_DIR / "printable_card.html"
    out.write_text(html, encoding="utf-8")
    print(f"Generated {out}")


if __name__ == "__main__":
    main()
