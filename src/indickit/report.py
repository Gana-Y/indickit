"""Turn benchmark results into a Markdown table or an SVG heatmap."""
from __future__ import annotations

from html import escape
from typing import Dict

from .bench import KIND_LABELS, KINDS, aggregate
from .corpus import LANGUAGES


def to_markdown(data: dict) -> str:
    table = aggregate(data)
    kinds = [k for k in KINDS if any(k in row for row in table.values())]
    model = data["meta"].get("model", "?")
    lines = [f"**Model:** `{model}`  ·  {data['meta'].get('tasks', len(data['results']))} tasks", ""]
    lines.append("| Language | " + " | ".join(KIND_LABELS[k] for k in kinds) + " | **Overall** |")
    lines.append("|---|" + "---:|" * (len(kinds) + 1))
    for lang, row in sorted(table.items(), key=lambda kv: -kv[1]["overall"]):
        cells = " | ".join(f"{row[k]*100:.0f}" if k in row else "–" for k in kinds)
        lines.append(f"| {LANGUAGES[lang][0]} | {cells} | **{row['overall']*100:.0f}** |")
    errors = sum(1 for r in data["results"] if r.get("error"))
    if errors:
        lines += ["", f"⚠️ {errors} request(s) failed and were scored 0."]
    lines += ["", "Scores are 0–100. translate/translit use chrF; respond = share of letters in the right script; "
              "numerals/script_id are exact match."]
    return "\n".join(lines)


def _color(v: float) -> str:
    # red (0) -> amber -> green (1)
    v = max(0.0, min(1.0, v))
    if v < 0.5:
        t = v / 0.5
        r, g, b = 220, int(70 + 130 * t), 70
    else:
        t = (v - 0.5) / 0.5
        r, g, b = int(220 - 150 * t), int(200 - 20 * t), int(70 + 20 * t)
    return f"rgb({r},{g},{b})"


def to_svg(data: dict) -> str:
    table = aggregate(data)
    kinds = [k for k in KINDS if any(k in row for row in table.values())]
    langs = sorted(table, key=lambda l: -table[l]["overall"])
    cw, ch, left, top = 112, 34, 130, 86
    width = left + cw * (len(kinds) + 1) + 20
    height = top + ch * len(langs) + 30
    sans = "-apple-system,'Segoe UI',Roboto,'Noto Sans',Helvetica,Arial,sans-serif"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="{sans}">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="16" y="28" font-size="18" font-weight="700" fill="#111">Indic language benchmark: {escape(str(data["meta"].get("model", "?")))}</text>',
        '<text x="16" y="48" font-size="12" fill="#555">score 0-100, higher is better (rule-based, no judge model)</text>',
    ]
    heads = [KIND_LABELS[k] for k in kinds] + ["Overall"]
    for j, h in enumerate(heads):
        out.append(f'<text x="{left + j*cw + cw/2}" y="{top-14}" font-size="12" font-weight="600" text-anchor="middle" fill="#222">{escape(h)}</text>')
    for i, lang in enumerate(langs):
        y = top + i * ch
        out.append(f'<text x="16" y="{y + ch/2 + 5}" font-size="13" fill="#222">{escape(LANGUAGES[lang][0])}</text>')
        for j, k in enumerate(kinds + ["overall"]):
            v = table[lang].get(k)
            x = left + j * cw
            if v is None:
                out.append(f'<rect x="{x+2}" y="{y+2}" width="{cw-4}" height="{ch-4}" rx="5" fill="#eee"/><text x="{x+cw/2}" y="{y+ch/2+5}" text-anchor="middle" font-size="13" fill="#999">–</text>')
                continue
            bold = ' font-weight="700"' if k == "overall" else ""
            out.append(
                f'<rect x="{x+2}" y="{y+2}" width="{cw-4}" height="{ch-4}" rx="5" fill="{_color(v)}"/>'
                f'<text x="{x+cw/2}" y="{y+ch/2+5}" text-anchor="middle" font-size="13" fill="#fff"{bold}>{v*100:.0f}</text>'
            )
    out.append("</svg>")
    return "\n".join(out)
