"""Action and flow nodes for MD."""

from __future__ import annotations

from typing import Literal, TypeAlias

from x4md.expressions import ExprLike

from .common import normalize_attrs
from .types import ActionNode, ParamNode


Operation: TypeAlias = Literal["add", "subtract", "multiply", "divide"]


class Params(ParamNode):
    def __init__(self, *children: ParamNode) -> None:
        super().__init__(tag="params", children=list(children))


class Param(ParamNode):
    def __init__(
        self,
        name: str,
        *children: ParamNode,
        default: ExprLike | None = None,
        value: ExprLike | None = None,
        type_: str | None = None,
        text: str | None = None,
        comment: str | None = None,
        advanced: bool | None = None,
    ) -> None:
        super().__init__(
            tag="param",
            attrs=normalize_attrs(
                {
                    "name": name,
                    "default": default,
                    "value": value,
                    "type": type_,
                    "text": text,
                    "comment": comment,
                    "advanced": advanced,
                }
            ),
            children=list(children),
        )


class Actions(ActionNode):
    def __init__(self, *children: ActionNode) -> None:
        super().__init__(tag="actions", children=list(children))


class SetValue(ActionNode):
    def __init__(
        self,
        name: str,
        *,
        exact: ExprLike | None = None,
        operation: Operation | None = None,
    ) -> None:
        super().__init__(
            tag="set_value",
            attrs=normalize_attrs({"name": name, "exact": exact, "operation": operation}),
        )


class RunActions(ActionNode):
    def __init__(
        self,
        ref: str,
        *params: Param,
        result: str | None = None,
    ) -> None:
        super().__init__(
            tag="run_actions",
            attrs=normalize_attrs({"ref": ref, "result": result}),
            children=list(params),
        )


class Return(ActionNode):
    def __init__(self, value: ExprLike) -> None:
        super().__init__(tag="return", attrs=normalize_attrs({"value": value}))


class DoIf(ActionNode):
    def __init__(self, value: ExprLike, *children: ActionNode, comment: str | None = None) -> None:
        super().__init__(
            tag="do_if",
            attrs=normalize_attrs({"value": value, "comment": comment}),
            children=list(children),
        )


class DoElse(ActionNode):
    def __init__(self, *children: ActionNode) -> None:
        super().__init__(tag="do_else", children=list(children))


class DoElseIf(ActionNode):
    def __init__(self, value: ExprLike, *children: ActionNode) -> None:
        super().__init__(
            tag="do_elseif",
            attrs=normalize_attrs({"value": value}),
            children=list(children),
        )


class DoAll(ActionNode):
    def __init__(
        self,
        exact: ExprLike,
        *children: ActionNode,
        counter: str | None = None,
        reverse: bool | None = None,
    ) -> None:
        super().__init__(
            tag="do_all",
            attrs=normalize_attrs({"exact": exact, "counter": counter, "reverse": reverse}),
            children=list(children),
        )


class SignalCueInstantly(ActionNode):
    def __init__(self, cue: str, *, param: ExprLike | None = None) -> None:
        super().__init__(
            tag="signal_cue_instantly",
            attrs=normalize_attrs({"cue": cue, "param": param}),
        )


class SignalObjects(ActionNode):
    def __init__(
        self,
        object: ExprLike,
        param: ExprLike,
        *,
        param2: ExprLike | None = None,
        delay: ExprLike | None = None,
    ) -> None:
        super().__init__(
            tag="signal_objects",
            attrs=normalize_attrs(
                {
                    "object": object,
                    "param": param,
                    "param2": param2,
                    "delay": delay,
                }
            ),
        )


class DebugText(ActionNode):
    def __init__(self, text: ExprLike, *, chance: ExprLike | None = None) -> None:
        super().__init__(
            tag="debug_text",
            attrs=normalize_attrs({"text": text, "chance": chance}),
        )


class RemoveValue(ActionNode):
    """Remove a variable from scope.

    Maps to X4 MD <remove_value name="..."/> element.

    Args:
        name: Name of variable to remove

    Example:
        RemoveValue("$tempData")
    """

    def __init__(self, name: str) -> None:
        super().__init__(tag="remove_value", attrs=normalize_attrs({"name": name}))


