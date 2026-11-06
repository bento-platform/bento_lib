"""
Render DatasetModelBase as a static data-dictionary page.

Usage: python scripts/build_dataset_dictionary.py [--out site/index.html]
"""

import argparse
import types
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from html import escape
from pathlib import Path
from typing import Annotated, Any, Literal, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, RootModel
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
td.field code{display:block;color:var(--muted);font-size:12px}
td.child{padding:0 0 0 20px;border-right:0;background:var(--soft)}
td.child>details{display:block;border-left:3px solid var(--accent)}
td.child>details>summary{display:block;padding:6px 10px;font-weight:600}
td.child table{background:var(--bg)}
nav details{display:block}nav summary{display:block;color:var(--fg)}
nav details>div{margin-left:12px;border-left:1px solid var(--line);padding-left:8px}
.intro{max-width:70ch;margin-bottom:16px}.intro p{margin:0 0 8px}.intro ul{margin:0;padding-left:20px}
tr:target>td,details:target>summary{outline:2px solid var(--accent)}
"""

INTRO = """
<div class="intro">
<p>This page documents the metadata schema used to describe a dataset in Bento: every field a dataset record
can contain, whether it is required, the type of value it takes, and the values it permits. It is generated
directly from the <code>bento_lib</code> dataset models, so it always matches the code.</p>
<ul>
<li><b>Required</b> fields must be present for a record to be valid; <b>Optional</b> fields may be omitted.</li>
<li>A field whose type is another model (for example <i>Person</i> or <i>License</i>) has an expandable block
beneath it listing that model's own fields. Blocks nest as deeply as the schema does.</li>
<li><i>ARRAY OF</i> means the field takes a list of values. A path such as <code>stakeholders[] › contact</code>
reads as "the <i>contact</i> of each item in <i>stakeholders</i>".</li>
<li>Use the sidebar to jump to a nested model, and the filter to show only required or optional fields.</li>
</ul>
</div>
"""

JS = """
const sel = document.getElementById('attr');
sel.onchange = () => document.querySelectorAll('tr[data-attr]').forEach(
  r => r.hidden = sel.value && r.dataset.attr !== sel.value);
