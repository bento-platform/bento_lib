"""
Render DatasetModelBase as a static data-dictionary page (in the style of https://dict.cqdg.ca/en/).

Usage: python scripts/build_dataset_dictionary.py [--out site/index.html]
"""

import argparse
import types
from html import escape
from pathlib import Path
from typing import Annotated, Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from bento_lib.i18n import TranslatedLiteral
from bento_lib.provenance.dataset import DatasetModelBase

MAX_VALUES_SHOWN = 5
SCALARS = {str: "TEXT", int: "INTEGER", float: "NUMBER", bool: "BOOLEAN"}

CSS = """
:root{--fg:#1f2937;--muted:#6b7280;--line:#e5e7eb;--accent:#0b5cab;--bg:#fff;--soft:#f3f6fa}
@media (prefers-color-scheme:dark){:root{--fg:#e5e7eb;--muted:#9ca3af;--line:#374151;--accent:#6cb2ff;--bg:#111827;--soft:#1f2937}}
*{box-sizing:border-box}body{margin:0;font:14px/1.5 system-ui,sans-serif;color:var(--fg);background:var(--bg);display:flex}
nav{position:sticky;top:0;align-self:flex-start;height:100vh;overflow:auto;width:230px;padding:16px;border-right:1px solid var(--line)}
nav a{display:block;padding:3px 0;color:var(--accent);text-decoration:none}
main{flex:1;min-width:0;padding:16px 24px}
.toolbar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:16px}
select,button{font:inherit;padding:4px 8px;color:var(--fg);background:var(--bg);border:1px solid var(--line);border-radius:4px}
section{margin-bottom:40px}h2{margin:0}h2 small{color:var(--muted);font-weight:400}
.desc{color:var(--muted);margin:4px 0 8px}
table{width:100%;border-collapse:collapse}
th{background:var(--soft);text-align:left}th,td{border:1px solid var(--line);padding:6px 8px;vertical-align:top}
td.field b{display:block}td.field span{color:var(--muted)}
.pill{padding:1px 8px;border-radius:10px;background:var(--soft);font-size:12px}
.pill.req{background:var(--accent);color:var(--bg)}
.vals b{margin-right:6px}details{display:inline}summary{cursor:pointer;color:var(--accent);display:inline}
a{color:var(--accent)}
"""

JS = """
const sel = document.getElementById('attr');
sel.onchange = () => document.querySelectorAll('tr[data-attr]').forEach(
  r => r.hidden = sel.value && r.dataset.attr !== sel.value);
document.getElementById('reset').onclick = () => { sel.value = ''; sel.onchange(); };
"""


def _walk(annotation: Any) -> list[Any]:
    """Flatten unions/lists/Annotated into the leaf types and metadata they contain."""
    origin = get_origin(annotation)
    if origin is Annotated:
        base, *meta = get_args(annotation)
        return [*_walk(base), *meta]
    if origin in (Union, types.UnionType, list, dict):
        return [leaf for arg in get_args(annotation) for leaf in _walk(arg)]
    return [annotation]


def _nested_models(annotation: Any) -> list[type[BaseModel]]:
    return [x for x in _walk(annotation) if isinstance(x, type) and issubclass(x, BaseModel)]


def _type_label(annotation: Any) -> str:
    leaves = [leaf for leaf in _walk(annotation) if leaf is not type(None)]
    labels = []
    for leaf in leaves:
        if leaf in SCALARS:
            labels.append(SCALARS[leaf])
        elif isinstance(leaf, type) and issubclass(leaf, BaseModel):
            labels.append(f'<a href="#{leaf.__name__}">{leaf.__name__}</a>')
        elif get_origin(leaf) is Literal:
            labels.append("TEXT")
        elif isinstance(leaf, type):
            labels.append(leaf.__name__.upper())
    labels = list(dict.fromkeys(labels))
    is_list = get_origin(annotation) is list or any(get_origin(a) is list for a in get_args(annotation))
    return escape("ARRAY OF ") * is_list + " | ".join(labels)  # labels already escaped


def _permitted_values(annotation: Any) -> list[str]:
    values: list[str] = []
    for leaf in _walk(annotation):
        if get_origin(leaf) is Literal:
            values.extend(str(v) for v in get_args(leaf))
        elif isinstance(leaf, TranslatedLiteral):
            values.extend(sorted(leaf.en_values))
    return values


def _values_html(values: list[str]) -> str:
    shown = "".join(f"<b>{escape(v)}</b>" for v in values[:MAX_VALUES_SHOWN])
    rest = values[MAX_VALUES_SHOWN:]
    if rest:
        more = "".join(f"<b>{escape(v)}</b>" for v in rest)
        shown += f"<details><summary>{len(rest)} more</summary>{more}</details>"
    return f'<div class="vals">{shown}</div>'


def _notes(field: FieldInfo) -> str:
    notes = []
    for m in field.metadata:
        notes += [f"{k}: {getattr(m, k)}" for k in ("min_length", "max_length", "pattern", "ge", "le") if hasattr(m, k)]
    return escape("; ".join(notes))


def _row(name: str, field: FieldInfo) -> str:
    attr = "Required" if field.is_required() else "Optional"
    cls = "pill req" if field.is_required() else "pill"
    return (
        f'<tr data-attr="{attr}"><td class="field"><b>{escape(name)}</b>'
        f"<span>{escape(field.description or '')}</span></td>"
        f'<td><span class="{cls}">{attr}</span></td>'
        f"<td>{_type_label(field.annotation)}</td>"
        f"<td>{_values_html(_permitted_values(field.annotation))}</td>"
        f"<td>{_notes(field)}</td></tr>"
    )


def _collect_models(root: type[BaseModel]) -> list[type[BaseModel]]:
    seen: dict[type[BaseModel], None] = {}
    stack = [root]
    while stack:
        model = stack.pop(0)
        if model in seen:
            continue
        seen[model] = None
        for field in model.model_fields.values():
            stack.extend(_nested_models(field.annotation))
    return list(seen)


def model_to_dictionary_html(root: type[BaseModel]) -> str:
    models = _collect_models(root)
    total = sum(len(m.model_fields) for m in models)
    nav = "".join(f'<a href="#{m.__name__}">{m.__name__}</a>' for m in models)
    sections = "".join(
        f'<section id="{m.__name__}"><h2>{m.__name__} <small>{len(m.model_fields)} fields</small></h2>'
        f'<p class="desc">{escape((m.__doc__ or "").strip().splitlines()[0] if m.__doc__ else "")}</p>'
        "<table><thead><tr><th>Field and description</th><th>Attributes</th><th>Type</th>"
        "<th>Permitted values</th><th>Notes</th></tr></thead><tbody>"
        + "".join(_row(n, f) for n, f in m.model_fields.items())
        + "</tbody></table></section>"
        for m in models
    )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{root.__name__} data dictionary</title><style>{CSS}</style></head><body>"
        f"<nav>{nav}</nav><main><h1>Data dictionary: {root.__name__}</h1>"
        f"<div class='toolbar'><span>{len(models)} models with {total} fields</span>"
        "<select id='attr'><option value=''>Attributes: all</option>"
        "<option>Required</option><option>Optional</option></select>"
        f"<button id='reset'>Reset</button></div>{sections}<script>{JS}</script></main></body></html>"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("site/index.html"))
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(model_to_dictionary_html(DatasetModelBase), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
