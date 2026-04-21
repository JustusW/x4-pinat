"""AI-script document root."""

from __future__ import annotations

from x4md.md.actions import Actions
from x4md.md.types import ActionNode

from .types import AINode, OrderChildNode


XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"


# Tags that the ``aiscripts.xsd`` schema allows *inside* an
# ``<order>`` element (see the ``orderdef`` complexType). Every other
# element the caller passes as an Order child is an AI action and must
# be hoisted out as a sibling of ``<order>`` under ``<aiscript>``.
_ORDER_META_TAGS: frozenset[str] = frozenset(
    {"params", "skill", "requires", "location", "icon"}
)

# Tags that become their own sibling of ``<order>`` under
# ``<aiscript>``. These map directly to the sequence the schema
# declares for the ``aiscript`` element: ``order``, ``interrupts``,
# ``init``, ``actions``, ``attention*``, ``on_abort``.
_AISCRIPT_SIBLING_TAGS: frozenset[str] = frozenset(
    {"interrupts", "init", "attention", "on_abort"}
)


class AIScript(AINode):
    """Root node for an X4 AI script.

    The ``aiscripts.xsd`` sequence for an ``<aiscript>`` is::

        documentation?, (order | params)?, interrupts?, init?,
        patch*, patches*, actions?, attention*, on_abort?, signature?

    In particular, ``<interrupts>``, ``<actions>``, and ``<attention>``
    are **siblings** of ``<order>``, not children. The ergonomic Python
    API lets the caller nest everything under ``Order(...)`` for
    readability; this class rewrites that tree at construction time so
    the rendered XML matches the schema. Emitting the Python layout
    verbatim causes X4 to log ``AI order '<id>' is infinite but action
    <set_order_syncpoint_reached> is missing ... attention level
    'unknown'`` and the ship enters a zombie poll loop, because the
    runtime analyzer only looks inside a real top-level ``<actions>``
    section.
    """

    def __init__(
        self,
        name: str,
        *children: OrderChildNode | ActionNode,
        version: int | str = 1,
        schema_location: str = "aiscripts.xsd",
    ) -> None:
        rewritten = self._rewrite_children(children)
        super().__init__(
            tag="aiscript",
            attrs={
                "name": name,
                "xmlns:xsi": XSI_NS,
                "xsi:noNamespaceSchemaLocation": schema_location,
                "version": version,
            },
            children=rewritten,
        )

    @staticmethod
    def _rewrite_children(
        children: tuple[OrderChildNode, ...],
    ) -> list[object]:
        """Split each ``Order`` child into the shape ``aiscripts.xsd`` expects.

        - ``params`` / ``skill`` / ``requires`` / ``location`` / ``icon``
          stay inside the ``<order>`` element.
        - ``<interrupts>``, ``<init>``, ``<attention>``, ``<on_abort>``
          become siblings of ``<order>`` under ``<aiscript>``.
        - Everything else is treated as a loose AI action and collected
          into one sibling ``<actions>`` wrapper. Without this step the
          ``<set_order_syncpoint_reached>`` validator at runtime refuses
          to find the sync point and the order thrashes.

        Siblings are emitted in the order required by the XSD sequence
        (``interrupts -> init -> actions -> attention* -> on_abort``) so
        a well-formed input produces a schema-valid output regardless of
        the Python argument order.
        """

        rewritten: list[object] = []
        for child in children:
            if getattr(child, "tag", None) != "order":
                rewritten.append(child)
                continue

            order_meta: list[object] = []
            interrupts_node: object | None = None
            init_node: object | None = None
            on_abort_node: object | None = None
            attention_nodes: list[object] = []
            loose_actions: list[object] = []

            for sub in list(getattr(child, "children", [])):
                tag = getattr(sub, "tag", None)
                if tag in _ORDER_META_TAGS:
                    order_meta.append(sub)
                elif tag == "interrupts":
                    interrupts_node = sub
                elif tag == "init":
                    init_node = sub
                elif tag == "attention":
                    attention_nodes.append(sub)
                elif tag == "on_abort":
                    on_abort_node = sub
                else:
                    loose_actions.append(sub)

            # Rebuild the Order element with only its meta children.
            # Mutating the existing node keeps its attributes (id,
            # name, description, category, infinite, canplayercancel).
            child.children = order_meta  # type: ignore[attr-defined]
            rewritten.append(child)

            if interrupts_node is not None:
                rewritten.append(interrupts_node)
            if init_node is not None:
                rewritten.append(init_node)
            if loose_actions:
                rewritten.append(Actions(*loose_actions))
            rewritten.extend(attention_nodes)
            if on_abort_node is not None:
                rewritten.append(on_abort_node)
        return rewritten

    def to_document(self) -> str:
        return '<?xml version="1.0" encoding="utf-8"?>\n' + self.to_xml()

    def __str__(self) -> str:
        return self.to_document()
