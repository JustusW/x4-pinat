"""Tests for MD action nodes."""

import unittest

from x4md import (
    Actions,
    AppendToList,
    Break,
    CancelAllOrders,
    CancelCue,
    CancelOrder,
    Continue,
    DebugText,
    DoAll,
    DoElse,
    DoElseIf,
    DoForEach,
    DoIf,
    DoWhile,
    MDCreateOrder,
    MoneyExpr,
    Param,
    PathExpr,
    RaiseLuaEvent,
    RemoveFromList,
    RemoveValue,
    Return,
    RunActions,
    SetObjectName,
    SetValue,
    ShowNotification,
    SignalCueAction,
    SignalCueInstantly,
    SignalObjects,
    TableEntry,
    TableExpr,
    TextExpr,
    WriteToLogbook,
)


class BasicActionTests(unittest.TestCase):
    """Tests for basic action nodes."""

    def test_remove_value_renders_correctly(self) -> None:
        """RemoveValue renders with name attribute."""
        node = RemoveValue("$tempData")
        self.assertEqual(str(node), '<remove_value name="$tempData"/>')

    def test_set_value_renders_correctly(self) -> None:
        """SetValue renders with name and exact."""
        node = SetValue("$count", exact=5)
        xml = str(node)
        self.assertIn('name="$count"', xml)
        self.assertIn('exact="5"', xml)

    def test_debug_text_renders_correctly(self) -> None:
        """DebugText renders with text and chance."""
        node = DebugText("Test", chance=100)
        xml = str(node)
        self.assertIn('text="Test"', xml)
        self.assertIn('chance="100"', xml)

    def test_return_renders_correctly(self) -> None:
        """Return renders with value."""
        node = Return(True)
        self.assertIn('value="true"', str(node))


class ListActionTests(unittest.TestCase):
    """Tests for list manipulation actions."""

    def test_append_to_list_renders_correctly(self) -> None:
        """AppendToList renders with name and exact attributes."""
        node = AppendToList("$errors", exact=TextExpr.quote("Error message"))
        xml = str(node)
        self.assertIn('<append_to_list', xml)
        self.assertIn('name="$errors"', xml)
        self.assertIn("exact=\"'Error message'\"", xml)

    def test_append_to_list_with_expression(self) -> None:
        """AppendToList accepts expression objects."""
        node = AppendToList("$ships", exact=PathExpr.of("this", "ship"))
        self.assertIn('exact="this.ship"', str(node))

    def test_remove_from_list_renders_correctly(self) -> None:
        """RemoveFromList renders with name and exact attributes."""
        node = RemoveFromList("$queue", exact="$processedItem")
        xml = str(node)
        self.assertIn('<remove_from_list', xml)
        self.assertIn('name="$queue"', xml)
        self.assertIn('exact="$processedItem"', xml)


class FlowControlTests(unittest.TestCase):
    """Tests for flow control action nodes."""

    def test_do_if_renders_with_children(self) -> None:
        """DoIf renders nested action block."""
        node = DoIf("$ready", SetValue("$count", exact=1))
        xml = str(node)
        self.assertIn('<do_if value="$ready">', xml)
        self.assertIn('<set_value', xml)
        self.assertIn('</do_if>', xml)

    def test_do_else_renders_correctly(self) -> None:
        """DoElse renders without attributes."""
        node = DoElse(DebugText("else"))
        xml = str(node)
        self.assertIn('<do_else>', xml)
        self.assertIn('</do_else>', xml)

    def test_do_elseif_renders_correctly(self) -> None:
        """DoElseIf renders with value condition."""
        node = DoElseIf("$other", DebugText(TextExpr.quote("other")))
        xml = str(node)
        self.assertIn('value="$other"', xml)

    def test_do_all_renders_with_options(self) -> None:
        """DoAll renders with counter and reverse."""
        node = DoAll("5", DebugText(TextExpr.quote("tick")), counter="$i", reverse=True)
        xml = str(node)
        self.assertIn('exact="5"', xml)
        self.assertIn('counter="$i"', xml)
        self.assertIn('reverse="true"', xml)


