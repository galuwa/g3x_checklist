#!/usr/bin/env python3
"""
Re-implementation of the original Scala checklist generator.

Outputs:
  build/N89SF_Checklist.html   – interactive / mobile
  build/N89SF_Checklist.ace    – Garmin ACE file (CRC OK)
  hackedminimal.ace            – tiny self-test file
"""

import json, zlib
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

# -------------------------------------------------------------------- #
CRLF       = "\r\n"
JSON_PATH  = Path("checklist.json")      # adjust if needed
BUILD_DIR  = Path("build"); BUILD_DIR.mkdir(exist_ok=True)

# -------------------------------------------------------------------- #
# Data classes mirroring JSON content
# -------------------------------------------------------------------- #
@dataclass
class ChecklistItem:
    uuid:   str
    action: str
    itemType: int
    title:  str

@dataclass
class Checklist:
    uuid:   str
    checklistItems: List[str]
    name:   str
    type:   int
    subtype:int

# Helper to ignore extra keys the dataclass doesn’t expect
def mk_item(d: dict) -> ChecklistItem:
    return ChecklistItem(
        uuid      = d["uuid"],
        action    = d.get("action",""),
        itemType  = d.get("itemType",0),
        title     = d.get("title","")
    )
def mk_checklist(d: dict) -> Checklist:
    return Checklist(
        uuid            = d["uuid"],
        checklistItems  = d["checklistItems"],
        name            = d["name"],
        type            = d["type"],
        subtype         = d["subtype"]
    )

# -------------------------------------------------------------------- #
# Load JSON
# -------------------------------------------------------------------- #
raw = json.load(JSON_PATH.open(encoding="utf-8"))
item_map: Dict[str, ChecklistItem]  = {i.uuid: i for i in map(mk_item,      raw["checklistItems"])}
checklist_map: Dict[str, Checklist] = {c.uuid: c for c in map(mk_checklist, raw["checklists"])}
binder_order: List[str]             = raw["binders"][0]["checklists"]

# -------------------------------------------------------------------- #
# Category filters
# -------------------------------------------------------------------- #
def preflight(c):  return c.subtype == 0 and c.type == 0
def cruise(c):     return c.subtype == 1 and c.type == 0
def landing(c):    return c.subtype == 2 and c.type == 0
def other(c):      return c.subtype == 3 and c.type == 0
def abnormal(c):   return c.type == 1
def emergency(c):  return c.type == 2

def is_note(itm: ChecklistItem) -> bool:
    return itm.itemType == 11 and not itm.action

# -------------------------------------------------------------------- #
# HTML generation (interactive / responsive)
# -------------------------------------------------------------------- #
STYLE = """
body {font-family:-apple-system,BlinkMacSystemFont,sans-serif;margin:12px;background:#fafafa;}
h1,h2,h3 {text-align:center;color:#004080;margin:0.4em 0;}

/* collapsible section */
details {border:1px solid #000;margin:10px 0;border-radius:4px;background:#fff;}
summary {padding:6px 10px;cursor:pointer;font-weight:bold;background:#eee;position:sticky;top:0;}
details[open] summary {border-bottom:1px solid #000;}

/* list rows */
ul {padding-left:0;margin:0;}
li {list-style:none;border-bottom:1px solid #ddd;padding:0.45em 0;
    display:flex;align-items:flex-start;justify-content:space-between;column-gap:10px;
    user-select:none;cursor:pointer;}
li.checked {text-decoration:line-through;opacity:.6;}

.title  {flex:1 1 auto;min-width:0;}                /* allow shrinking */
.action {flex:0 0 auto;text-align:right;color:#333;white-space:nowrap;}

.note   {justify-content:center;font-weight:bold;font-style:italic;background:#f2f2f2;}

input[type=checkbox]{transform:scale(1.25);margin:2px 4px 0 0;pointer-events:none;}

@media(max-width:600px){
  /* still keep single line; increase gap a bit */
  .action{margin-left:8px;}
  input[type=checkbox]{transform:scale(1.3);}
}

  /* Clear-All button */
  .clear-btn{
    display:inline-block;background:#c62828;color:#fff;border:none;border-radius:4px;
    padding:6px 14px;margin:10px auto;font-size:.9rem;cursor:pointer;
    box-shadow:0 1px 3px rgba(0,0,0,.3);
  }
"""

