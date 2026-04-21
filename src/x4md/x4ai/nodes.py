"""AI-script building blocks."""

from __future__ import annotations

import warnings

from x4md.expressions import Expr, ExprLike
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

    Maps to the X4 AI ``<handler>`` element used inside
    ``<interrupts>``. The schema's ``interrupts``-context ``<handler>``
    only permits two children: ``<conditions>`` and ``<actions>``.

    For convenience, callers can pass loose action nodes directly -
    this class hoists them into a single ``<actions>`` child, the same
    rewrite ``AIScript`` applies to loose order children. Passing an
    explicit ``Actions(...)`` child is always accepted unchanged; a
    ``Conditions(...)`` child is always passed through.

    Args:
        *children: A mix of ``Conditions``, ``Actions``, and/or loose
            action nodes. Loose actions are wrapped into a single
            ``<actions>`` child to match aiscripts.xsd.
        ref: Optional handler reference.
        comment: Optional comment for generated XML.
        consume: If set, X4 marks the event consumed after the handler
            fires (XSD ``boolean``). Defaults to schema default.
    """

    def __init__(
        self,
        *children: AINode | ConditionNode | ActionNode | CueChildNode,
        ref: str | None = None,
        comment: str | None = None,
        consume: bool | None = None,
    ) -> None:
        rewritten = Handler._rewrite_children(children)
        super().__init__(
            tag="handler",
            attrs=normalize_attrs(
                {"ref": ref, "comment": comment, "consume": consume}
            ),
            children=rewritten,
        )

    @staticmethod
    def _rewrite_children(
        children: tuple[object, ...],
    ) -> list[object]:
        """Group loose actions into a single ``<actions>`` wrapper.

        ``<handler>`` in the ``interrupts`` schema only accepts
        ``<conditions>`` and ``<actions>`` children. Emitting loose
        actions (e.g. ``<resume>``, ``<clear_order_failure>``) directly
        produces "Unexpected child ... at position N" schema errors
        and, worse, X4 silently drops the handler at runtime. This
        rewrite makes the common caller pattern (pass Conditions
        followed by loose actions) produce valid XML.
        """

        # Import locally to avoid a circular import with x4md.md.actions.
        from x4md.md.actions import Actions as _Actions

        meta: list[object] = []
        actions_wrapper: object | None = None
        loose_actions: list[object] = []

        for child in children:
            tag = getattr(child, "tag", None)
            if tag == "conditions":
                meta.append(child)
            elif isinstance(child, _Actions):
                actions_wrapper = child
            else:
                loose_actions.append(child)

        if loose_actions and actions_wrapper is not None:
            # Caller supplied both an explicit Actions wrapper and loose
            # actions - merge the loose ones into the wrapper to keep a
            # single <actions> element.
            actions_wrapper.children = (  # type: ignore[attr-defined]
                list(actions_wrapper.children)  # type: ignore[attr-defined]
                + loose_actions
            )
            loose_actions = []

        rewritten: list[object] = list(meta)
        if actions_wrapper is not None:
            rewritten.append(actions_wrapper)
        elif loose_actions:
            rewritten.append(_Actions(*loose_actions))
        return rewritten


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

    Note:
        The shipped ``.x4-refs/aiscripts.xsd`` does *not* declare a
        ``<goto>`` element, yet every vanilla X4 AI script uses it to
        loop back to labels inside the main ``<actions>`` block. This
        is an XSD-shipping gap, not a library bug: the runtime happily
        executes ``<goto>``. The render-time XSD validator tolerates
        this element via an explicit known-gap allowlist (see
        :mod:`x4md._xsd_validation`).
    """

    def __init__(self, label: str) -> None:
        super().__init__(tag="goto", attrs=normalize_attrs({"label": label}))


