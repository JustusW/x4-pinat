"""Tests for AI-script nodes."""

import unittest
import warnings

from x4md import (
    AddWareReservation,
    AIScript,
    Actions,
    Attention,
    CheckValue,
    ClearOrderFailure,
    ClampTradeAmount,
    Conditions,
    CreateOrder,
    CreatePosition,
    CreateTradeOrder,
    EventObjectSignalled,
    GetJumpPath,
    Goto,
    Handler,
    IncludeInterruptActions,
    Interrupts,
    Label,
    Order,
    Param,
    PathExpr,
    RemoveWareReservation,
    Requires,
    Resume,
    RunScript,
    SetCommand,
    SetCommandAction,
    SetOrderFailed,
    SetOrderState,
    SetOrderSyncpointReached,
    TextExpr,
    Wait,
    X4OrderCategoryWarning,
)


class AIScriptTests(unittest.TestCase):
    """Tests for AI-script document structure."""

    def test_ai_script_renders_expected_structure(self) -> None:
        """Complete AI script renders with proper structure.

        Note: This test uses Actions (MD) with CreateOrder/Resume (AI) which is
        valid XML but creates a type mismatch. This is a known edge case where
        handlers in AI scripts use MD Actions wrapper with AI order commands.
        """
        script = AIScript(
            "order.trade.demo",
            Order(
                "DemoOrder",
                Interrupts(
                    Handler(
                        Conditions(EventObjectSignalled(PathExpr.of("this", "ship"), param=TextExpr.quote("GT_Go"))),
                        Actions(
                            CreateOrder(
                                PathExpr.of("this", "ship"),
                                TextExpr.quote("DockAndWait"),
                                Param("destination", value=PathExpr.of("this", "sector")),
                                immediate=True,
                            ),
                            Resume("main_loop"),
                        ),
                    )
                ),
                Wait(max="5s"),
                SetOrderSyncpointReached(),
                name=TextExpr.ref(20001, 1101),
                description=TextExpr.ref(20001, 1102),
                category="trade",
                infinite=True,
            ),
            version=3,
        )

        expected = """<?xml version="1.0" encoding="utf-8"?>
<aiscript name="order.trade.demo" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="aiscripts.xsd" version="3">
  <order id="DemoOrder" name="{20001, 1101}" description="{20001, 1102}" category="trade" infinite="true">
    <interrupts>
      <handler>
        <conditions>
          <event_object_signalled object="this.ship" param="'GT_Go'"/>
        </conditions>
        <actions>
          <create_order object="this.ship" id="'DockAndWait'" immediate="true">
            <param name="destination" value="this.sector"/>
          </create_order>
          <resume label="main_loop"/>
        </actions>
      </handler>
    </interrupts>
    <wait max="5s"/>
    <set_order_syncpoint_reached/>
  </order>
</aiscript>"""

        self.assertEqual(str(script), expected)


class AINodeTests(unittest.TestCase):
    """Tests for individual AI nodes."""

    def test_requires_renders_correctly(self) -> None:
        """Requires node renders with conditions."""
        requires = Requires(CheckValue("$ok"))
        self.assertEqual(
            str(requires),
            """<requires>
  <check_value value="$ok"/>
</requires>""",
        )

    def test_label_renders_correctly(self) -> None:
        """Label renders with name attribute."""
        label = Label("main_loop")
        self.assertEqual(str(label), '<label name="main_loop"/>')

    def test_goto_renders_correctly(self) -> None:
        """Goto renders with label attribute."""
        goto = Goto("main_loop")
        self.assertEqual(str(goto), '<goto label="main_loop"/>')

    def test_resume_renders_correctly(self) -> None:
        """Resume renders with label attribute."""
        resume = Resume("main_loop")
        self.assertEqual(str(resume), '<resume label="main_loop"/>')

    def test_wait_renders_with_duration(self) -> None:
        """Wait renders with time parameters."""
        wait = Wait(exact="10s")
        self.assertIn('exact="10s"', str(wait))

        wait_range = Wait(min="5s", max="10s")
        xml = str(wait_range)
        self.assertIn('min="5s"', xml)
        self.assertIn('max="10s"', xml)

    def test_command_nodes_render_raw_x4_tokens(self) -> None:
        """SetCommand helpers keep command tokens unquoted."""
        self.assertEqual(
            str(SetCommand(command="command.trade")),
            '<set_command command="command.trade"/>',
        )
        self.assertEqual(
            str(SetCommandAction(commandaction="commandaction.searchingtrades")),
            '<set_command_action commandaction="commandaction.searchingtrades"/>',
        )

    def test_order_control_nodes_render_correctly(self) -> None:
        """Order control helpers render their simple attributes."""
        self.assertEqual(
            str(ClearOrderFailure()),
            '<clear_order_failure/>',
        )
        self.assertEqual(
            str(SetOrderFailed(reason=TextExpr.quote("No route"))),
            '<set_order_failed reason="\'No route\'"/>',
        )
        self.assertEqual(
            str(SetOrderState(state="STARTED")),
            '<set_order_state state="STARTED"/>',
        )
        self.assertEqual(
            str(SetOrderSyncpointReached(value=True)),
            '<set_order_syncpoint_reached value="true"/>',
        )
        self.assertEqual(
            str(SetOrderSyncpointReached()),
            '<set_order_syncpoint_reached/>',
        )
        self.assertEqual(
            str(IncludeInterruptActions(ref="TradeAbort")),
            '<include_interrupt_actions ref="TradeAbort"/>',
        )

    def test_trade_and_attention_helpers_render_correctly(self) -> None:
        """Trading helpers render explicit attributes without quoting drift."""
        self.assertEqual(
            str(AddWareReservation(object="$station", ware="energycells", amount=100, type="buy")),
            '<add_ware_reservation object="$station" ware="energycells" amount="100" type="buy"/>',
        )
        self.assertEqual(
            str(RemoveWareReservation(object="$station", ware="energycells", type="buy")),
            '<remove_ware_reservation object="$station" ware="energycells" type="buy"/>',
        )
        self.assertEqual(
            str(CreateTradeOrder(object="this.ship", tradeoffer="$offer", amount="$amount", type="sell")),
            '<create_trade_order object="this.ship" tradeoffer="$offer" amount="$amount" type="sell"/>',
        )
        self.assertEqual(
            str(ClampTradeAmount(object="this.ship", tradeoffer="$offer", amount="$amount")),
            '<clamp_trade_amount object="this.ship" tradeoffer="$offer" amount="$amount"/>',
        )
        self.assertEqual(
            str(Attention(object="$target", min="5s", max="10s")),
            '<attention object="$target" min="5s" max="10s"/>',
        )
        self.assertEqual(
            str(CreatePosition(name="$pos", object="$station", min="1km", max="5km")),
            '<create_position name="$pos" object="$station" min="1km" max="5km"/>',
        )
        self.assertEqual(
            str(GetJumpPath(result="$path", start="this.sector", end="$targetSector")),
            '<get_jump_path result="$path" start="this.sector" end="$targetSector"/>',
        )

    def test_run_script_renders_with_params(self) -> None:
        """RunScript keeps its explicit script name and params."""
        node = RunScript(Param("station", value="$target"), name="move.tradeship")
        xml = str(node)
        self.assertIn('<run_script name="move.tradeship">', xml)
        self.assertIn('<param name="station" value="$target"/>', xml)


