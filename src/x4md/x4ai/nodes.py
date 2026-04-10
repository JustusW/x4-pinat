"""AI-script building blocks."""

from __future__ import annotations

from x4md.expressions import ExprLike
from x4md.md.common import normalize_attrs
from x4md.md.types import ActionNode, ConditionNode, ParamNode

from .types import AINode, InterruptNode, OrderChildNode


class Order(OrderChildNode):
    def __init__(
        self,
        id: str,
        *children: OrderChildNode,
        name: str | None = None,
        description: str | None = None,
        category: str | None = None,
        infinite: bool | None = None,
        allowinloop: bool | None = None,
        canplayercancel: bool | None = None,
    ) -> None:
        super().__init__(
            tag="order",
            attrs=normalize_attrs(
                {
                    "id": id,
                    "name": name,
                    "description": description,
                    "category": category,
                    "infinite": infinite,
                    "allowinloop": allowinloop,
                    "canplayercancel": canplayercancel,
                }
            ),
            children=list(children),
        )


class Requires(OrderChildNode):
    def __init__(self, *children: AINode | ConditionNode) -> None:
        super().__init__(tag="requires", children=list(children))


class Interrupts(OrderChildNode):
    def __init__(self, *children: InterruptNode) -> None:
        super().__init__(tag="interrupts", children=list(children))


class Handler(InterruptNode):
    def __init__(
        self,
        *children: AINode | ConditionNode | ActionNode,
        ref: str | None = None,
        comment: str | None = None,
    ) -> None:
        super().__init__(
            tag="handler",
            attrs=normalize_attrs({"ref": ref, "comment": comment}),
            children=list(children),
        )


class Wait(OrderChildNode):
    def __init__(
        self,
        *children: AINode | ConditionNode,
        exact: ExprLike | None = None,
        min: ExprLike | None = None,
        max: ExprLike | None = None,
        comment: str | None = None,
    ) -> None:
        super().__init__(
            tag="wait",
            attrs=normalize_attrs({"exact": exact, "min": min, "max": max, "comment": comment}),
            children=list(children),
        )


class Resume(OrderChildNode):
    def __init__(self, label: str | None = None) -> None:
        super().__init__(tag="resume", attrs=normalize_attrs({"label": label}))


class CreateOrder(OrderChildNode):
    def __init__(
        self,
        object: ExprLike,
        id: ExprLike,
        *children: ParamNode,
        immediate: bool | None = None,
    ) -> None:
        super().__init__(
            tag="create_order",
            attrs=normalize_attrs({"object": object, "id": id, "immediate": immediate}),
            children=list(children),
        )


class Label(OrderChildNode):
    def __init__(self, name: str) -> None:
        super().__init__(tag="label", attrs=normalize_attrs({"name": name}))


class Goto(OrderChildNode):
    def __init__(self, label: str) -> None:
        super().__init__(tag="goto", attrs=normalize_attrs({"label": label}))