class LoopActionTests(unittest.TestCase):
    """Tests for loop action nodes."""

    def test_do_while_renders_with_children(self) -> None:
        """DoWhile renders nested action block with condition."""
        node = DoWhile(
            "$queue.count gt 0",
            SetValue("$item", exact="$queue.{1}"),
            RemoveFromList("$queue", exact="$item"),
        )
        xml = str(node)
        self.assertIn('<do_while value="$queue.count gt 0">', xml)
        self.assertIn('<set_value name="$item"', xml)
        self.assertIn('<remove_from_list', xml)
        self.assertIn('</do_while>', xml)

    def test_do_for_each_renders_correctly(self) -> None:
        """DoForEach renders with name, in, and optional parameters."""
        node = DoForEach(
            "$ship",
            DebugText("Processing ship"),
            in_="$ships",
            counter="$i",
            reverse=True,
        )
        xml = str(node)
        self.assertIn('name="$ship"', xml)
        self.assertIn('in="$ships"', xml)
        self.assertIn('counter="$i"', xml)
        self.assertIn('reverse="true"', xml)

    def test_do_for_each_without_optional_params(self) -> None:
        """DoForEach works without counter and reverse."""
        node = DoForEach("$item", DebugText("test"), in_="$items")
        xml = str(node)
        self.assertNotIn('counter=', xml)
        self.assertNotIn('reverse=', xml)

    def test_break_renders_self_closing(self) -> None:
        """Break renders as self-closing tag."""
        self.assertEqual(str(Break()), '<break/>')

    def test_continue_renders_self_closing(self) -> None:
        """Continue renders as self-closing tag."""
        self.assertEqual(str(Continue()), '<continue/>')


class CueActionTests(unittest.TestCase):
    """Tests for cue-related actions."""

    def test_signal_cue_action_renders_with_param(self) -> None:
        """SignalCueAction renders with cue and optional param."""
        node = SignalCueAction("ProcessTrade", param="$tradeData")
        xml = str(node)
        self.assertIn('cue="ProcessTrade"', xml)
        self.assertIn('param="$tradeData"', xml)

    def test_signal_cue_action_without_param(self) -> None:
        """SignalCueAction works without param."""
        node = SignalCueAction("Ready")
        xml = str(node)
        self.assertIn('cue="Ready"', xml)
        self.assertNotIn('param=', xml)

    def test_signal_cue_instantly_renders_correctly(self) -> None:
        """SignalCueInstantly renders with cue and param."""
        node = SignalCueInstantly("NextCue", param=PathExpr.of("player", "age"))
        self.assertEqual(
            str(node),
            '<signal_cue_instantly cue="NextCue" param="player.age"/>',
        )

    def test_cancel_cue_renders_correctly(self) -> None:
        """CancelCue renders with cue attribute."""
        node = CancelCue("ProcessingLoop")
        self.assertEqual(str(node), '<cancel_cue cue="ProcessingLoop"/>')


class OrderActionTests(unittest.TestCase):
    """Tests for order management actions."""

    def test_create_order_renders_with_params(self) -> None:
        """CreateOrder renders with object, id, params, and immediate."""
        node = MDCreateOrder(
            Param("home", value="$homeSector"),
            Param("maxbuy", value=5),
            object="$ship",
            id=TextExpr.quote("GalaxyTraderMK3"),
            immediate=True,
        )
        xml = str(node)
        self.assertIn('<create_order', xml)
        self.assertIn('object="$ship"', xml)
        self.assertIn("id=\"'GalaxyTraderMK3'\"", xml)
        self.assertIn('immediate="true"', xml)
        self.assertIn('<param name="home"', xml)
        self.assertIn('<param name="maxbuy"', xml)

    def test_create_order_without_immediate(self) -> None:
        """CreateOrder works without immediate flag."""
        from x4md import CreateOrder
        node = CreateOrder(object="$ship", id=TextExpr.quote("Trade"))
        xml = str(node)
        self.assertNotIn('immediate=', xml)

    def test_cancel_order_renders_correctly(self) -> None:
        """CancelOrder renders with object attribute."""
        node = CancelOrder(object="$ship")
        self.assertEqual(str(node), '<cancel_order object="$ship"/>')

    def test_cancel_all_orders_renders_correctly(self) -> None:
        """CancelAllOrders renders with object attribute."""
        node = CancelAllOrders(object="$ship")
        self.assertEqual(str(node), '<cancel_all_orders object="$ship"/>')


