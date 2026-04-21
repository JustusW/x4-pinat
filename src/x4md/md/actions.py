"""Action and flow nodes for MD."""

from __future__ import annotations

from typing import Literal, TypeAlias

from x4md.core import XmlElement
from x4md.expressions import ExprLike

from .common import normalize_attrs, validate_md_lvalue
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
    def __init__(self, *children: XmlElement) -> None:
        """Action sequence wrapper.

        Note: In AI script handlers, this may contain AI order commands
        (OrderChildNode) alongside MD actions, which is why we accept
        XmlElement rather than just ActionNode.
        """
        super().__init__(tag="actions", children=list(children))


class SetValue(ActionNode):
    def __init__(
        self,
        name: str,
        *,
        exact: ExprLike | None = None,
        operation: Operation | None = None,
    ) -> None:
        validate_md_lvalue(name, action="SetValue")
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
    def __init__(self, value: ExprLike, *children: ConditionNode, comment: str | None = None) -> None:
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
        *children: ConditionNode,
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
        validate_md_lvalue(name, action="RemoveValue")
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
        validate_md_lvalue(name, action="AppendToList")
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
        validate_md_lvalue(name, action="RemoveFromList")
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
        *children: ConditionNode,
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
    """Cancel a specific AI order and remove it from the owner's queue.

    Maps to X4 MD ``<cancel_order>`` element. The XSD requires the
    ``order`` attribute (an expression that evaluates to an AI order,
    e.g. ``$order`` or ``$ship.pilot.order``). Passing the ship/station
    object instead is a common mistake that surfaces in ``debuglog.txt``
    as ``Required attribute 'order' is missing in <cancel_order>``; to
    cancel every order on an object use :class:`CancelAllOrders`
    instead.

    Args:
        order: Order to cancel. Expression yielding an ``order`` value
            (the XSD attribute is required).
        keepinloop: For cancelled loop orders, keep the cancelled order
            in the loop instead of removing it. Only meaningful for
            non-temporary orders that are part of an order loop.

    Example:
        CancelOrder(order="$order")
        CancelOrder(order="$ship.pilot.order", keepinloop=True)
    """

    def __init__(
        self,
        *,
        order: ExprLike,
        keepinloop: bool | None = None,
    ) -> None:
        super().__init__(
            tag="cancel_order",
            attrs=normalize_attrs({"order": order, "keepinloop": keepinloop}),
        )


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


# X4 only accepts a fixed set of logbook categories. The most common
# mistake is writing "alert" (singular) which the engine logs as
# "Invalid or missing log category" and then drops the write without
# surfacing a logbook entry. The values here mirror the
# ``logcategorylookup`` enum in ``common.xsd`` (the shared schema
# shipped with the game); keep this list in sync if Egosoft ever adds
# new categories in a future patch.
VALID_LOGBOOK_CATEGORIES: frozenset[str] = frozenset(
    {"general", "missions", "news", "upkeep", "alerts", "tips"}
)


# Interaction types accepted by ``<write_to_logbook interaction="..."/>``.
# Mirrors the ``loginteractionlookup`` enum in ``common.xsd``. Using an
# unknown value causes X4 to reject the logbook entry at load time.
VALID_LOGBOOK_INTERACTIONS: frozenset[str] = frozenset(
    {"guidance", "showonmap", "showlocationonmap"}
)


