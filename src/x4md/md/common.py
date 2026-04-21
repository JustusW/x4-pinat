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


def validate_md_lvalue(path: object, *, action: str) -> None:
    """Raise ``ValueError`` if ``path`` would silently fail as an MD l-value.

    Actions like ``set_value``, ``remove_value``, ``append_to_list``, and
    ``sort_list`` mutate the location named by their ``name``/``list``
    attribute. In X4 MD, table keys that live under a ``$variable`` must
    themselves be ``$``-prefixed (or accessed dynamically via
    ``.{expr}``). A bareword segment following a ``$var`` is a *property*
    lookup (e.g. ``.count``, ``.keys``) and is read-only.

    If the generator emits something like ``global.$gp.encounters`` as
    the target of a ``set_value``, X4 silently rejects the write with::

        Error in MD cue ...: Failed to set table[].encounters to value ...
        * Expression: global.$gp.encounters

    and the rest of the script carries on with an empty table, which is
    the hardest possible bug to diagnose from the mod's own logging.

    The correct form is ``global.$gp.$encounters`` (vanilla X4 uses this
    convention, e.g. ``global.$FactionLogic.$faction.$ships``). This
    function enforces that convention at emit time so a typo in a path
    surfaces as a ``ValueError`` instead of a silent in-game failure.

    Args:
        path: The l-value path. Non-string values (``Expr`` instances,
            ``PathExpr``, etc.) are assumed pre-validated and pass through.
        action: Name of the calling action, used in the error message.

    Raises:
        ValueError: If ``path`` contains a bareword segment after a
            ``$``-prefixed owner.
    """

    if not isinstance(path, str):
        return
    if "$" not in path:
        return

    segments: list[str] = []
    i = 0
    length = len(path)
    while i < length:
        c = path[i]
        if c == ".":
            i += 1
            continue
        if c == "{":
            depth = 1
            j = i + 1
            while j < length and depth > 0:
                if path[j] == "{":
                    depth += 1
                elif path[j] == "}":
                    depth -= 1
                j += 1
            if depth != 0:
                return
            segments.append(path[i:j])
            i = j
            continue
        j = i
        while j < length and path[j] not in ".{":
            j += 1
        segments.append(path[i:j])
        i = j

    seen_dollar = False
    for seg in segments:
        if seg.startswith("$"):
            seen_dollar = True
            continue
        if seg.startswith("{"):
            seen_dollar = True
            continue
        if seen_dollar:
            raise ValueError(
                f"{action} target path {path!r} writes to bareword segment "
                f"{seg!r} after a $-prefixed owner. X4 MD treats that as a "
                f"read-only property lookup and silently refuses the write "
                f"(look for 'Failed to set table[].{seg} to value ...' in "
                f"the X4 debuglog). Table keys must be $-prefixed, e.g. "
                f"use '${seg}' or '.{{expr}}' instead."
            )
