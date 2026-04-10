"""Generic XML tree primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable
from xml.sax.saxutils import escape

from x4md.expressions import Expr


def _render_attribute_value(value: object) -> str:
    if isinstance(value, Expr):
        value = value.source
    elif isinstance(value, bool):
        value = "true" if value else "false"
    return escape(str(value), {'"': "&quot;"})


@dataclass(slots=True)
class XmlElement:
    """Simple XML element that renders itself and its children."""

    tag: str
    attrs: dict[str, object] = field(default_factory=dict)
    children: list["XmlElement"] = field(default_factory=list)
    text: str | None = None

    def __post_init__(self) -> None:
        self.children = list(self.children)

    def add(self, *children: "XmlElement") -> "XmlElement":
        self.children.extend(children)
        return self

    def set(self, **attrs: object) -> "XmlElement":
        self.attrs.update(
            {name.replace("__", ":").rstrip("_"): value for name, value in attrs.items()}
        )
        return self

    def to_xml(self, *, indent: str = "  ", level: int = 0) -> str:
        spacing = indent * level
        attributes = "".join(
            f' {name}="{_render_attribute_value(value)}"'
            for name, value in self.attrs.items()
            if value is not None
        )

        if not self.children and self.text is None:
            return f"{spacing}<{self.tag}{attributes}/>"

        if self.text is not None and self.children:
            raise ValueError(f"{self.tag} cannot render both text and child elements")

        if self.text is not None:
            return f"{spacing}<{self.tag}{attributes}>{escape(self.text)}</{self.tag}>"

        rendered_children = "\n".join(
            child.to_xml(indent=indent, level=level + 1) for child in self.children
        )
        return f"{spacing}<{self.tag}{attributes}>\n{rendered_children}\n{spacing}</{self.tag}>"

    def __str__(self) -> str:
        return self.to_xml()

    @classmethod
    def many(cls, tag: str, items: Iterable["XmlElement"]) -> "XmlElement":
        return cls(tag=tag, children=list(items))