class WriteToLogbook(ActionNode):
    """Write an entry to the player's logbook.

    Maps to X4 MD ``<write_to_logbook>`` element. The attribute list
    mirrors the element definition in ``common.xsd``.

    Args:
        category: Logbook category. Must be one of
            :data:`VALID_LOGBOOK_CATEGORIES`. ``category`` is a required
            attribute in the XSD.
        title: Entry title (required by XSD).
        text: Entry text, either a single string or a notification-style
            list of rows.
        separator: Optional separator used between the left/right column
            of a notification row (defaults to a single space in-game).
        interaction: Optional logbook interaction type. When set, it
            must be one of :data:`VALID_LOGBOOK_INTERACTIONS`.
        object: Optional interaction object (meaning depends on
            ``interaction``).
        position: Optional interaction position (used with
            ``interaction="showlocationonmap"``).
        entity: Optional source entity (real entity or plain name).
        faction: Optional source faction (real faction or plain name).
        money: Optional money amount associated with the entry.
        bonus: Optional bonus amount associated with the entry.
        highlighted: Whether the logbook entry should be highlighted.

    Raises:
        ValueError: If ``category`` is not a known X4 logbook category,
            or if ``interaction`` is set to an unknown value.

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
        separator: ExprLike | None = None,
        interaction: str | None = None,
        object: ExprLike | None = None,
        position: ExprLike | None = None,
        entity: ExprLike | None = None,
        faction: ExprLike | None = None,
        money: ExprLike | None = None,
        bonus: ExprLike | None = None,
        highlighted: bool | None = None,
    ) -> None:
        if category not in VALID_LOGBOOK_CATEGORIES:
            valid = ", ".join(sorted(VALID_LOGBOOK_CATEGORIES))
            raise ValueError(
                f"Invalid WriteToLogbook category {category!r}. X4 "
                f"accepts only: {valid}. Note that 'alert' (singular) "
                "is a common typo; the correct value is 'alerts'."
            )
        if interaction is not None and interaction not in VALID_LOGBOOK_INTERACTIONS:
            valid_inter = ", ".join(sorted(VALID_LOGBOOK_INTERACTIONS))
            raise ValueError(
                f"Invalid WriteToLogbook interaction {interaction!r}. "
                f"X4 accepts only: {valid_inter}."
            )
        super().__init__(
            tag="write_to_logbook",
            attrs=normalize_attrs({
                "category": category,
                "title": title,
                "text": text,
                "separator": separator,
                "interaction": interaction,
                "object": object,
                "position": position,
                "entity": entity,
                "faction": faction,
                "money": money,
                "bonus": bonus,
                "highlighted": highlighted,
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


class SetSkill(ActionNode):
    """Set skill level for an NPC.

    Maps to X4 MD <set_skill> element.

    Args:
        object: NPC to modify
        skill: Skill type to set
        exact: Exact skill value
        value: Skill value
        min: Minimum skill value
        max: Maximum skill value
        comment: Optional comment

    Example:
        SetSkill(object="$pilot", skill="piloting", exact=3)
    """

    def __init__(
        self,
        *,
        object: ExprLike,
        skill: str,
        exact: ExprLike | None = None,
        value: ExprLike | None = None,
        min: ExprLike | None = None,
        max: ExprLike | None = None,
        comment: str | None = None,
    ) -> None:
        super().__init__(
            tag="set_skill",
            attrs=normalize_attrs({
                "object": object,
                "skill": skill,
                "exact": exact,
                "value": value,
                "min": min,
                "max": max,
                "comment": comment,
            }),
        )


class CreateList(ActionNode):
    """Create a new list variable.

    Maps to X4 MD <create_list name="..."/> element.

    Args:
        name: Name of list variable to create

    Example:
        CreateList(name="$candidates")
    """

    def __init__(self, *, name: str) -> None:
        validate_md_lvalue(name, action="CreateList")
        super().__init__(tag="create_list", attrs=normalize_attrs({"name": name}))


class ShuffleList(ActionNode):
    """Randomize the order of a list.

    Maps to X4 MD <shuffle_list list="..."/> element.

    Args:
        list: List variable to shuffle

    Example:
        ShuffleList(list="$trades")
    """

    def __init__(self, *, list: str) -> None:
        validate_md_lvalue(list, action="ShuffleList")
        super().__init__(tag="shuffle_list", attrs=normalize_attrs({"list": list}))


class SortList(ActionNode):
    """Sort a list by criteria.

    Maps to X4 MD ``<sort_list>`` element (see ``common.xsd``). The XSD
    requires the list argument to be named ``list`` (the sort criterion
    is ``sortbyvalue``, not ``sortkey``); emitting the list attribute as
    ``name`` causes X4 to reject the script at load time with
    "Required attribute 'list' is missing".

    Args:
        list: List variable to sort (required).
        sortbyvalue: Optional expression evaluated per element. The
            implicit iteration variables are ``loop.element`` and
            ``loop.index``. Omit to sort by natural value order.
        sortdescending: When ``True``, sort from highest to lowest.

    Example:
        SortList(
            list="$sectors",
            sortbyvalue="global.$gp.encountercounts.{loop.element}",
            sortdescending=True,
        )
    """

    def __init__(
        self,
        *,
        list: ExprLike,
        sortbyvalue: ExprLike | None = None,
        sortdescending: ExprLike | None = None,
    ) -> None:
        validate_md_lvalue(list, action="SortList")
        super().__init__(
            tag="sort_list",
            attrs=normalize_attrs(
                {
                    "list": list,
                    "sortbyvalue": sortbyvalue,
                    "sortdescending": sortdescending,
                }
            ),
        )


class EditOrderParam(ActionNode):
    """Edit a parameter of an existing order.

    Maps to X4 MD <edit_order_param> element.

    Args:
        object: Object whose order to modify
        orderid: ID of the order to modify (optional)
        param: Parameter name to edit
        value: New parameter value

    Example:
        EditOrderParam(object="$ship", orderid="TradeRoutine", param="maxbuy", value=10)
    """

    def __init__(
        self,
        *,
        object: ExprLike,
        param: str,
        value: ExprLike,
        orderid: ExprLike | None = None,
    ) -> None:
        super().__init__(
            tag="edit_order_param",
            attrs=normalize_attrs({
                "object": object,
                "orderid": orderid,
                "param": param,
                "value": value,
            }),
        )


class SubstituteText(ActionNode):
    """Perform text substitution with variables.

    Maps to X4 MD <substitute_text> element.

    Args:
        text: Text template with placeholders
        source: Source object for substitution
        result: Variable to store result

    Example:
        SubstituteText(text="Ship: {ship.name}", source="$ship", result="$message")
    """

    def __init__(self, *, text: ExprLike, source: ExprLike | None = None, result: str | None = None) -> None:
        super().__init__(
            tag="substitute_text",
            attrs=normalize_attrs({"text": text, "source": source, "result": result}),
        )


class RewardPlayer(ActionNode):
    """Give rewards to the player.

    Maps to X4 MD <reward_player> element.

    Args:
        money: Money amount to give
        notificationtext: Optional notification text

    Example:
        RewardPlayer(money=MoneyExpr.of(10000), notificationtext=TextExpr.quote("Bonus!"))
    """

    def __init__(self, *, money: ExprLike | None = None, notificationtext: ExprLike | None = None) -> None:
        super().__init__(
            tag="reward_player",
            attrs=normalize_attrs({"money": money, "notificationtext": notificationtext}),
        )


# Find/Query Actions - these are complex with child match nodes

class FindBuyOffer(ActionNode):
    """Find buy offers matching criteria.

    Maps to X4 MD <find_buy_offer> element.

    Args:
        *children: Match condition nodes
        space: Space/sector to search
        wares: Wares to search for
        tradepartner: Ship for trade partner checks
        result: Variable to store result
        multiple: Whether to find multiple results

    Example:
        FindBuyOffer(
            space="$sector",
            tradepartner="$ship",
            result="$buyOffers",
            multiple=True,
        )
    """

    def __init__(
        self,
        *children: ConditionNode,
        space: ExprLike | None = None,
        wares: ExprLike | None = None,
        tradepartner: ExprLike | None = None,
        result: str | None = None,
        multiple: bool | None = None,
    ) -> None:
        super().__init__(
            tag="find_buy_offer",
            attrs=normalize_attrs({
                "space": space,
                "wares": wares,
                "tradepartner": tradepartner,
                "result": result,
                "multiple": multiple,
            }),
            children=list(children),
        )


class FindSellOffer(ActionNode):
    """Find sell offers matching criteria.

    Maps to X4 MD <find_sell_offer> element.

    Args:
        *children: Match condition nodes
        space: Space/sector to search
        wares: Wares to search for
        tradepartner: Ship for trade partner checks
        result: Variable to store result
        multiple: Whether to find multiple results

    Example:
        FindSellOffer(
            space="$sector",
            wares="[$ware]",
            result="$sellOffers",
            multiple=True,
        )
    """

    def __init__(
        self,
        *children: ConditionNode,
        space: ExprLike | None = None,
        wares: ExprLike | None = None,
        tradepartner: ExprLike | None = None,
        result: str | None = None,
        multiple: bool | None = None,
    ) -> None:
        super().__init__(
            tag="find_sell_offer",
            attrs=normalize_attrs({
                "space": space,
                "wares": wares,
                "tradepartner": tradepartner,
                "result": result,
                "multiple": multiple,
            }),
            children=list(children),
        )


class FindStation(ActionNode):
    """Find stations matching criteria.

    Maps to X4 MD <find_station> element.

    Args:
        *children: Match condition nodes
        name: Variable to store result
        space: Space/sector to search
        multiple: Whether to find multiple results
        tradesknownto: Faction that knows trades
        sortbydistanceto: Object to sort by distance from

    Example:
        FindStation(
            name="$stations",
            space="player.galaxy",
            multiple=True,
            tradesknownto="faction.player",
        )
    """

    def __init__(
        self,
        *children: ConditionNode,
        name: str | None = None,
        space: ExprLike | None = None,
        multiple: bool | None = None,
        tradesknownto: ExprLike | None = None,
        sortbydistanceto: ExprLike | None = None,
    ) -> None:
        super().__init__(
            tag="find_station",
            attrs=normalize_attrs({
                "name": name,
                "space": space,
                "multiple": multiple,
                "tradesknownto": tradesknownto,
                "sortbydistanceto": sortbydistanceto,
            }),
            children=list(children),
        )


class FindSector(ActionNode):
    """Find sectors matching criteria.

    Maps to X4 MD <find_sector> element.

    Args:
        *children: Match condition nodes
        name: Variable to store result
        space: Space to search
        multiple: Whether to find multiple results

    Example:
        FindSector(name="$sectors", space="player.galaxy", multiple=True)
    """

    def __init__(
        self,
        *children: ConditionNode,
        name: str | None = None,
        space: ExprLike | None = None,
        multiple: bool | None = None,
    ) -> None:
        super().__init__(
            tag="find_sector",
            attrs=normalize_attrs({"name": name, "space": space, "multiple": multiple}),
            children=list(children),
        )


class FindGate(ActionNode):
    """Find gates matching criteria.

    Maps to X4 MD <find_gate> element.

    Args:
        *children: Match condition nodes
        name: Variable to store result
        space: Space/sector to search
        multiple: Whether to find multiple results

    Example:
        FindGate(name="$gates", space="$sector", multiple=True)
    """

    def __init__(
        self,
        *children: ConditionNode,
        name: str | None = None,
        space: ExprLike | None = None,
        multiple: bool | None = None,
    ) -> None:
        super().__init__(
            tag="find_gate",
            attrs=normalize_attrs({"name": name, "space": space, "multiple": multiple}),
            children=list(children),
        )


class FindDockingbay(ActionNode):
    """Find docking bays matching criteria.

    Maps to X4 MD <find_dockingbay> element.

    Args:
        *children: Match condition nodes
        name: Variable to store result
        object: Object to search for docking bays
        checkoperational: Whether to check if operational
        multiple: Whether to find multiple results

    Example:
        FindDockingbay(name="$dock", object="$station", checkoperational=True)
    """

    def __init__(
        self,
        *children: ConditionNode,
        name: str | None = None,
        object: ExprLike | None = None,
        checkoperational: bool | None = None,
        multiple: bool | None = None,
    ) -> None:
        super().__init__(
            tag="find_dockingbay",
            attrs=normalize_attrs({
                "name": name,
                "object": object,
                "checkoperational": checkoperational,
                "multiple": multiple,
            }),
            children=list(children),
        )


class FindShip(ActionNode):
    """Find ships matching criteria.

    Maps to X4 MD <find_ship> element.

    Args:
        *children: Match condition nodes
        name: Variable to store result
        space: Space/sector to search
        multiple: Whether to find multiple results

    Example:
        FindShip(name="$ships", space="$sector", multiple=True)
    """

    def __init__(
        self,
        *children: ConditionNode,
        name: str | None = None,
        space: ExprLike | None = None,
        multiple: bool | None = None,
    ) -> None:
        super().__init__(
            tag="find_ship",
            attrs=normalize_attrs({"name": name, "space": space, "multiple": multiple}),
            children=list(children),
        )


class FindObject(ActionNode):
    """Find objects matching criteria.

    Maps to X4 MD <find_object> element.

    Args:
        *children: Match condition nodes
        name: Variable to store result
        space: Space/sector to search
        multiple: Whether to find multiple results
        class_: Object class to find

    Example:
        FindObject(name="$objects", space="$sector", class_="station")
    """

    def __init__(
        self,
        *children: ConditionNode,
        name: str | None = None,
        space: ExprLike | None = None,
        multiple: bool | None = None,
        class_: str | None = None,
    ) -> None:
        super().__init__(
            tag="find_object",
            attrs=normalize_attrs({
                "name": name,
                "space": space,
                "multiple": multiple,
                "class": class_,
            }),
            children=list(children),
        )


class GetWareReservation(ActionNode):
    """Get ware reservation amount.

    Maps to X4 MD <get_ware_reservation> element.

    Args:
        object: Object with reservations
        ware: Ware to check
        type: Reservation type ('buy' or 'sell')
        virtual: Whether to check virtual reservations
        result: Variable to store result

    Example:
        GetWareReservation(
            object="$station",
            ware="$ware",
            type="sell",
            virtual=False,
            result="$reserved",
        )
    """

    def __init__(
        self,
        *,
        object: ExprLike,
        ware: ExprLike,
        type: str,
        virtual: bool | None = None,
        result: str,
    ) -> None:
        super().__init__(
            tag="get_ware_reservation",
            attrs=normalize_attrs({
                "object": object,
                "ware": ware,
                "type": type,
                "virtual": virtual,
                "result": result,
            }),
        )


class SortTrades(ActionNode):
    """Sort trade offers by profitability and other criteria.

    Maps to X4 MD <sort_trades> element. GalaxyTrader-specific action
    that sorts trade offers to prioritize the most profitable routes.

    Args:
        tradelist: List of trade offers to sort
        sorter: Sorting criteria/expression
        result: Variable name to store sorted list

    Example:
        SortTrades(
            tradelist="$availableTrades",
            sorter="@$trade.profit",
            result="$sortedTrades"
        )
    """

    def __init__(
        self,
        *,
        tradelist: ExprLike,
        sorter: ExprLike,
        result: str,
    ) -> None:
        super().__init__(
            tag="sort_trades",
            attrs=normalize_attrs(
                {
                    "tradelist": tradelist,
                    "sorter": sorter,
                    "result": result,
                }
            ),
        )


class AppendListElements(ActionNode):
    """Append all elements from one list to another.

    Maps to X4 MD <append_list_elements> element.

    Args:
        name: Target list to append to
        other: Source list to append from

    Example:
        AppendListElements(name="$allShips", other="$newShips")
    """

    def __init__(self, *, name: str, other: ExprLike) -> None:
        super().__init__(
            tag="append_list_elements",
            attrs=normalize_attrs({"name": name, "other": other}),
        )