SCRIPT = """
document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('li[data-uuid]').forEach(row=>{
    const box=row.querySelector('input');
    const key='chk-'+row.dataset.uuid;

    // initial state
    box.checked=localStorage.getItem(key)==='1';
    row.classList.toggle('checked',box.checked);

  /* ---- Clear-All ---- */
  const reset=document.getElementById('reset');
  if(reset) reset.addEventListener('click',()=>{
    document.querySelectorAll('li[data-uuid]').forEach(row=>{
      const box=row.querySelector('input');
      const k='chk-'+row.dataset.uuid;
      localStorage.removeItem(k);
      box.checked=false;
      row.classList.remove('checked');
    });
  });

    // toggle on row-click
    row.addEventListener('click',()=>{
      box.checked=!box.checked;
      localStorage.setItem(key,box.checked?'1':'0');
      row.classList.toggle('checked',box.checked);
    });
  });
});
"""

def render_checklist(cl: Checklist) -> str:
    rows = []
    for uid in cl.checklistItems:
        itm = item_map[uid]
        if is_note(itm):
            rows.append(f'<li class="note"><span>{itm.title}</span></li>')
        else:
            action_html = (f'<span class="action">{itm.action}</span>' if itm.action else '')
            rows.append(
                f'<li data-uuid="{uid}">'
                f'<input type="checkbox"><span class="title">{itm.title}</span>{action_html}</li>')

    cols = "2" if cl.name == "Preflight Inspection" else "1"
    return (
        f'<details style="column-count:{cols};page-break-inside:avoid;">'
        f'  <summary>{cl.name}</summary>'
        f'  <ul>{"".join(rows)}</ul>'
        f'</details>'
    )

def build_html() -> str:
    sections=[
        ("Normal Procedures",[("Preflight",preflight),
                              ("Takeoff/cruise",cruise),
                              ("Landing",landing),
                              ("Other",other)]),
        ("Abnormal Procedures",[("",abnormal)]),
        ("Emergency Procedures",[("",emergency)]),
    ]
    body=[]
    for hdr,sub in sections:
        body.append(f'<h2>{hdr}</h2>')
        for lab,flt in sub:
            if lab: body.append(f'<h3>{lab}</h3>')
            for cid in binder_order:
                cl=checklist_map[cid]
                if flt(cl): body.append(render_checklist(cl))
    return f"""<!doctype html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>N89SF Checklist</title><style>{STYLE}</style><script>{SCRIPT}</script>
</head><body>
<h1>N89SF – C177RG</h1>
<p style="text-align:center;font-style:italic;margin-top:0;">Luke Miller</p>
<button class="clear-btn" id="reset">Clear All Checks</button>
<div>{"".join(body)}</div></body></html>"""

# -------------------------------------------------------------------- #
# ACE file generation (byte-perfect)
# -------------------------------------------------------------------- #
def ace_lines(items):
    for uid in items:
        itm=item_map[uid]
        yield (f"p0{itm.title}{itm.action}" if itm.itemType==11
               else f"r0{itm.title}~{itm.action}")

def ace_block(label,flt):
    inner=[]
    for cid in binder_order:
        cl=checklist_map[cid]
        if flt(cl):
            inner.append("(0"+cl.name+CRLF+CRLF.join(ace_lines(cl.checklistItems))+CRLF+")")
    return f"<0{label}{CRLF}{CRLF.join(inner)}{CRLF}>{CRLF}"

def build_ace() -> bytes:
    body=( ace_block("Preflight",preflight)+ace_block("Cruise",cruise)+
           ace_block("Landing",landing)+ace_block("Abnormal",abnormal)+
           ace_block("Emergency",emergency)+"END"+CRLF )

    magic=b"\xF0\xF0\xF0\xF0"
    revision=b"\x00\x01\x00\x00"
    header_lines=[
        "GARMIN CHECKLIST PN XXX-XXXXX-XX",
        "Aircraft Make and Model",
        "Aircraft specific identification",
        "Manufacturer Identification",
        "Copyright Information",
    ]
    header=CRLF.join(header_lines)+CRLF
    full=(magic+revision+CRLF.encode("latin-1")+
          header.encode("latin-1")+body.encode("latin-1"))

    crc=zlib.crc32(full)&0xFFFFFFFF
    big=crc.to_bytes(4,"big")
    if big[0]&0x80: big=b"\x00"+big            # Scala’s signed BigInt quirk
    little=big[::-1][:4]
    inv=bytes(~b & 0xFF for b in little)
    return full+inv

# -------------------------------------------------------------------- #
# Main
# -------------------------------------------------------------------- #
def main():
    (BUILD_DIR/"N89SF_Checklist.html").write_text(build_html(),encoding="utf-8")
    (BUILD_DIR/"N89SF_Checklist.ace").write_bytes(build_ace())
    print("✅  Files generated in ./build (HTML interactive, ACE correct)")

if __name__=="__main__":
    main()