class AppendToList(ActionNode):
    """Append a value to a list variable.

    Maps to X4 MD <append_to_list> element.

    Args:
        name: Name of list variable to append to
        exact: Value to append to the list

    Example:
        AppendToList("$errors", exact=TextExpr.quote("Validation failed"))
    """

    def __init__(self, name: str, *, exact: ExprLike) -> None:
        super().__init__(
            tag="append_to_list",
            attrs=normalize_attrs({"name": name, "exact": exact}),
        )


class RemoveFromList(ActionNode):
    """Remove a value from a list variable.

    Maps to X4 MD <remove_from_list> element.

    Args:
        name: Name of list variable to remove from
        exact: Value to remove from the list

    Example:
        RemoveFromList("$queue", exact="$processedItem")
    """

    def __init__(self, name: str, *, exact: ExprLike) -> None:
        super().__init__(
            tag="remove_from_list",
            attrs=normalize_attrs({"name": name, "exact": exact}),
        )


class DoWhile(ActionNode):
    """Loop while a condition is true.

    Maps to X4 MD <do_while value="..."> element.

    Args:
        value: Boolean expression to evaluate each iteration
        *children: Action nodes to execute while condition is true

    Example:
        DoWhile(
            "$queue.count gt 0",
            SetValue("$item", exact="$queue.{1}"),
            RemoveFromList("$queue", exact="$item"),
        )
    """

    def __init__(self, value: ExprLike, *children: ActionNode) -> None:
        super().__init__(
            tag="do_while",
            attrs=normalize_attrs({"value": value}),
            children=list(children),
        )


class DoForEach(ActionNode):
    """Iterate over each element in a collection.

    Maps to X4 MD <do_for_each> element.

    Args:
        name: Variable name for current item
        in_: Collection to iterate over
        *children: Action nodes to execute for each item
        counter: Optional counter variable name
        reverse: Whether to iterate in reverse order

    Example:
        DoForEach(
            "$ship",
            in_="$ships",
            DebugText("Processing: {$ship.knownname}"),
        )
    """

    def __init__(
        self,
        name: str,
        *children: ActionNode,
        in_: ExprLike,
        counter: str | None = None,
        reverse: bool | None = None,
    ) -> None:
        super().__init__(
            tag="do_for_each",
            attrs=normalize_attrs({"name": name, "in": in_, "counter": counter, "reverse": reverse}),
            children=list(children),
        )


class Break(ActionNode):
    """Break out of current loop.

    Maps to X4 MD <break/> element.

    Example:
        DoWhile(
            "true",
            DoIf("$found", Break()),
        )
    """

    def __init__(self) -> None:
        super().__init__(tag="break")


class Continue(ActionNode):
    """Continue to next iteration of current loop.

    Maps to X4 MD <continue/> element.

    Example:
        DoAll(
            "$items",
            DoIf("not $items.{$i}.valid", Continue()),
        )
    """

    def __init__(self) -> None:
        super().__init__(tag="continue")


class SignalCueAction(ActionNode):
    """Signal a cue with optional parameter (action node).

    Maps to X4 MD <signal_cue> element.

    Args:
        cue: Name of cue to signal
        param: Optional parameter to pass

    Example:
        SignalCueAction("ProcessTrade", param="$tradeData")
    """

    def __init__(self, cue: str, *, param: ExprLike | None = None) -> None:
        super().__init__(
            tag="signal_cue",
            attrs=normalize_attrs({"cue": cue, "param": param}),
        )


class CancelCue(ActionNode):
    """Cancel a running cue.

    Maps to X4 MD <cancel_cue cue="..."/> element.

    Args:
        cue: Name of cue to cancel

    Example:
        CancelCue("ProcessingLoop")
    """

    def __init__(self, cue: str) -> None:
        super().__init__(tag="cancel_cue", attrs=normalize_attrs({"cue": cue}))


