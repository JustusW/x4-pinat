"""Tests for AI-script nodes."""

import unittest

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


if __name__ == "__main__":
    unittest.main()
