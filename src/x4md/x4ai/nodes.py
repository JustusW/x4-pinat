"""AI-script building blocks."""

from __future__ import annotations

import warnings

from x4md.expressions import ExprLike
from x4md.md.common import normalize_attrs
from x4md.md.types import ActionNode, ConditionNode, CueChildNode, ParamNode

from .types import AINode, InterruptNode, OrderChildNode


# AI order categories declared by ``aiscripts.xsd``
# (``ordercategorylookup``). In practice, vanilla extensions and mods
# sometimes use additional strings (notably ``"fight"``) that X4
# appears to accept without complaint, so we only *warn* when a value
# is outside the known enum rather than raising. Setting
# ``warnings.simplefilter("error", X4OrderCategoryWarning)`` in strict
# builds will promote the warning to an error.
VALID_ORDER_CATEGORIES: frozenset[str] = frozenset(
    {
        "internal",
        "navigation",
        "combat",
        "trade",
        "mining",
        "coordination",
        "salvage",
    }
)


class X4OrderCategoryWarning(UserWarning):
    """Emitted when an AI ``<order category="...">`` value is outside
    the XSD-declared ``ordercategorylookup`` enum."""


def _contains_syncpoint(nodes: tuple[object, ...]) -> bool:
    """Return ``True`` if any descendant is a ``SetOrderSyncpointReached``."""

    for node in nodes:
        if isinstance(node, SetOrderSyncpointReached):
            return True
        child_nodes = getattr(node, "children", None)
        if child_nodes and _contains_syncpoint(tuple(child_nodes)):
            return True
    return False


class Order(OrderChildNode):
    """Top-level AI order definition.

    Visible `name` and `description` values usually point at t-file entries,
    for example ``TextExpr.ref(77000, 10002)``.

    Args:
        id: Internal order id used when creating the order
        *children: Order child nodes such as interrupts or steps
        name: Visible order label, usually a t-file reference
        description: Visible order description, usually a t-file reference
        category: X4 order category such as ``trade`` or ``fight``
        infinite: Whether the order repeats indefinitely
        allowinloop: Whether the order is allowed inside order loops
        canplayercancel: Whether the player can cancel the order manually

    Raises:
        ValueError: If ``infinite=True`` is set but no
            ``SetOrderSyncpointReached`` action is present in the order
            tree. Without it, X4 logs:
            ``AI order '<id>' is infinite but action
            <set_order_syncpoint_reached> is missing`` and the ship
            enters a zombie loop where no follow-up orders ever apply.
    """

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
        if infinite is True and not _contains_syncpoint(children):
            raise ValueError(
                f"Order {id!r} declares infinite=True but is missing a "
                "SetOrderSyncpointReached action. X4 rejects infinite "
                "orders without a sync point and will spam 'returned but "
                "no new order in the queue' while the ship is stuck."
            )
        if category is not None and category not in VALID_ORDER_CATEGORIES:
            valid = ", ".join(sorted(VALID_ORDER_CATEGORIES))
            warnings.warn(
                (
                    f"Order {id!r} uses category={category!r}, which is "
                    "not in the aiscripts.xsd ordercategorylookup enum "
                    f"({valid}). X4 may accept this at runtime but the "
                    "order will likely be miscategorised in the UI or "
                    "fall back to a default. Common typo: 'fight' vs "
                    "'combat'."
                ),
                X4OrderCategoryWarning,
                stacklevel=2,
            )
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
    """Container for AI preconditions.

    Args:
        *children: AI or condition nodes evaluated before the order runs
    """

    def __init__(self, *children: AINode | ConditionNode) -> None:
        super().__init__(tag="requires", children=list(children))


class Interrupts(OrderChildNode):
    """Container for AI interrupt handlers.

    Args:
        *children: Interrupt handlers for the order
    """

    def __init__(self, *children: InterruptNode) -> None:
        super().__init__(tag="interrupts", children=list(children))


class Handler(InterruptNode):
    """Interrupt handler for AI orders.

    Args:
        *children: Conditions and actions used by the handler
        ref: Optional handler reference
        comment: Optional comment for generated XML
    """

    def __init__(
        self,
        *children: AINode | ConditionNode | ActionNode | CueChildNode,
        ref: str | None = None,
        comment: str | None = None,
    ) -> None:
        """Interrupt handler.

        Note: Accepts CueChildNode to allow Conditions wrapper which extends
        CueChildNode but is used in both MD cues and AI handlers.
        """
        super().__init__(
            tag="handler",
            attrs=normalize_attrs({"ref": ref, "comment": comment}),
            children=list(children),
        )


class Wait(OrderChildNode):
    """Pause execution for a duration or until child conditions resolve.

    Args:
        *children: Optional AI or condition children
        exact: Exact wait duration
        min: Minimum wait duration
        max: Maximum wait duration
        comment: Optional comment for generated XML
    """

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
    """Resume execution at the given label.

    Args:
        label: Label to resume from
    """

    def __init__(self, label: str | None = None) -> None:
        super().__init__(tag="resume", attrs=normalize_attrs({"label": label}))


