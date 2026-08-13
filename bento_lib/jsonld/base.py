from __future__ import annotations

from abc import ABC, abstractmethod
from typing import overload

from structlog.stdlib import BoundLogger

from .utils import first_if_only_else_all

__all__ = ["JsonLd", "ToJsonLd"]


@overload
def _rec_render_json_ld(v: ToJsonLd | None, namespaces: frozenset[str], logger: BoundLogger) -> dict | None: ...


@overload
def _rec_render_json_ld(v: JsonLd | None, namespaces: frozenset[str], logger: BoundLogger) -> dict | None: ...


@overload
def _rec_render_json_ld(v: dict | None, namespaces: frozenset[str], logger: BoundLogger) -> dict | None: ...


@overload
def _rec_render_json_ld(v: list | None, namespaces: frozenset[str], logger: BoundLogger) -> list | None: ...


@overload
def _rec_render_json_ld(v: str | None, namespaces: frozenset[str], logger: BoundLogger) -> str | None: ...


def _rec_render_json_ld(
    v: ToJsonLd | JsonLd | dict | list | str | None, namespaces: frozenset[str], logger: BoundLogger
) -> dict | list | str | None:
    if isinstance(v, list):
        res = [vvv for vvv in (_rec_render_json_ld(vv, namespaces, logger) for vv in v) if vvv is not None]
        if not res:
            return None  # normalize [] --> None
        return first_if_only_else_all(res)
    if isinstance(v, ToJsonLd):
        return _rec_render_json_ld(v.to_json_ld(), namespaces, logger)
    elif isinstance(v, JsonLd):
        norm_dict = v.render(logger, top_level=False, namespaces=namespaces)
        if not norm_dict or all(isinstance(k, str) and k.startswith("@") for k in norm_dict):
            # normalize {} or dicts without any non-meta properties --> None
            return None
        return norm_dict
    elif isinstance(v, dict):
        final_dict = {}

        for kk, vv in v.items():
            vvv = _rec_render_json_ld(vv, namespaces, logger)
            if vvv is None:  # skip any nulled fields to help us write cleaner JsonLd-generating code
                continue
            if kk.startswith("@"):
                # TODO: validate prefix on types
                final_dict[kk] = vvv
            elif any(kk.startswith(f"{ns}:") for ns in namespaces):
                final_dict[kk] = vvv
            else:
                logger.debug("skipping JSON-LD key (excluded from namespace): %s", kk)
        return final_dict or None
    else:  # str or dict or None
        return v


class JsonLd:
    def __init__(self, json_ld_type: str | list[str], props: dict):
        self.json_ld_types = [json_ld_type] if isinstance(json_ld_type, str) else json_ld_type
        self.props = props

    # noinspection HttpUrlsUsage
    def render(self, logger: BoundLogger, top_level: bool, namespaces: frozenset[str] = frozenset(("schema",))) -> dict:
        final = _rec_render_json_ld(self.props, namespaces, logger) or {}
        final_type = first_if_only_else_all(
            [t for t in self.json_ld_types if any(t.startswith(f"{ns}:") for ns in namespaces)]
        )
        if not final_type:
            raise ValueError("No @type left after namespace pruning")
        final["@type"] = final_type
        if top_level:
            final["@context"] = {
                "dcat": "http://www.w3.org/ns/dcat#",
                "dcterms": "http://purl.org/dc/terms/",
                "schema": "https://schema.org/",
            }
        return final


class ToJsonLd(ABC):
    """
    Mixin implementing the `to_json_ld` interface, for mapping a Pydantic model to a JsonLd object, which can then be
    reduced to a JSON LD dictionary representation.
    """

    @abstractmethod
    def to_json_ld(self) -> JsonLd | None: ...
