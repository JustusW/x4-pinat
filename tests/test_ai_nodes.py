"""Tests for AI-script nodes."""

import unittest

from x4md import (
    AIScript,
    Actions,
    CheckValue,
    Conditions,
    CreateOrder,
    EventObjectSignalled,
    Goto,
    Handler,
    Interrupts,
    Label,
    Order,
    Param,
    PathExpr,
    Requires,
    Resume,
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
                name=TextExpr.quote("Demo Order"),
                category="trade",
                infinite=True,
            ),
            version=3,
        )

        expected = """<?xml version="1.0" encoding="utf-8"?>
<aiscript name="order.trade.demo" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="aiscripts.xsd" version="3">
  <order id="DemoOrder" name="'Demo Order'" category="trade" infinite="true">
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


if __name__ == "__main__":
    unittest.main()
