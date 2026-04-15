"""HTML report generator — turns an analysis receipt into a shareable single-file document.

Pure function: takes analysis result + stamp, returns HTML string.
No I/O. The caller saves it.
"""

from __future__ import annotations
from typing import Any


def render_html_report(
    result: dict[str, Any],
    stamp_data: dict[str, Any],
    target: str = "",
    metadata: dict[str, Any] | None = None,
) -> str:
    """Render a governance report as a self-contained HTML file. Pure."""

    s = result.get("summary", {})
    violations = result.get("violations", [])
    metadata = metadata or {}

    # Separate smoking gun from rest
    dangerous = [v for v in violations if v.get("type") in ("dangerous_deserialization", "code_execution", "dangerous_code_enabled", "constraint_violation")]
    other_violations = [v for v in violations if v not in dangerous]
    smoking_gun = (dangerous or violations[:1] or [None])[0]

    # File results
    file_results = result.get("files", {})

    # Build function rows
    function_rows = []
    for fname, fdata in sorted(file_results.items()):
        for f in fdata.get("functions", []):
            purity = "pure" if f.get("is_pure") else "impure"
            mt = f.get("mother_type", "?")
            st = f.get("subtype", "?")
            function_rows.append({
                "file": fname,
                "name": f["name"],
                "line": f.get("lineno", "?"),
                "mother_type": mt,
                "subtype": st,
                "purity": purity,
                "violations": f.get("violations", []),
            })

    # External deps
    external_deps = s.get("external_deps", [])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Substrate Report — {_esc(target)}</title>
<style>
:root {{
  --bg: #0d1117; --bg2: #161b22; --card: #1c2128; --border: #30363d;
  --text: #e6edf3; --text2: #8b949e; --text3: #6e7681;
  --accent: #58a6ff; --green: #3fb950; --yellow: #d29922;
  --red: #f85149; --purple: #bc8cff; --orange: #ffa657;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: var(--bg); color: var(--text);
  max-width: 900px; margin: 0 auto; padding: 24px 16px;
  line-height: 1.6;
}}
h1 {{ font-size: 18px; font-weight: 600; margin-bottom: 4px; }}
h2 {{ font-size: 14px; font-weight: 600; color: var(--text2); margin: 24px 0 8px; text-transform: uppercase; letter-spacing: 0.05em; }}
.subtitle {{ font-size: 12px; color: var(--text3); margin-bottom: 20px; }}
.stats {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px; margin-bottom: 20px;
}}
.stat {{
  background: var(--card); border: 1px solid var(--border); border-radius: 6px;
  padding: 10px 12px; text-align: center;
}}
.stat-val {{ font-size: 22px; font-weight: 700; }}
.stat-label {{ font-size: 10px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.05em; }}
.stat-red .stat-val {{ color: var(--red); }}
.stat-green .stat-val {{ color: var(--green); }}
.stat-accent .stat-val {{ color: var(--accent); }}

.smoking-gun {{
  background: rgba(248,81,73,0.08); border: 1px solid var(--red); border-radius: 8px;
  padding: 16px; margin-bottom: 20px;
}}
.smoking-gun-label {{
  font-size: 10px; font-weight: 700; color: var(--red);
  text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;
}}
.smoking-gun-msg {{ font-size: 14px; color: var(--text); font-weight: 500; }}
.smoking-gun-loc {{ font-size: 11px; color: var(--text3); margin-top: 4px; }}

.violation {{
  background: var(--card); border: 1px solid var(--border); border-radius: 6px;
  padding: 10px 12px; margin-bottom: 6px;
}}
.v-header {{ display: flex; gap: 8px; align-items: center; }}
.v-type {{
  font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 3px;
  text-transform: uppercase; letter-spacing: 0.04em;
}}
.v-constraint {{ background: rgba(248,81,73,0.15); color: var(--red); }}
.v-contract {{ background: rgba(88,166,255,0.15); color: var(--accent); }}
.v-witness {{ background: rgba(188,140,255,0.15); color: var(--purple); }}
.v-uncertainty {{ background: rgba(210,153,34,0.15); color: var(--yellow); }}
.v-relation {{ background: rgba(63,185,80,0.15); color: var(--green); }}
.v-loc {{ font-size: 11px; color: var(--text3); }}
.v-msg {{ font-size: 12px; color: var(--text2); margin-top: 4px; }}

table {{
  width: 100%; border-collapse: collapse; font-size: 11px; margin-bottom: 16px;
}}
th {{
  text-align: left; font-size: 10px; color: var(--text3); padding: 6px 8px;
  border-bottom: 1px solid var(--border); text-transform: uppercase; letter-spacing: 0.04em;
}}
td {{ padding: 6px 8px; border-bottom: 1px solid rgba(48,54,61,0.5); color: var(--text2); }}
.pure {{ color: var(--green); }}
.impure {{ color: var(--red); }}
.tag {{
  font-size: 9px; font-weight: 600; padding: 1px 5px; border-radius: 3px;
  display: inline-block;
}}
.tag-contract {{ background: rgba(88,166,255,0.15); color: var(--accent); }}
.tag-constraint {{ background: rgba(248,81,73,0.15); color: var(--red); }}
.tag-uncertainty {{ background: rgba(210,153,34,0.15); color: var(--yellow); }}
.tag-relation {{ background: rgba(63,185,80,0.15); color: var(--green); }}
.tag-witness {{ background: rgba(188,140,255,0.15); color: var(--purple); }}