document.getElementById('reset').onclick = () => { sel.value = ''; sel.onchange(); };
const setAll = open => document.querySelectorAll('td.child details').forEach(d => d.open = open);
document.getElementById('expand').onclick = () => setAll(true);
document.getElementById('collapse').onclick = () => setAll(false);
const reveal = () => {
  const el = document.getElementById(decodeURIComponent(location.hash.slice(1)));
  for (let d = el; d; d = d.parentElement) if (d.tagName === 'DETAILS') d.open = true;
  if (el) el.scrollIntoView();
};
addEventListener('hashchange', reveal);
reveal();
"""


CONSTRAINTS = ("min_length", "max_length", "pattern", "ge", "le", "gt", "lt")


@dataclass(frozen=True)
class Variant:
    """One branch of a (possibly union) annotation, with the container and constraints that apply to it."""

    leaf: Any
    container: str | None = None  # "ARRAY OF" / "MAP OF"
    constraints: tuple[tuple[str, Any], ...] = ()
    translated: TranslatedLiteral | None = None


def _constraints(items: Iterable[Any]) -> tuple[tuple[str, Any], ...]:
    found: dict[str, Any] = {}
    for item in items:
        if isinstance(item, FieldInfo):  # e.g. Annotated[str, Field(min_length=1)]
            found.update(_constraints(item.metadata))
        else:
            found.update({k: getattr(item, k) for k in CONSTRAINTS if hasattr(item, k)})
    return tuple(found.items())


def _variants(
    annotation: Any,
    container: str | None = None,
    constraints: tuple[tuple[str, Any], ...] = (),
    translated: TranslatedLiteral | None = None,
) -> list[Variant]:
    """
    Flatten an annotation into its union branches. Raises on anything it cannot document faithfully, so that
    the generated page never silently misstates the schema (and CI fails instead).
    """
    origin = get_origin(annotation)
    if origin is Annotated:
        base, *meta = get_args(annotation)
        tl = next((m for m in meta if isinstance(m, TranslatedLiteral)), translated)
        return _variants(base, container, (*constraints, *_constraints(meta)), tl)
    if origin in (Union, types.UnionType):
        return [v for arg in get_args(annotation) for v in _variants(arg, container, constraints, translated)]
    if origin is list:
        return _variants(get_args(annotation)[0], "ARRAY OF", constraints, translated)
    if origin is tuple:
        args = get_args(annotation)
        if len(args) == 2 and args[1] is Ellipsis:
            return _variants(args[0], "ARRAY OF", constraints, translated)
        if args and len(set(args)) == 1:  # fixed-length, homogeneous (e.g. a GeoJSON bbox)
            return _variants(args[0], "ARRAY OF", (*constraints, ("length", len(args))), translated)
        raise TypeError(f"Unsupported type in data dictionary: {annotation!r}")
    if origin is dict:
        return _variants(get_args(annotation)[1], "MAP OF", constraints, translated)
    if annotation is type(None):
        return []
    if isinstance(annotation, TypeVar):  # unparametrized generic model: pydantic validates against the bound
        if annotation.__bound__ is not None:
            return _variants(annotation.__bound__, container, constraints, translated)
        if annotation.__constraints__:
            return [v for c in annotation.__constraints__ for v in _variants(c, container, constraints, translated)]
    if isinstance(annotation, type) and issubclass(annotation, RootModel):
        # Transparent wrapper (e.g. a discriminated union): document what it wraps, not a lone "root" field
        return _variants(annotation.model_fields["root"].annotation, container, constraints, translated)
    if origin is Literal or (origin is None and isinstance(annotation, type)):
        return [Variant(annotation, container, constraints, translated)]
    raise TypeError(f"Unsupported type in data dictionary: {annotation!r}")


def _nested_models(annotation: Any) -> list[type[BaseModel]]:
    return [v.leaf for v in _variants(annotation) if isinstance(v.leaf, type) and issubclass(v.leaf, BaseModel)]


def _leaf_label(leaf: Any) -> str:
    if leaf in SCALARS:
        return SCALARS[leaf]
    if get_origin(leaf) is Literal:
        return "TEXT"
    if issubclass(leaf, BaseModel):
        return leaf.__name__
    return leaf.__name__.upper()


def _variant_label(v: Variant) -> str:
    return (f"{v.container} " if v.container else "") + _leaf_label(v.leaf)


def _type_label(annotation: Any) -> str:
    return escape(" | ".join(dict.fromkeys(_variant_label(v) for v in _variants(annotation))))


def _permitted_values(annotation: Any) -> list[str]:
    values: list[str] = []
    for v in _variants(annotation):
        if get_origin(v.leaf) is Literal:
            values.extend(str(x) for x in get_args(v.leaf))
        elif isinstance(v.leaf, type) and issubclass(v.leaf, Enum):
            values.extend(str(m.value) for m in v.leaf)
        elif v.translated is not None:
            values.extend(sorted(v.translated.en_values))
    return values


def _values_html(values: list[str]) -> str:
    shown = "".join(f"<b>{escape(v)}</b>" for v in values[:MAX_VALUES_SHOWN])
    rest = values[MAX_VALUES_SHOWN:]
    if rest:
        more = "".join(f"<b>{escape(v)}</b>" for v in rest)
        shown += f"<details><summary>{len(rest)} more</summary>{more}</details>"
    return f'<div class="vals">{shown}</div>'


def _notes(field: FieldInfo) -> str:
    notes = [f"{k}: {v}" for k, v in _constraints(field.metadata)]
    variants = _variants(field.annotation)
    for v in variants:
        prefix = f"{_variant_label(v)} " if len(variants) > 1 else ""
        notes += [f"{prefix}{k}: {val}" for k, val in v.constraints]
    return escape("; ".join(dict.fromkeys(notes)))


def _is_list(annotation: Any) -> bool:
    return any(v.container == "ARRAY OF" for v in _variants(annotation))


def _path_id(path: str) -> str:
    return "f-" + path.replace("[]", "").replace(".", "-")


def _model_table(model: type[BaseModel], path: str, ancestors: tuple[type[BaseModel], ...]) -> str:
    rows = "".join(_row(n, f, f"{path}.{n}" if path else n, (*ancestors, model)) for n, f in model.model_fields.items())
    return (
        "<table><thead><tr><th>Field and description</th><th>Attributes</th><th>Type</th>"
        f"<th>Permitted values</th><th>Notes</th></tr></thead><tbody>{rows}</tbody></table>"
    )


def _row(name: str, field: FieldInfo, path: str, ancestors: tuple[type[BaseModel], ...]) -> str:
    """One field row, followed by an expandable sub-table for each nested model the field can hold."""
    attr = "Required" if field.is_required() else "Optional"
    cls = "pill req" if field.is_required() else "pill"
    suffix = "[]" if _is_list(field.annotation) else ""
    path_label = escape(path.replace(".", " › ") + suffix)
    row = (
        f'<tr id="{_path_id(path)}" data-attr="{attr}"><td class="field"><b>{escape(name)}</b>'
        f"<code>{path_label}</code><span>{escape(field.description or '')}</span></td>"
        f'<td><span class="{cls}">{attr}</span></td>'
        f"<td>{_type_label(field.annotation)}</td>"
        f"<td>{_values_html(_permitted_values(field.annotation))}</td>"
        f"<td>{_notes(field)}</td></tr>"
    )
    for nested in dict.fromkeys(_nested_models(field.annotation)):
        child_path = path + suffix
        if nested in ancestors:
            body = f'<p class="desc">↩ recursive reference to {nested.__name__}</p>'
        else:
            body = _model_table(nested, child_path, ancestors)
        row += (
            f'<tr><td class="child" colspan="5"><details id="{_path_id(child_path)}-{nested.__name__}"{" open" if len(ancestors) == 1 else ""}>'
            f"<summary>{nested.__name__} · {len(nested.model_fields)} fields</summary>{body}</details></td></tr>"
        )
    return row


def _nav_tree(model: type[BaseModel], path: str, ancestors: tuple[type[BaseModel], ...]) -> str:
    """Sidebar tree: each field holding nested models lists those models (and their own nested fields) beneath it."""
    ancestors = (*ancestors, model)
    out = []
    for name, field in model.model_fields.items():
        nested = [n for n in dict.fromkeys(_nested_models(field.annotation)) if n not in ancestors]
        if not nested:
            continue
        field_path = f"{path}.{name}" if path else name
        child_path = field_path + ("[]" if _is_list(field.annotation) else "")
        items = []
        for n in nested:
            link = f'<a href="#{_path_id(child_path)}-{n.__name__}">{n.__name__}</a>'
            inner = _nav_tree(n, child_path, ancestors)
            items.append(
                f"<details><summary>{link}</summary><div>{inner}</div></details>" if inner else f"<div>{link}</div>"
            )
        link = f'<a href="#{_path_id(field_path)}">{escape(name)}</a>'
        out.append(f"<details><summary>{link}</summary><div>{''.join(items)}</div></details>")
    return "".join(out)


def _count_fields(model: type[BaseModel]) -> int:
    seen: set[type[BaseModel]] = set()
    stack = [model]
    while stack:
        m = stack.pop()
        if m not in seen:
            seen.add(m)
            stack.extend(n for f in m.model_fields.values() for n in _nested_models(f.annotation))
    return len(seen)


def model_to_dictionary_html(root: type[BaseModel]) -> str:
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{root.__name__} data dictionary</title><style>{CSS}</style></head><body>"
        f"<nav><b>{root.__name__}</b>{_nav_tree(root, '', ())}</nav><main>"
        f"<h1>Data dictionary: {root.__name__}</h1>{INTRO}"
        f"<div class='toolbar'><span>{len(root.model_fields)} top-level fields, "
        f"{_count_fields(root) - 1} nested models</span>"
        "<select id='attr'><option value=''>Attributes: all</option>"
        "<option>Required</option><option>Optional</option></select>"
        "<button id='reset'>Reset</button><button id='expand'>Expand all</button>"
        "<button id='collapse'>Collapse all</button></div>"
        f"{_model_table(root, '', ())}<script>{JS}</script></main></body></html>"
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
