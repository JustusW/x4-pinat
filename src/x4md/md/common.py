"""Shared MD helpers."""

from __future__ import annotations

from typing import Mapping

from x4md.expressions import Expr, render_expr


def normalize_attrs(attrs: Mapping[str, object | None]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for name, value in attrs.items():
        if value is None:
            continue
        key = name.replace("__", ":").rstrip("_")
        if isinstance(value, Expr):
            normalized[key] = value
        elif isinstance(value, (str, int, float, bool)):
            normalized[key] = render_expr(value)
        else:
            normalized[key] = value
    return normalized