class OnAbort(OrderChildNode):
    """Cleanup actions that run if the AI order is aborted.

    Maps to the ``<on_abort>`` element declared by ``aiscripts.xsd`` as
    a top-level ``<aiscript>`` child, at the same level as ``<order>``
    and ``<interrupts>``. In Python it is exposed as an
    ``OrderChildNode`` for ergonomic nesting: pass it inside
    :class:`Order`, and :class:`AIScript._rewrite_children` hoists it
    to the correct sibling position.

    This node previously lived in :mod:`x4md.md.document`; that location
    was wrong because ``md.xsd`` declares no ``<on_abort>`` element. Any
    MD script that embedded it would have been rejected by a strict
    validator. See ``KNOWN_DEFECTS.md`` for the migration history.

    Args:
        *children: Action nodes that execute during cleanup. Loose
            actions are emitted directly as ``<on_abort>`` children,
            matching ``xs:group ref="actions"`` in the schema.
        killed: When true, the actions only run if the script aborted
            because the entity was killed (per XSD ``killed`` attribute).
        comment: Optional comment for generated XML.

    Example:
        Order(
            "cleanup.example",
            SetOrderSyncpointReached(),
            OnAbort(DebugText("cleaning up"), SetValue(name="$busy", exact=False)),
            infinite=True,
        )
    """

    def __init__(
        self,
        *children: object,
        killed: bool | None = None,
        comment: str | None = None,
    ) -> None:
        super().__init__(
            tag="on_abort",
            attrs=normalize_attrs({"killed": killed, "comment": comment}),
            children=list(children),
        )


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


# Order-state lookup enum declared by ``aiscripts.xsd`` as the
# ``set_order_state`` ``state`` attribute type. Passing anything outside
# this set causes X4 to ignore the state change at runtime; the schema
# rejects it outright.
VALID_ORDER_STATES: frozenset[str] = frozenset({"orderstate.critical", "orderstate.finish"})


# Default target for the ``order`` attribute on the order-state mutation
# actions (``set_order_state``, ``set_order_syncpoint_reached``, etc.).
# The XSD marks ``order`` as required. In ship default-order scripts the
# running context is the *order object*, not the ship: ``this.order`` is
# null there. Vanilla order scripts therefore pass ``this.ship.order``
# (or ``this.assignedcontrolled.order`` for assist orders).
_DEFAULT_ORDER_REF = "this.ship.order"


class SetOrderFailed(OrderChildNode):
    """Mark the current order as failed with a user-visible message.

    Maps to X4 AI ``<set_order_failed>``. The schema requires both
    ``order`` (the order to mark, usually ``this.ship.order``) and ``text``
    (the failure message shown to the player).

    Args:
        text: Failure message expression (usually a ``TextExpr.quote(...)``
              or a ``TextExpr.ref(...)`` entry).
        order: Order reference; defaults to ``this.ship.order``.
        recurring: Whether to repeat the failure message.

    Example:
        SetOrderFailed(text=TextExpr.quote("No trade opportunities found"))
    """

    def __init__(
        self,
        *,
        text: ExprLike,
        order: ExprLike = _DEFAULT_ORDER_REF,
        recurring: ExprLike | None = None,
    ) -> None:
        super().__init__(
            tag="set_order_failed",
            attrs=normalize_attrs(
                {"order": order, "text": text, "recurring": recurring}
            ),
        )


class SetOrderState(OrderChildNode):
    """Transition the current order into one of the XSD-declared states.

    Maps to X4 AI ``<set_order_state>``. The schema requires ``order``
    and constrains ``state`` to :data:`VALID_ORDER_STATES`.

    Args:
        order: Order reference; defaults to ``this.ship.order``.
        state: Target state. Must be one of :data:`VALID_ORDER_STATES`
               (``"orderstate.critical"`` or ``"orderstate.finish"``).
               Passing anything else raises ``ValueError`` because X4
               silently drops unknown states at runtime.

    Example:
        SetOrderState(state="orderstate.finish")
    """

    def __init__(
        self,
        *,
        state: str | None = None,
        order: ExprLike = _DEFAULT_ORDER_REF,
    ) -> None:
        if state is not None and state not in VALID_ORDER_STATES:
            valid = ", ".join(sorted(VALID_ORDER_STATES))
            raise ValueError(
                f"Invalid <set_order_state state={state!r}>. X4 "
                f"aiscripts.xsd restricts this to the orderstatelookup "
                f"enum: {valid}. Pass one of those literals (not "
                f"free-form strings like 'STARTED', 'EXECUTING', etc.)."
            )
        super().__init__(
            tag="set_order_state",
            attrs=normalize_attrs({"order": order, "state": state}),
        )