.dep {{ padding: 4px 0; font-size: 11px; color: var(--text2); }}
.dep-unstamped {{ color: var(--orange); }}

.receipt {{
  background: var(--card); border: 1px solid var(--border); border-radius: 6px;
  padding: 12px; font-family: 'SF Mono', 'Fira Code', monospace; font-size: 11px;
  color: var(--text3); word-break: break-all; line-height: 1.8;
}}
.receipt-label {{ color: var(--text2); }}

.footer {{
  margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border);
  font-size: 10px; color: var(--text3); text-align: center;
}}
</style>
</head>
<body>

<h1>Substrate Governance Report</h1>
<div class="subtitle">{_esc(target)} &middot; {s.get('total_files', 0)} files &middot; {metadata.get('elapsed_s', '?')}s</div>

<div class="stats">
  <div class="stat stat-accent"><div class="stat-val">{s.get('total_functions', 0)}</div><div class="stat-label">Functions</div></div>
  <div class="stat stat-green"><div class="stat-val">{s.get('pure_count', 0)}</div><div class="stat-label">Pure</div></div>
  <div class="stat"><div class="stat-val">{s.get('impure_count', 0)}</div><div class="stat-label">Impure</div></div>
  <div class="stat stat-red"><div class="stat-val">{len(violations)}</div><div class="stat-label">Violations</div></div>
  <div class="stat"><div class="stat-val">{len(external_deps)}</div><div class="stat-label">Unstamped Deps</div></div>
</div>

"""

    # Smoking gun
    if smoking_gun:
        fn = smoking_gun.get("function") or "module"
        line = smoking_gun.get("line", "?")
        html += f"""<div class="smoking-gun">
  <div class="smoking-gun-label">Smoking Gun</div>
  <div class="smoking-gun-msg">{_esc(smoking_gun['message'])}</div>
  <div class="smoking-gun-loc">{_esc(fn)}:{line} &middot; {_esc(smoking_gun.get('file', ''))}</div>
</div>
"""

    # Violations
    remaining = [v for v in violations if v is not smoking_gun]
    if remaining:
        html += f'<h2>Violations ({len(remaining)} more)</h2>\n'
        for v in remaining:
            mt = v.get("mother_type", "?")
            css = f"v-{mt.lower()}" if mt in ("CONSTRAINT", "CONTRACT", "WITNESS", "UNCERTAINTY", "RELATION") else ""
            fn = v.get("function") or "module"
            html += f"""<div class="violation">
  <div class="v-header">
    <span class="v-type {css}">{_esc(mt)}</span>
    <span class="v-loc">{_esc(fn)}:{v.get('line', '?')}</span>
  </div>
  <div class="v-msg">{_esc(v['message'])}</div>
</div>
"""

    # Functions table
    if function_rows:
        html += '<h2>Functions</h2>\n<table>\n<tr><th>Function</th><th>File</th><th>Line</th><th>Type</th><th>Purity</th></tr>\n'
        for fr in function_rows:
            mt = fr["mother_type"]
            tag_css = f"tag-{mt.lower()}" if mt in ("CONTRACT", "CONSTRAINT", "UNCERTAINTY", "RELATION", "WITNESS") else ""
            purity_css = "pure" if fr["purity"] == "pure" else "impure"
            html += f'<tr><td>{_esc(fr["name"])}()</td><td>{_esc(fr["file"])}</td><td>{fr["line"]}</td>'
            html += f'<td><span class="tag {tag_css}">{_esc(mt)}</span></td>'
            html += f'<td class="{purity_css}">{fr["purity"]}</td></tr>\n'
        html += '</table>\n'

    # Dependencies
    if external_deps:
        html += '<h2>Unstamped Dependencies</h2>\n'
        for dep in external_deps:
            html += f'<div class="dep dep-unstamped">&#9888; {_esc(dep)} — no provenance receipt</div>\n'

    # Receipt
    html += '<h2>Receipt</h2>\n<div class="receipt">\n'
    for key in ("stamp_hash", "input_hash", "fn_hash", "output_hash", "prev_stamp_hash", "schema", "domain"):
        val = stamp_data.get(key, "")
        if val:
            html += f'<span class="receipt-label">{key}:</span> {_esc(str(val))}<br>\n'
    html += '</div>\n'

    # Verify
    html += f"""
<div style="margin-top:12px; font-size:11px; color:var(--text3);">
  Verify: <code>substrate verify receipt.json</code>
</div>
"""

    # Footer
    html += f"""
<div class="footer">
  Generated by Substrate v{metadata.get('version', '0.1.0')} &middot;
  analyzer hash: {_esc(metadata.get('analyzer_hash', '?')[:16])}...
</div>

</body>
</html>"""

    return html


def _esc(s: str) -> str:
    """HTML-escape a string. Pure."""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
