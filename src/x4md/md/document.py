"""Document-level MD nodes."""

from __future__ import annotations

from .common import normalize_attrs
from .types import ActionNode, CueChildNode, MDNode, ParamNode


XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


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
        return '<?xml version="1.0" encoding="utf-8"?>\n' + self.to_xml()

    def __str__(self) -> str:
        return self.to_document()


class Cues(MDNode):
    def __init__(self, *children: CueChildNode) -> None:
        super().__init__(tag="cues", children=list(children))


class Cue(CueChildNode):
    def __init__(
        self,
        name: str,
        *children: CueChildNode,
        ref: str | None = None,
        instantiate: bool | None = None,
        version: int | str | None = None,
        comment: str | None = None,
    ) -> None:
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
    def __init__(
        self,
        name: str,
        *children: MDNode,
        purpose: str | None = None,
        comment: str | None = None,
    ) -> None:
        super().__init__(
            tag="library",
            attrs=normalize_attrs({"name": name, "purpose": purpose, "comment": comment}),
            children=list(children),
        )


class InputParam(ParamNode):
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