class SetOrderSyncpointReached(OrderChildNode):
    """Signal that the order's sync point has been reached.

    Maps to X4 AI ``<set_order_syncpoint_reached>``. The schema requires
    ``order`` (the order whose sync point to mark). Vanilla scripts
    always point it at ``this.ship.order``.

    Args:
        order: Order reference; defaults to ``this.ship.order``.

    Example:
        SetOrderSyncpointReached()
    """

    def __init__(self, *, order: ExprLike = _DEFAULT_ORDER_REF) -> None:
        super().__init__(
            tag="set_order_syncpoint_reached",
            attrs=normalize_attrs({"order": order}),
        )


class ClearOrderFailure(OrderChildNode):
    """Clear any previously-set failure state on an order.

    Maps to X4 AI ``<clear_order_failure>``. The schema requires
    ``order``; vanilla scripts always point it at ``this.ship.order``.

    Args:
        order: Order reference; defaults to ``this.ship.order``.

    Example:
        ClearOrderFailure()
    """

    def __init__(self, *, order: ExprLike = _DEFAULT_ORDER_REF) -> None:
        super().__init__(
            tag="clear_order_failure",
            attrs=normalize_attrs({"order": order}),
        )


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


# AI attention levels declared in ``aiscripts.xsd`` (``attentionlookup``).
# The order element may have up to one ``<attention>`` section per level
# to give the ship level-specific behavior; ``"unknown"`` is the level
# assigned to a ship that has not been resolved yet and is the level
# under which the validator always checks that ``set_order_syncpoint_reached``
# is reachable.
VALID_ATTENTION_LEVELS: frozenset[str] = frozenset(
    {"unknown", "none", "visible", "scanned", "known", "minimal", "standard"}
)


class Attention(OrderChildNode):
    """Attention-level action block for an AI order.

    Maps to the X4 AI ``<attention>`` element with a required ``min``
    attribute naming an attention level (see :data:`VALID_ATTENTION_LEVELS`).
    The element wraps its own ``<actions>`` group, not arbitrary order
    children, so this class accepts :class:`Actions` children exactly
    like a ``<handler>`` does.

    Common mistake this class guards against: treating ``<attention>``
    like a one-shot "look at object X" action by passing an ``object``
    attribute. X4 actually defines that shape as ``<move_to>`` /
    ``<run_script>`` / similar blocking actions; the ``<attention>``
    element is an *attention-level section* wrapper. Emitting
    ``<attention object="X" min="5s"/>`` inside a ``<do_if>`` produces
    an order whose execution path re-enters an attention-level branch
    each tick, the runtime reports ``set_order_syncpoint_reached`` as
    missing at attention level ``unknown``, and the ship thrashes
    through the script with ``"returned but no new order in the queue"``
    messages every frame.

    Args:
        min: Attention level at which the wrapped actions apply. Must
            be one of :data:`VALID_ATTENTION_LEVELS`.
        *children: Child nodes for the wrapped ``<actions>`` group.
            Usually a single :class:`Actions` node.
        comment: Optional comment for the generated XML.

    Example:
        Attention(min="unknown", Actions(SetOrderSyncpointReached()))
    """

    def __init__(
        self,
        *children: ActionNode,
        min: str,
        comment: str | None = None,
    ) -> None:
        if min not in VALID_ATTENTION_LEVELS:
            valid = ", ".join(sorted(VALID_ATTENTION_LEVELS))
            raise ValueError(
                f"Invalid <attention> min={min!r}. X4 aiscripts.xsd "
                f"restricts this to the attentionlookup enum: {valid}."
            )
        super().__init__(
            tag="attention",
            attrs=normalize_attrs({"min": min, "comment": comment}),
            children=list(children),
        )


