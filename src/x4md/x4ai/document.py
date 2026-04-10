"""AI-script document root."""

from __future__ import annotations

from .types import AINode, OrderChildNode


XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


class AIScript(AINode):
    """Root node for an X4 AI script."""

    def __init__(
        self,
        name: str,
        *children: OrderChildNode,
        version: int | str = 1,
        schema_location: str = "aiscripts.xsd",
    ) -> None:
        super().__init__(
            tag="aiscript",
            attrs={
                "name": name,
                "xmlns:xsi": XSI_NS,
                "xsi:noNamespaceSchemaLocation": schema_location,
                "version": version,
            },
            children=list(children),
        )

    def to_document(self) -> str:
        return '<?xml version="1.0" encoding="utf-8"?>\n' + self.to_xml()

    def __str__(self) -> str:
        return self.to_document()
