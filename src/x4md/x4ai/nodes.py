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

    Maps to X4 AI <set_order_syncpoint_reached> element.

    Args:
        value: Syncpoint value

    Example:
        SetOrderSyncpointReached(value="true")
    """

    def __init__(self, *, value: ExprLike) -> None:
        super().__init__(
            tag="set_order_syncpoint_reached",
            attrs=normalize_attrs({"value": value}),
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