class CreateOrder(ActionNode):
    """Create an order for a ship or station.

    Maps to X4 MD <create_order> element.

    Args:
        object: Ship or station to receive order
        id: Order ID to create
        *params: Parameters for the order
        immediate: Whether to execute order immediately

    Example:
        CreateOrder(
            object="$ship",
            id=TextExpr.quote("GalaxyTraderMK3"),
            Param("home", value="$homeSector"),
            immediate=True,
        )
    """

    def __init__(
        self,
        *params: Param,
        object: ExprLike,
        id: ExprLike,
        immediate: bool | None = None,
    ) -> None:
        super().__init__(
            tag="create_order",
            attrs=normalize_attrs({"object": object, "id": id, "immediate": immediate}),
            children=list(params),
        )


class CancelOrder(ActionNode):
    """Cancel a ship's current order.

    Maps to X4 MD <cancel_order> element.

    Args:
        object: Ship whose order to cancel

    Example:
        CancelOrder(object="$ship")
    """

    def __init__(self, *, object: ExprLike) -> None:
        super().__init__(tag="cancel_order", attrs=normalize_attrs({"object": object}))


class CancelAllOrders(ActionNode):
    """Cancel all orders for a ship.

    Maps to X4 MD <cancel_all_orders> element.

    Args:
        object: Ship whose orders to cancel

    Example:
        CancelAllOrders(object="$ship")
    """

    def __init__(self, *, object: ExprLike) -> None:
        super().__init__(tag="cancel_all_orders", attrs=normalize_attrs({"object": object}))


class WriteToLogbook(ActionNode):
    """Write an entry to the player's logbook.

    Maps to X4 MD <write_to_logbook> element.

    Args:
        category: Logbook category
        title: Entry title
        text: Entry text
        interaction: Optional interaction object
        money: Optional money amount

    Example:
        WriteToLogbook(
            category="upkeep",
            title=TextExpr.quote("Trade Complete"),
            text=TextExpr.quote("Profit: {$profit}Cr"),
        )
    """

    def __init__(
        self,
        *,
        category: str,
        title: ExprLike,
        text: ExprLike | None = None,
        interaction: ExprLike | None = None,
        money: ExprLike | None = None,
    ) -> None:
        super().__init__(
            tag="write_to_logbook",
            attrs=normalize_attrs({
                "category": category,
                "title": title,
                "text": text,
                "interaction": interaction,
                "money": money,
            }),
        )


class ShowNotification(ActionNode):
    """Show a notification to the player.

    Maps to X4 MD <show_notification> element.

    Args:
        text: Notification text
        caption: Optional caption
        sound: Optional sound effect
        timeout: Optional timeout duration

    Example:
        ShowNotification(
            text=TextExpr.quote("Trade completed successfully"),
            caption=TextExpr.quote("GalaxyTrader"),
        )
    """

    def __init__(
        self,
        *,
        text: ExprLike,
        caption: ExprLike | None = None,
        sound: str | None = None,
        timeout: ExprLike | None = None,
    ) -> None:
        super().__init__(
            tag="show_notification",
            attrs=normalize_attrs({
                "text": text,
                "caption": caption,
                "sound": sound,
                "timeout": timeout,
            }),
        )


class SetObjectName(ActionNode):
    """Set the name of an object.

    Maps to X4 MD <set_object_name> element.

    Args:
        object: Object to rename
        name: New name for the object

    Example:
        SetObjectName(object="$ship", name=TextExpr.quote("Trader-1"))
    """

    def __init__(self, *, object: ExprLike, name: ExprLike) -> None:
        super().__init__(
            tag="set_object_name",
            attrs=normalize_attrs({"object": object, "name": name}),
        )


class RaiseLuaEvent(ActionNode):
    """Raise a Lua event.

    Maps to X4 MD <raise_lua_event> element.

    Args:
        name: Event name
        param: Event parameter

    Example:
        RaiseLuaEvent(name=TextExpr.quote("GT_TradeComplete"), param="$tradeData")
    """

    def __init__(self, *, name: ExprLike, param: ExprLike | None = None) -> None:
        super().__init__(
            tag="raise_lua_event",
            attrs=normalize_attrs({"name": name, "param": param}),
        )
