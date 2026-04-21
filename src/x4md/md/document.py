"""Document-level MD nodes."""

from __future__ import annotations

import re

from .common import normalize_attrs
from .types import ActionNode, CueChildNode, MDNode, ParamNode


XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

# X4 Mission Director rejects any cue or library whose name contains a
# ``.`` character with errors like:
#   [=ERROR=] Cue name contains contains invalid '.' character: '<name>'
# The engine's identifier rule is the standard XML NCName-ish form: a
# leading letter or underscore followed by letters, digits, or
# underscores. Dashes, dots, colons, and spaces all blow up at load
# time, so we refuse them up-front instead of silently emitting broken
# extensions.
_MD_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_md_identifier(kind: str, name: object) -> None:
    """Raise ``ValueError`` when ``name`` is not a valid MD identifier.

    ``kind`` is used only to produce a clearer error message (e.g.
    ``"cue"`` or ``"library"``).
    """

    if not isinstance(name, str) or not _MD_IDENTIFIER_RE.fullmatch(name):
        raise ValueError(
            f"Invalid MD {kind} name {name!r}: must match "
            f"[A-Za-z_][A-Za-z0-9_]* (no dots, dashes, or spaces)."
        )


def _contains_return(nodes: tuple[object, ...]) -> bool:
    """Return ``True`` if any descendant emits a ``<return>`` element.

    The traversal deliberately stops at nested ``<library>`` boundaries
    because ``<return>`` is legal inside libraries; callers should only
    ever pass the direct children of a ``Cue``. We identify ``<return>``
    nodes by their XML ``tag`` attribute rather than the Python type,
    because :class:`x4md.md.actions.Return` would introduce a circular
    import here.
    """

    for node in nodes:
        if getattr(node, "tag", None) == "library":
            continue
        if getattr(node, "tag", None) == "return":
            return True
        child_nodes = getattr(node, "children", None)
        if child_nodes and _contains_return(tuple(child_nodes)):
            return True
    return False


class MDScript(MDNode):
    """Root node for an X4 Mission Director document."""

    def __init__(self, name: str = "ScriptName", cues: "Cues | None" = None) -> None:
        super().__init__(
            tag="mdscript",
            attrs={
                "name": name,
                "xmlns:xsi": XSI_NS,
                "xsi:noNamespaceSchemaLocation": "md.xsd",
            },
            children=[cues or Cues()],
        )

    def to_document(self) -> str:
        """Render the full MD document including the XML declaration."""

        return '<?xml version="1.0" encoding="utf-8"?>\n' + self.to_xml()

    def __str__(self) -> str:
        return self.to_document()


class Cues(MDNode):
    """Container for top-level cue and library nodes.

    Args:
        *children: Cue-level children to place under ``<cues>``
    """

    def __init__(self, *children: CueChildNode) -> None:
        super().__init__(tag="cues", children=list(children))


class Cue(CueChildNode):
    """Mission Director cue definition.

    Args:
        name: Cue name
        *children: Cue child nodes such as conditions and actions
        ref: Optional cue reference
        instantiate: Whether X4 should instantiate the cue immediately
        version: Optional cue version
        comment: Optional comment for generated XML
    """

    def __init__(
        self,
        name: str,
        *children: CueChildNode,
        ref: str | None = None,
        instantiate: bool | None = None,
        version: int | str | None = None,
        comment: str | None = None,
    ) -> None:
        _validate_md_identifier("cue", name)
        # X4 only permits <return> inside library actions. In a cue it
        # produces "Script node 'return' is not allowed in this
        # context." and the engine then refuses to run the cue at all,
        # which is extremely hard to diagnose because the cue simply
        # stops firing. Fail fast in Python instead.
        if _contains_return(children):
            raise ValueError(
                f"Cue {name!r} contains a <return> action. <return> is "
                "only valid inside <library> actions; in cue actions "
                "use an inverted DoIf guard to skip the rest of the "
                "body instead of returning early."
            )
        super().__init__(
            tag="cue",
            attrs=normalize_attrs(
                {
                    "name": name,
                    "ref": ref,
                    "instantiate": instantiate,
                    "version": version,
                    "comment": comment,
                }
            ),
            children=list(children),
        )


class Library(CueChildNode):
    """Reusable Mission Director library block.

    Args:
        name: Library name
        *children: Library child nodes
        purpose: Optional X4 purpose value
        comment: Optional comment for generated XML
    """

    def __init__(
        self,
        name: str,
        *children: MDNode,
        purpose: str | None = None,
        comment: str | None = None,
    ) -> None:
        _validate_md_identifier("library", name)
        super().__init__(
            tag="library",
            attrs=normalize_attrs({"name": name, "purpose": purpose, "comment": comment}),
            children=list(children),
        )


class InputParam(ParamNode):
    """Input parameter node for library calls.

    Args:
        name: Parameter name
        value: Parameter value expression
    """

    def __init__(self, name: str, value: object) -> None:
        super().__init__(
            tag="input_param",
            attrs=normalize_attrs({"name": name, "value": value}),
        )


class OnAbort(CueChildNode):
    """Actions to execute when a cue is aborted.

    Maps to X4 MD <on_abort> element. Used within cues to define cleanup
    or error handling actions that run when the cue is cancelled.

    Args:
        *children: Action nodes to execute on abort

    Example:
        Cue(
            "TradingCue",
            Conditions(...),
            Actions(...),
            OnAbort(
                DebugText("Trading cue was aborted"),
                SetValue(name="$trading", exact=False)
            )
        )
    """

    def __init__(self, *children: ActionNode) -> None:
        super().__init__(tag="on_abort", children=list(children))


class Delay(CueChildNode):
    """Add delay before cue activation.

    Maps to X4 MD <delay> cue child element.

    Args:
        exact: Exact delay duration
        min: Minimum delay
        max: Maximum delay

    Example:
        Delay(exact="5s")
        Delay(min="1s", max="10s")
    """

    def __init__(
        self,
        *,
        exact: ExprLike | None = None,
        min: ExprLike | None = None,
        max: ExprLike | None = None,
    ) -> None:
        from .common import normalize_attrs
        super().__init__(
            tag="delay",
            attrs=normalize_attrs({"exact": exact, "min": min, "max": max}),
        )