class MoveTo(OrderChildNode):
    """Fly an object to a destination (blocking).

    Maps to the X4 AI ``<move_to>`` element. Blocking: the ship actually
    travels to ``destination`` and the script only advances past this
    action when the movement resolves. This is the correct primitive for
    "send the QRF to its staging sector" or "close on the attacker", and
    is what ``<attention>`` is *not* (see :class:`Attention`).

    Args:
        object: Object doing the moving (typically ``this.ship``).
        destination: Target object or position expression.
        abortpath: Whether existing path points are dropped first.
        finishonapproach: If true, stop on approach instead of arriving.
        uselocalhighways: Allow local highways (default true in-game).
        useblacklist: Faction travel blacklist group name.
        useknownpath: Restrict to sectors known to the owner faction.
        flightbehaviour: Flight behaviour lookup.
        forcerotation: Keep rotating to match final orientation.
        rollintoturns: Bank into turns during movement.
        forceposition: Ignore obstacles for the final placement.
        comment: Optional comment on the generated XML.

    Example:
        MoveTo(object="this.ship", destination="$stage", finishonapproach=True)
    """

    def __init__(
        self,
        *,
        object: ExprLike,
        destination: ExprLike,
        abortpath: ExprLike | None = None,
        finishonapproach: ExprLike | None = None,
        uselocalhighways: ExprLike | None = None,
        useblacklist: ExprLike | None = None,
        useknownpath: ExprLike | None = None,
        flightbehaviour: ExprLike | None = None,
        forcerotation: ExprLike | None = None,
        rollintoturns: ExprLike | None = None,
        forceposition: ExprLike | None = None,
        comment: str | None = None,
    ) -> None:
        super().__init__(
            tag="move_to",
            attrs=normalize_attrs(
                {
                    "object": object,
                    "destination": destination,
                    "abortpath": abortpath,
                    "finishonapproach": finishonapproach,
                    "uselocalhighways": uselocalhighways,
                    "useblacklist": useblacklist,
                    "useknownpath": useknownpath,
                    "flightbehaviour": flightbehaviour,
                    "forcerotation": forcerotation,
                    "rollintoturns": rollintoturns,
                    "forceposition": forceposition,
                    "comment": comment,
                }
            ),
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


class Start(OrderChildNode):
    """Anchor for the jump-path start sector.

    Maps to the ``<start>`` child that ``<get_jump_path>`` requires
    (see ``common.xsd`` ``componentoffset``). The schema marks the
    ``object`` attribute as required; everything else is informational.

    Args:
        object: Reference to the starting sector/component.
        comment: Optional comment for generated XML.
    """

    def __init__(self, *, object: ExprLike, comment: str | None = None) -> None:
        super().__init__(
            tag="start",
            attrs=normalize_attrs({"object": object, "comment": comment}),
        )


class End(OrderChildNode):
    """Anchor for the jump-path end sector.

    Maps to the ``<end>`` child that ``<get_jump_path>`` requires. The
    schema treats all attributes as optional, but in practice callers
    supply at least ``object`` (pointing at the target sector). Position
    expressions (``x=``/``y=``/``z=`` etc.) are accepted for the
    rarer "jump to coordinate" case.

    Args:
        object: Reference to the target sector/component.
        x, y, z: Absolute coordinates.
        space: Space context.
        comment: Optional comment for generated XML.
    """

    def __init__(
        self,
        *,
        object: ExprLike | None = None,
        x: ExprLike | None = None,
        y: ExprLike | None = None,
        z: ExprLike | None = None,
        space: ExprLike | None = None,
        comment: str | None = None,
    ) -> None:
        super().__init__(
            tag="end",
            attrs=normalize_attrs(
                {
                    "object": object,
                    "x": x,
                    "y": y,
                    "z": z,
                    "space": space,
                    "comment": comment,
                }
            ),
        )


class GetJumpPath(OrderChildNode):
    """Compute a jump path between two sectors and store it in a variable.

    Maps to the X4 AI ``<get_jump_path>`` element. The schema
    (``common.xsd``) expects:

    - A required ``component`` **attribute** that names the lvalue
      receiving the path (list of components if ``multiple=true``,
      otherwise the first hop).
    - ``<start>`` and ``<end>`` **child elements** (not attributes)
      pointing at the source and destination sectors.

    For ergonomic callers, ``start=`` and ``end=`` also accept bare
    ``ExprLike`` values; those are auto-wrapped into
    ``<start object="..."/>`` / ``<end object="..."/>`` children. Pass
    explicit :class:`Start` / :class:`End` instances when you need to
    set additional attributes (coordinates, comments, etc.).

    Args:
        component: Variable to receive the result (first hop or full
            path list depending on ``multiple``).
        start: ``<start>`` anchor. Either a raw sector expression
            (shortcut for ``Start(object=start)``) or an explicit
            :class:`Start`.
        end: ``<end>`` anchor. Either a raw sector expression
            (shortcut for ``End(object=end)``) or an explicit :class:`End`.
        offset: Optional lvalue for the corresponding position list.
        refobject: Reference object whose known map knowledge is used.
        multiple: When true, returns the full path; otherwise only the
            first hop.
        useblacklist: Whether to apply the travel blacklist.
        useknownpath: Whether to restrict to known sectors.
        uselocalhighways: Whether local highways may be used.
        chance: Path-finding chance parameter.
        weight: Path-finding weight parameter.
        comment: Optional comment for generated XML.

    Raises:
        TypeError: If ``component`` is omitted. ``component`` is
            keyword-only and required by the XSD; Python enforces that
            at call time.

    Example:
        GetJumpPath(
            component="$path",
            start=PathExpr.of("this", "ship", "sector"),
            end="$target_sector",
        )
    """

    def __init__(
        self,
        *,
        component: ExprLike,
        start: "ExprLike | Start",
        end: "ExprLike | End",
        offset: ExprLike | None = None,
        refobject: ExprLike | None = None,
        multiple: bool | None = None,
        useblacklist: ExprLike | None = None,
        useknownpath: ExprLike | None = None,
        uselocalhighways: ExprLike | None = None,
        chance: ExprLike | None = None,
        weight: ExprLike | None = None,
        comment: str | None = None,
    ) -> None:
        start_node = start if isinstance(start, Start) else Start(object=start)
        end_node = end if isinstance(end, End) else End(object=end)

        super().__init__(
            tag="get_jump_path",
            attrs=normalize_attrs(
                {
                    "component": component,
                    "offset": offset,
                    "refobject": refobject,
                    "multiple": multiple,
                    "useblacklist": useblacklist,
                    "useknownpath": useknownpath,
                    "uselocalhighways": uselocalhighways,
                    "chance": chance,
                    "weight": weight,
                    "comment": comment,
                }
            ),
            children=[start_node, end_node],
        )


class SetCommand(OrderChildNode):
    """Set command interface for object.

    Maps to X4 AI <set_command> element.

    Args:
        command: Command token such as ``command.trade``. Pass
            ``Expr.raw("command.trade")`` or a plain string; bare strings
            are auto-wrapped with :meth:`Expr.raw` so the engine does not
            parse ``command.`` as a property chain.

    Example:
        SetCommand(command="command.trade")
    """

    def __init__(self, *, command: ExprLike) -> None:
        if isinstance(command, str):
            command = Expr.raw(command)
        super().__init__(
            tag="set_command",
            attrs=normalize_attrs({"command": command}),
        )


class SetCommandAction(OrderChildNode):
    """Set command action.

    Maps to X4 AI <set_command_action> element.

    Args:
        commandaction: Action token such as
            ``commandaction.searchingtrades``. Bare strings are
            auto-wrapped with :meth:`Expr.raw` for the same reason as
            :class:`SetCommand`.

    Example:
        SetCommandAction(commandaction="commandaction.searchingtrades")
    """

    def __init__(self, *, commandaction: ExprLike) -> None:
        if isinstance(commandaction, str):
            commandaction = Expr.raw(commandaction)
        super().__init__(
            tag="set_command_action",
            attrs=normalize_attrs({"commandaction": commandaction}),
        )
