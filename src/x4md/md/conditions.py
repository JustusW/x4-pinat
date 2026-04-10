"""Condition and event nodes for MD."""

from __future__ import annotations

from x4md.expressions import ExprLike

from .common import normalize_attrs
from .types import ConditionNode


class Conditions(ConditionNode):
    def __init__(self, *children: ConditionNode) -> None:
        super().__init__(tag="conditions", children=list(children))


class CheckAny(ConditionNode):
    def __init__(self, *children: ConditionNode) -> None:
        super().__init__(tag="check_any", children=list(children))


class CheckValue(ConditionNode):
    def __init__(self, value: ExprLike) -> None:
        super().__init__(tag="check_value", attrs=normalize_attrs({"value": value}))


class EventGameLoaded(ConditionNode):
    def __init__(self) -> None:
        super().__init__(tag="event_game_loaded")


class EventPlayerCreated(ConditionNode):
    def __init__(self) -> None:
        super().__init__(tag="event_player_created")


class EventCueSignalled(ConditionNode):
    def __init__(self) -> None:
        super().__init__(tag="event_cue_signalled")


class EventObjectSignalled(ConditionNode):
    def __init__(self, object: ExprLike, *, param: ExprLike | None = None) -> None:
        super().__init__(
            tag="event_object_signalled",
            attrs=normalize_attrs({"object": object, "param": param}),
        )