class CreateOrder(OrderChildNode):
    """Create an AI order on an object.

    Args:
        object: Target object for the created order
        id: Order id expression, commonly ``TextExpr.quote(...)``
        *children: Parameter nodes for the created order
        immediate: Whether the order should start immediately
    """

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
    """Define a jump label inside an AI order.

    Args:
        name: Label name
    """

    def __init__(self, name: str) -> None:
        super().__init__(tag="label", attrs=normalize_attrs({"name": name}))


class Goto(OrderChildNode):
    """Jump to a named label inside an AI order.

    Args:
        label: Label name to jump to
    """

    def __init__(self, label: str) -> None:
        super().__init__(tag="goto", attrs=normalize_attrs({"label": label}))


class AddWareReservation(OrderChildNode):
    """Add ware reservation for trading.

    Maps to X4 AI <add_ware_reservation> element.

    Args:
        object: Object to add reservation to
        ware: Ware to reserve
        amount: Amount to reserve
        type: Reservation type ('buy' or 'sell')
        virtual: Whether this is a virtual reservation

    Example:
        AddWareReservation(
            object="$station",
            ware="energycells",
            amount="100",
            type="buy"
        )
    """

    def __init__(
        self,
        *,
        object: ExprLike,
        ware: ExprLike,
        amount: ExprLike,
        type: str,
        virtual: bool | None = None,
    ) -> None:
        super().__init__(
            tag="add_ware_reservation",
            attrs=normalize_attrs({
                "object": object,
                "ware": ware,
                "amount": amount,
                "type": type,
                "virtual": virtual,
            }),
        )


class RemoveWareReservation(OrderChildNode):
    """Remove ware reservation.

    Maps to X4 AI <remove_ware_reservation> element.

    Args:
        object: Object to remove reservation from
        ware: Ware reservation to remove
        type: Reservation type ('buy' or 'sell')
        virtual: Whether this is a virtual reservation

    Example:
        RemoveWareReservation(
            object="$station",
            ware="energycells",
            type="buy"
        )
    """

    def __init__(
        self,
        *,
        object: ExprLike,
        ware: ExprLike,
        type: str,
        virtual: bool | None = None,
    ) -> None:
        super().__init__(
            tag="remove_ware_reservation",
            attrs=normalize_attrs({
                "object": object,
                "ware": ware,
                "type": type,
                "virtual": virtual,
            }),
        )


class SetOrderFailed(OrderChildNode):
    """Mark current order as failed.

    Maps to X4 AI <set_order_failed> element.

    Args:
        reason: Optional failure reason

    Example:
        SetOrderFailed(reason="'No trade opportunities found'")
    """

    def __init__(self, *, reason: ExprLike | None = None) -> None:
        super().__init__(
            tag="set_order_failed",
            attrs=normalize_attrs({"reason": reason}),
        )


class SetOrderState(OrderChildNode):
    """Set current order state.

    Maps to X4 AI <set_order_state> element.

    Args:
        state: Order state to set

    Example:
        SetOrderState(state="EXECUTING")
    """

    def __init__(self, *, state: str) -> None:
        super().__init__(
            tag="set_order_state",
            attrs=normalize_attrs({"state": state}),
        )


class SetOrderSyncpointReached(OrderChildNode):
    """Mark order synchronization point reached.

    Maps to X4 AI <set_order_syncpoint_reached> element. In vanilla X4
    the element is most often emitted without any attributes, signalling
    that the order's primary sync point has been reached. A named sync
    point can optionally be passed via ``value``.

    Args:
        value: Optional syncpoint value. When omitted, the element is
               emitted with no attributes (the common vanilla form).

    Example:
        SetOrderSyncpointReached()
        SetOrderSyncpointReached(value="true")
    """

    def __init__(self, *, value: ExprLike | None = None) -> None:
        attrs = normalize_attrs({"value": value}) if value is not None else {}
        super().__init__(
            tag="set_order_syncpoint_reached",
            attrs=attrs,
        )


class ClearOrderFailure(OrderChildNode):
    """Clear order failure state.

    Maps to X4 AI <clear_order_failure/> element.

    Example:
        ClearOrderFailure()
    """

    def __init__(self) -> None:
        super().__init__(tag="clear_order_failure")


class RunScript(OrderChildNode):
    """Execute another AI script.

    Maps to X4 AI <run_script> element.

    Args:
        name: Script name to run
        *children: Parameter nodes

    Example:
        RunScript(name="'move.tradeship'", Param(name="station", value="$target"))
    """

    def __init__(self, *children: ParamNode, name: str) -> None:
        super().__init__(
            tag="run_script",
            attrs=normalize_attrs({"name": name}),
            children=list(children),
        )