class UIActionTests(unittest.TestCase):
    """Tests for UI and notification actions."""

    def test_write_to_logbook_renders_with_all_params(self) -> None:
        """WriteToLogbook renders with all optional parameters."""
        node = WriteToLogbook(
            category="upkeep",
            title=TextExpr.quote("Trade Complete"),
            text=TextExpr.quote("Profit: 1000Cr"),
            interaction="$ship",
            money=MoneyExpr.of(1000),
        )
        xml = str(node)
        self.assertIn('category="upkeep"', xml)
        self.assertIn("title=\"'Trade Complete'\"", xml)
        self.assertIn("text=\"'Profit: 1000Cr'\"", xml)
        self.assertIn('interaction="$ship"', xml)
        self.assertIn('money="1000Cr"', xml)

    def test_write_to_logbook_with_minimal_params(self) -> None:
        """WriteToLogbook works with only required params."""
        node = WriteToLogbook(category="tips", title=TextExpr.quote("Tip"))
        xml = str(node)
        self.assertIn('category="tips"', xml)
        self.assertNotIn('text=', xml)
        self.assertNotIn('interaction=', xml)

    def test_show_notification_renders_correctly(self) -> None:
        """ShowNotification renders with text and optional params."""
        node = ShowNotification(
            text=TextExpr.quote("Trade completed"),
            caption=TextExpr.quote("GalaxyTrader"),
            sound="notification_generic",
            timeout="5s",
        )
        xml = str(node)
        self.assertIn("text=\"'Trade completed'\"", xml)
        self.assertIn("caption=\"'GalaxyTrader'\"", xml)
        self.assertIn('sound="notification_generic"', xml)
        self.assertIn('timeout="5s"', xml)


class MiscActionTests(unittest.TestCase):
    """Tests for miscellaneous actions."""

    def test_set_object_name_renders_correctly(self) -> None:
        """SetObjectName renders with object and name."""
        node = SetObjectName(object="$ship", name=TextExpr.quote("Trader-1"))
        xml = str(node)
        self.assertIn('object="$ship"', xml)
        self.assertIn("name=\"'Trader-1'\"", xml)

    def test_raise_lua_event_renders_with_param(self) -> None:
        """RaiseLuaEvent renders with name and optional param."""
        node = RaiseLuaEvent(name=TextExpr.quote("GT_TradeComplete"), param="$tradeData")
        xml = str(node)
        self.assertIn("name=\"'GT_TradeComplete'\"", xml)
        self.assertIn('param="$tradeData"', xml)

    def test_raise_lua_event_without_param(self) -> None:
        """RaiseLuaEvent works without param."""
        node = RaiseLuaEvent(name=TextExpr.quote("GT_Init"))
        xml = str(node)
        self.assertNotIn('param=', xml)

    def test_run_actions_renders_correctly(self) -> None:
        """RunActions renders with ref and params."""
        node = RunActions(
            "md.Test.Lib",
            Param("ship", value=PathExpr.of("this", "ship")),
            result="$ok",
        )
        xml = str(node)
        self.assertIn('ref="md.Test.Lib"', xml)
        self.assertIn('result="$ok"', xml)
        self.assertIn('<param name="ship"', xml)

    def test_signal_objects_renders_correctly(self) -> None:
        """SignalObjects renders with all parameters."""
        node = SignalObjects(
            PathExpr.of("player", "galaxy"),
            TextExpr.quote("GT_Test"),
            param2=TableExpr.of(TableEntry("Ship", "$ship")),
            delay="1ms",
        )
        xml = str(node)
        self.assertIn('object="player.galaxy"', xml)
        self.assertIn("param=\"'GT_Test'\"", xml)
        self.assertIn('param2="table[$Ship = $ship]"', xml)
        self.assertIn('delay="1ms"', xml)


if __name__ == "__main__":
    unittest.main()
