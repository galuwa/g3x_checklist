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
# Front side: normal procedures
FRONT_CHECKLISTS = [
    "Before Starting Engine",
    "Engine Start",
    "Post Engine Start",
    "Engine Runup",
    "Departure Preparation",
    "Enroute Climb",
    "Cruise",
    "VFR Approach",
    "IFR Approach",
    "Clear Runway",
    "Shutdown",
]

# Back side: emergency + abnormal procedures
BACK_CHECKLISTS = [
    # Emergency
    "Engine Out",
    "Ditching",
    "Lost Comms",
    "Manual Gear Extension",
    "Icing",
    "Engine Fire Flight",
    "Electrical Fire Flight",
    "Engine Failure After Takeoff",
    "Precautionary Landing",
    "Engine Start Fire",
    "Cabin Fire",
    "Wing FIre",
    "Failed Gear Retract",
    "Gear Up Landing",
    "No Gear Indication",
    "Failed Nose Gear",
    "Overvoltage Light",
    "Discharge",
    # Abnormal
    "Light Gun Air",
    "Loss of GPS",
]

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
  background: #000;
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
  background: #000;
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
.front-cols { column-count: 3; font-size: 5.5pt; line-height: 1.2; }
.back-cols  { column-count: 3; font-size: 6pt; line-height: 1.22; }

/* Individual checklist box */
.section {
  break-inside: avoid;
  border: 0.75pt solid #000;
  border-radius: 2pt;
  overflow: hidden;
  margin-bottom: 3pt;
  position: relative;
}

/* Phase/type badge */
.badge {
  position: absolute;
  top: 0;
  left: 0;
  font-size: 5pt;
  font-weight: 900;
  line-height: 1;
  padding: 0.5pt 1.5pt;
  background: #000;
  color: #fff;
  border-radius: 0 0 2pt 0;
  z-index: 1;
}

/* Ground preflight */
.section.preflight { background: #fff; }
.section.preflight .section-title { background: #ddd; color: #000; }

/* In flight */
.section.inflight { background: #fff; }
.section.inflight .section-title { background: #bbb; color: #000; }

/* Landed */
.section.landed { background: #fff; }
.section.landed .section-title { background: #eee; color: #000; }

/* Emergency (back) color scheme */
.section.emergency { background: #fff; }
.section.emergency .section-title { background: #000; color: #fff; }

/* Abnormal color scheme */
.section.abnormal { background: #fff; }
.section.abnormal .section-title { background: #555; color: #fff; }

.section-title {
  font-size: 5.5pt;
  font-weight: 800;
  text-transform: uppercase;
  text-align: center;
  padding: 1.2pt 2pt;
  letter-spacing: 0.3pt;
}
.front-cols .section-title { font-size: 5.5pt; }
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
  color: #333;
}

/* Compact frequency bar */
.freq-bar {
  background: #f5f5f5;
  border-bottom: 0.75pt solid #999;
  padding: 1.5pt 4pt;
  font-size: 5pt;
  line-height: 1.4;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0 6pt;
  flex: 0 0 auto;
}
.freq-grp { white-space: nowrap; }
.freq-id { font-weight: 800; color: #000; margin-right: 2pt; }
.freq-pair { margin-right: 3pt; }
.freq-pair b { font-weight: 700; color: #333; }

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


SECTION_EMOJI = {
    "preflight": "G",
    "inflight": "F",
    "landed": "L",
    "emergency": "!",
    "abnormal": "?",
}

# Map each front checklist to a phase
FRONT_PHASES = {
    "Before Starting Engine": "preflight",
    "Engine Start": "preflight",
    "Post Engine Start": "preflight",
    "Engine Runup": "preflight",
    "Departure Preparation": "preflight",
    "Enroute Climb": "inflight",
    "Cruise": "inflight",
    "VFR Approach": "inflight",
    "IFR Approach": "inflight",
    "Clear Runway": "landed",
    "Shutdown": "landed",
}


def render_section(checklist, css_class="normal"):
    """Render a checklist section box."""
    badge = SECTION_EMOJI.get(css_class, "")
    badge_html = f'<span class="badge">{badge}</span>' if badge else ""
    items_html = "\n".join(render_item(i) for i in checklist["items"])
    return (
        f'<div class="section {css_class}">'
        f'{badge_html}'
        f'<div class="section-title">{escape(checklist["title"])}</div>'
        f'<div class="section-body">{items_html}</div>'
        f'</div>'
    )


# ── Local frequencies ─────────────────────────────────────────────────
FREQUENCIES = [
    ("KPAE", [
        ("ATIS", "128.65"),
        ("Gnd", "121.8"),
        ("Twr E", "120.2"),
        ("Twr W", "132.95"),
        ("App", "128.5"),
    ]),
    ("KNUW", [
        ("E", "120.7"),
        ("W", "118.2"),
    ]),
    ("KORS", [
        ("CTAF", "128.25"),
    ]),
    ("KAWO", [
        ("CTAF", "122.725"),
    ]),
    ("KBVS", [
        ("CTAF", "123.075"),
    ]),
    ("SEA App", [
        ("S", "119.2"),
        ("N", "128.5"),
    ]),
]


def render_freq_bar():
    """Render frequencies as a compact two-line horizontal bar."""
    groups = []
    for group_name, freqs in FREQUENCIES:
        pairs = " ".join(f'<span class="freq-pair"><b>{escape(label)}</b> {escape(freq)}</span>' for label, freq in freqs)
        groups.append(f'<span class="freq-grp"><span class="freq-id">{escape(group_name)}</span>{pairs}</span>')
    return f'<div class="freq-bar">{"".join(groups)}</div>'


def build_front(data):
    """Build front page with normal procedures."""
    cl_by_name = {}
    for g in data["groups"]:
        for cl in g["checklists"]:
            cl_by_name[cl["title"]] = cl

    sections = []
    for name in FRONT_CHECKLISTS:
        if name in cl_by_name:
            phase = FRONT_PHASES.get(name, "preflight")
            sections.append(render_section(cl_by_name[name], phase))
    return sections


def build_back(data):
    """Build back page with emergency & abnormal procedures."""
    cl_by_name = {}
    group_for = {}
    for g in data["groups"]:
        for cl in g["checklists"]:
            cl_by_name[cl["title"]] = cl
            group_for[cl["title"]] = g["title"]

    sections = []
    for name in BACK_CHECKLISTS:
        if name in cl_by_name:
            css = "emergency" if group_for[name] == "Emergency" else "abnormal"
            sections.append(render_section(cl_by_name[name], css))
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
  <div class="page-header">Quick Reference Checklist</div>
  {render_freq_bar()}
  <div class="columns front-cols">
    {"".join(front_sections)}
  </div>
</div>

<!-- BACK SIDE -->
<div class="page">
  <div class="sidebar">
    {escape(aircraft)}
    <span class="sub">&mdash; Emergency &amp; Abnormal</span>
  </div>
  <div class="page-header">Emergency &amp; Abnormal Procedures</div>
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