class Attention(OrderChildNode):
    """Set attention object.

    Maps to X4 AI <attention> element.

    Args:
        object: Object to pay attention to
        min: Minimum attention duration
        max: Maximum attention duration

    Example:
        Attention(object="$target", min="5s", max="10s")
    """

    def __init__(
        self,
        *,
        object: ExprLike,
        min: ExprLike | None = None,
        max: ExprLike | None = None,
    ) -> None:
        super().__init__(
            tag="attention",
            attrs=normalize_attrs({"object": object, "min": min, "max": max}),
        )


class IncludeInterruptActions(OrderChildNode):
    """Include interrupt handler actions.

    Maps to X4 AI <include_interrupt_actions> element.

    Args:
        ref: Reference to interrupt handler

    Example:
        IncludeInterruptActions(ref="TradeAbort")
    """

    def __init__(self, *, ref: str) -> None:
        super().__init__(
            tag="include_interrupt_actions",
            attrs=normalize_attrs({"ref": ref}),
        )


class CreateTradeOrder(OrderChildNode):
    """Create trade-specific order.

    Maps to X4 AI <create_trade_order> element.

    Args:
        object: Ship to create order for
        tradeoffer: Trade offer to execute
        amount: Amount to trade
        type: Trade type ('buy' or 'sell')

    Example:
        CreateTradeOrder(
            object="this.ship",
            tradeoffer="$offer",
            amount="$quantity",
            type="buy"
        )
    """

    def __init__(
        self,
        *,
        object: ExprLike,
        tradeoffer: ExprLike,
        amount: ExprLike,
        type: str,
    ) -> None:
        super().__init__(
            tag="create_trade_order",
            attrs=normalize_attrs({
                "object": object,
                "tradeoffer": tradeoffer,
                "amount": amount,
                "type": type,
            }),
        )


class ClampTradeAmount(OrderChildNode):
    """Clamp trade amount to available capacity.

    Maps to X4 AI <clamp_trade_amount> element.

    Args:
        object: Ship to check capacity
        tradeoffer: Trade offer
        amount: Variable containing amount (will be clamped)

    Example:
        ClampTradeAmount(
            object="this.ship",
            tradeoffer="$offer",
            amount="$quantity"
        )
    """

    def __init__(
        self,
        *,
        object: ExprLike,
        tradeoffer: ExprLike,
        amount: str,
    ) -> None:
        super().__init__(
            tag="clamp_trade_amount",
            attrs=normalize_attrs({
                "object": object,
                "tradeoffer": tradeoffer,
                "amount": amount,
            }),
        )


class CreatePosition(OrderChildNode):
    """Create position object for navigation.

    Maps to X4 AI <create_position> element.

    Args:
        name: Variable to store position
        object: Object to create position from
        space: Space context
        x, y, z: Coordinates
        min, max: Random offset range

    Example:
        CreatePosition(name="$pos", object="$station", min="1km", max="5km")
    """

    def __init__(
        self,
        *,
        name: str,
        object: ExprLike | None = None,
        space: ExprLike | None = None,
        x: ExprLike | None = None,
        y: ExprLike | None = None,
        z: ExprLike | None = None,
        min: ExprLike | None = None,
        max: ExprLike | None = None,
    ) -> None:
        super().__init__(
            tag="create_position",
            attrs=normalize_attrs({
                "name": name,
                "object": object,
                "space": space,
                "x": x,
                "y": y,
                "z": z,
                "min": min,
                "max": max,
            }),
        )


class GetJumpPath(OrderChildNode):
    """Calculate jump path between sectors.

    Maps to X4 AI <get_jump_path> element.

    Args:
        result: Variable to store path
        start: Start sector/object
        end: End sector/object

    Example:
        GetJumpPath(result="$path", start="this.sector", end="$targetSector")
    """

    def __init__(self, *, result: str, start: ExprLike, end: ExprLike) -> None:
        super().__init__(
            tag="get_jump_path",
            attrs=normalize_attrs({"result": result, "start": start, "end": end}),
        )


class SetCommand(OrderChildNode):
    """Set command interface for object.

    Maps to X4 AI <set_command> element.

    Args:
        command: Command to set

    Example:
        SetCommand(command="command.trade")
    """

    def __init__(self, *, command: ExprLike) -> None:
        super().__init__(
            tag="set_command",
            attrs=normalize_attrs({"command": command}),
        )


class SetCommandAction(OrderChildNode):
    """Set command action.

    Maps to X4 AI <set_command_action> element.

    Args:
        commandaction: Action to set

    Example:
        SetCommandAction(commandaction="commandaction.searchingtrades")
    """

    def __init__(self, *, commandaction: ExprLike) -> None:
        super().__init__(
            tag="set_command_action",
            attrs=normalize_attrs({"commandaction": commandaction}),
        )