class InfiniteOrderValidationTests(unittest.TestCase):
    """Tests for ``Order(infinite=True)`` sync-point enforcement.

    X4 logs ``AI order '<id>' is infinite but action
    <set_order_syncpoint_reached> is missing`` and then spams the log
    with ``returned but no new order in the queue`` every tick if a
    ship enters an infinite order that never marks a sync point. The
    ``Order`` constructor validates this up-front so the broken script
    never reaches the engine.
    """

    def test_infinite_order_without_syncpoint_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            Order("QRF", Wait(max="5s"), infinite=True)
        message = str(ctx.exception)
        self.assertIn("QRF", message)
        self.assertIn("SetOrderSyncpointReached", message)

    def test_infinite_order_with_syncpoint_passes(self) -> None:
        Order(
            "QRF",
            Wait(max="5s"),
            SetOrderSyncpointReached(),
            infinite=True,
        )

    def test_infinite_order_detects_nested_syncpoint(self) -> None:
        Order(
            "QRF",
            Interrupts(
                Handler(
                    Conditions(CheckValue("$ok")),
                    Actions(SetOrderSyncpointReached()),
                )
            ),
            Wait(max="5s"),
            infinite=True,
        )

    def test_non_infinite_order_does_not_require_syncpoint(self) -> None:
        Order("QRF", Wait(max="5s"))
        Order("QRF", Wait(max="5s"), infinite=False)


class OrderCategoryWarningTests(unittest.TestCase):
    """Tests for the AI ``Order`` ``category`` XSD-alignment warning.

    The XSD ``ordercategorylookup`` enum lists a closed set of order
    categories; values outside that set (notably the common ``"fight"``
    vs. ``"combat"`` confusion) should surface as a warning so modders
    know the UI may categorise the order differently from what they
    expect. The warning is non-fatal because X4 accepts undocumented
    values at runtime today.
    """

    def test_known_categories_do_not_warn(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            for category in (
                "internal",
                "navigation",
                "combat",
                "trade",
                "mining",
                "coordination",
                "salvage",
            ):
                Order("QRF", Wait(max="5s"), category=category)
        category_warnings = [
            w for w in caught if issubclass(w.category, X4OrderCategoryWarning)
        ]
        self.assertEqual(category_warnings, [])

    def test_unknown_category_warns(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Order("QRF", Wait(max="5s"), category="fight")
        category_warnings = [
            w for w in caught if issubclass(w.category, X4OrderCategoryWarning)
        ]
        self.assertEqual(len(category_warnings), 1)
        self.assertIn("fight", str(category_warnings[0].message))
        self.assertIn("combat", str(category_warnings[0].message))

    def test_none_category_does_not_warn(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Order("QRF", Wait(max="5s"))
        category_warnings = [
            w for w in caught if issubclass(w.category, X4OrderCategoryWarning)
        ]
        self.assertEqual(category_warnings, [])


if __name__ == "__main__":
    unittest.main()
