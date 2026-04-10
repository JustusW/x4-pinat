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


class CheckAll(ConditionNode):
    """Conjunction of multiple conditions (all must be true).

    Maps to X4 MD <check_all> element.

    Args:
        *children: Condition nodes that must all be true

    Example:
        CheckAll(
            CheckValue("$ready"),
            CheckValue("$count gt 0"),
        )
    """

    def __init__(self, *children: ConditionNode) -> None:
        super().__init__(tag="check_all", children=list(children))


class EventObjectOrderReady(ConditionNode):
    """Event triggered when an object's order becomes ready.

    Maps to X4 MD <event_object_order_ready> element.

    Args:
        object: Object to monitor for order ready state
        comment: Optional comment

    Example:
        EventObjectOrderReady(object="player.galaxy")
    """

    def __init__(self, *, object: ExprLike, comment: str | None = None) -> None:
        super().__init__(
            tag="event_object_order_ready",
            attrs=normalize_attrs({"object": object, "comment": comment}),
        )


class EventObjectDestroyed(ConditionNode):
    """Event triggered when an object is destroyed.

    Maps to X4 MD <event_object_destroyed> element.

    Args:
        object: Object to monitor for destruction

    Example:
        EventObjectDestroyed(object="$targetShip")
    """

    def __init__(self, *, object: ExprLike) -> None:
        super().__init__(
            tag="event_object_destroyed",
            attrs=normalize_attrs({"object": object}),
        )


class EventGameSaved(ConditionNode):
    """Event triggered when the game is saved.

    Maps to X4 MD <event_game_saved/> element.

    Example:
        EventGameSaved()
    """

    def __init__(self) -> None:
        super().__init__(tag="event_game_saved")


class EventPlayerAssignedHiredActor(ConditionNode):
    """Event triggered when player assigns a hired crew member.

    Maps to X4 MD <event_player_assigned_hired_actor/> element.

    Example:
        EventPlayerAssignedHiredActor()
    """

    def __init__(self) -> None:
        super().__init__(tag="event_player_assigned_hired_actor")


class EventObjectChangedZone(ConditionNode):
    """Event triggered when an object changes zones.

    Maps to X4 MD <event_object_changed_zone> element.

    Args:
        object: Object to monitor for zone changes

    Example:
        EventObjectChangedZone(object="$ship")
    """

    def __init__(self, *, object: ExprLike) -> None:
        super().__init__(
            tag="event_object_changed_zone",
            attrs=normalize_attrs({"object": object}),
        )


class EventUITriggered(ConditionNode):
    """Event triggered by UI interaction.

    Maps to X4 MD <event_ui_triggered> element.

    Args:
        screen: Screen identifier
        control: Control identifier

    Example:
        EventUITriggered(screen="MapMenu", control="confirm_button")
    """

    def __init__(self, *, screen: str, control: str) -> None:
        super().__init__(
            tag="event_ui_triggered",
            attrs=normalize_attrs({"screen": screen, "control": control}),
        )


class MatchBuyer(ConditionNode):
    """Match buyer criteria for trade offers.

    Maps to X4 MD <match_buyer> element. Used as child of FindBuyOffer
    to filter results by buyer characteristics.

    Args:
        tradepartner: Trade partner to match
        space: Space to search in
        sector: Specific sector to match
        friend: Filter by friendly status
        neutral: Filter by neutral status
        enemy: Filter by enemy status

    Example:
        FindBuyOffer(
            space="$sector",
            wares="[$energycells]",
            MatchBuyer(friend=True)
        )
    """

    def __init__(
        self,
        *,
        tradepartner: ExprLike | None = None,
        space: ExprLike | None = None,
        sector: ExprLike | None = None,
        friend: bool | None = None,
        neutral: bool | None = None,
        enemy: bool | None = None,
    ) -> None:
        super().__init__(
            tag="match_buyer",
            attrs=normalize_attrs(
                {
                    "tradepartner": tradepartner,
                    "space": space,
                    "sector": sector,
                    "friend": friend,
                    "neutral": neutral,
                    "enemy": enemy,
                }
            ),
        )


class MatchSeller(ConditionNode):
    """Match seller criteria for trade offers.

    Maps to X4 MD <match_seller> element. Used as child of FindSellOffer
    to filter results by seller characteristics.

    Args:
        tradepartner: Trade partner to match
        space: Space to search in
        sector: Specific sector to match
        friend: Filter by friendly status
        neutral: Filter by neutral status
        enemy: Filter by enemy status

    Example:
        FindSellOffer(
            space="$sector",
            wares="[$ore]",
            MatchSeller(friend=True, space="$currentzone")
        )
    """

    def __init__(
        self,
        *,
        tradepartner: ExprLike | None = None,
        space: ExprLike | None = None,
        sector: ExprLike | None = None,
        friend: bool | None = None,
        neutral: bool | None = None,
        enemy: bool | None = None,
    ) -> None:
        super().__init__(
            tag="match_seller",
            attrs=normalize_attrs(
                {
                    "tradepartner": tradepartner,
                    "space": space,
                    "sector": sector,
                    "friend": friend,
                    "neutral": neutral,
                    "enemy": enemy,
                }
            ),
        )


class MatchGateDistance(ConditionNode):
    """Match objects by gate jump distance.

    Maps to X4 MD <match_gate_distance> element. Used as child of Find
    actions to filter results by distance in gate jumps.

    Args:
        object: Reference object to measure from
        min: Minimum gate distance (inclusive)
        max: Maximum gate distance (inclusive)

    Example:
        FindStation(
            space="player.galaxy",
            MatchGateDistance(object="player.ship", max=3)
        )
    """

    def __init__(
        self,
        *,
        object: ExprLike,
        min: ExprLike | None = None,
        max: ExprLike | None = None,
    ) -> None:
        super().__init__(
            tag="match_gate_distance",
            attrs=normalize_attrs({"object": object, "min": min, "max": max}),
        )
