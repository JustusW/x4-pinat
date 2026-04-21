"""Tests for MD document structure and integration."""

import unittest

from x4md import (
    Actions,
    CheckAny,
    Conditions,
    Cue,
    Cues,
    DebugText,
    Delay,
    DoElse,
    DoIf,
    EventGameLoaded,
    EventObjectSignalled,
    EventPlayerCreated,
    InputParam,
    Library,
    MDScript,
    Param,
    PathExpr,
    Return,
    RunActions,
    SetValue,
    SignalObjects,
    TableEntry,
    TableExpr,
    TextExpr,
)


class MDDocumentTests(unittest.TestCase):
    """Tests for complete MD document rendering."""

    def test_basic_md_document_renders_expected_structure(self) -> None:
        """Complete MD document renders with proper structure."""
        document = MDScript(
            name="GalaxyTraderBootstrap",
            cues=Cues(
                Cue(
                    "SystemInit",
                    Conditions(
                        CheckAny(
                            EventGameLoaded(),
                            EventPlayerCreated(),
                        )
                    ),
                    Actions(
                        SetValue(
                            "global.$GT_State",
                            exact=TableExpr.of(
                                TableEntry("Ready", True),
                                TableEntry("LastUpdate", PathExpr.of("player", "age")),
                            ),
                        ),
                        RunActions("md.GT_Libraries_General.GT_RequestStatus_Init"),
                        DebugText(TextExpr.quote("Python-generated MD initialized"), chance=100),
                    ),
                    instantiate=True,
                    version=1,
                )
            ),
        )

        expected = """<?xml version="1.0" encoding="utf-8"?>
<mdscript name="GalaxyTraderBootstrap" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="md.xsd">
  <cues>
    <cue name="SystemInit" instantiate="true" version="1">
      <conditions>
        <check_any>
          <event_game_loaded/>
          <event_player_created/>
        </check_any>
      </conditions>
      <actions>
        <set_value name="global.$GT_State" exact="table[$Ready = true, $LastUpdate = player.age]"/>
        <run_actions ref="md.GT_Libraries_General.GT_RequestStatus_Init"/>
        <debug_text text="'Python-generated MD initialized'" chance="100"/>
      </actions>
    </cue>
  </cues>
</mdscript>"""

        self.assertEqual(str(document), expected)

    def test_document_helpers_render_library_delay_and_str_consistently(self) -> None:
        """Document-level helpers render their wrapper XML correctly."""
        cue = Cue(
            "DelayedInit",
            Delay(exact="5s"),
            instantiate=True,
            comment="demo",
        )
        library = Library(
            "Demo_Library",
            Actions(DebugText(TextExpr.quote("Hello"))),
            purpose="run_actions",
        )
        document = MDScript(name="DemoDoc", cues=Cues(cue, library))

        xml = str(document)
        self.assertIn('<cue name="DelayedInit" instantiate="true" comment="demo">', xml)
        self.assertIn('<delay exact="5s"/>', xml)
        self.assertIn('<library name="Demo_Library" purpose="run_actions">', xml)
        self.assertEqual(document.to_document(), xml)

    def test_library_and_flow_nodes_render_expected_xml(self) -> None:
        """Library references and flow control render correctly.

        ``<return>`` is deliberately placed inside a ``<library>`` in
        this fixture because X4 only accepts the tag in library
        actions; ``Cue`` rejects it at construction time.
        """
        library = Library(
            "HandleSignalLib",
            Actions(
                RunActions(
                    "md.Test.Lib",
                    Param("ship", value=PathExpr.of("this", "ship")),
                    Param("traceId", value=TextExpr.quote("trace-1")),
                    result="$ok",
                ),
                DoIf(
                    "$ok",
                    SignalObjects(
                        PathExpr.of("player", "galaxy"),
                        TextExpr.quote("GT_Test_Handled"),
                        param2=TableExpr.of(TableEntry("Ship", PathExpr.of("this", "ship"))),
                        delay="1ms",
                    ),
                    DoElse(
                        Return(False),
                    ),
                ),
            ),
        )

        expected = """<library name="HandleSignalLib">
  <actions>
    <run_actions ref="md.Test.Lib" result="$ok">
      <param name="ship" value="this.ship"/>
      <param name="traceId" value="'trace-1'"/>
    </run_actions>
    <do_if value="$ok">
      <signal_objects object="player.galaxy" param="'GT_Test_Handled'" param2="table[$Ship = this.ship]" delay="1ms"/>
      <do_else>
        <return value="false"/>
      </do_else>
    </do_if>
  </actions>
</library>"""

        self.assertEqual(str(library), expected)


class ParamTests(unittest.TestCase):
    """Tests for parameter nodes."""

    def test_param_renders_with_attributes(self) -> None:
        """Param renders with various attributes."""
        param = Param("foo", default="bar")
        self.assertEqual(str(param), '<param name="foo" default="bar"/>')

    def test_input_param_renders_correctly(self) -> None:
        """InputParam renders with name and value."""
        input_param = InputParam("class", "[class.ship]")
        self.assertEqual(str(input_param), '<input_param name="class" value="[class.ship]"/>')


class ComplexWorkflowTests(unittest.TestCase):
    """Tests for complex workflows combining multiple nodes."""

    def test_complex_workflow_with_new_nodes(self) -> None:
        """Test complex workflow using multiple new nodes together."""
        from x4md import Break, Continue, DoWhile, EventGameSaved, RemoveFromList, WriteToLogbook

        cue = Cue(
            "ProcessQueue",
            Conditions(EventGameSaved()),
            Actions(
                DoWhile(
                    "global.$GT_Queue.count gt 0",
                    SetValue("$item", exact="global.$GT_Queue.{1}"),
                    RemoveFromList("global.$GT_Queue", exact="$item"),
                    DoIf(
                        "$item.$Valid",
                        WriteToLogbook(
                            category="upkeep",
                            title=TextExpr.quote("Item processed"),
                        ),
                        Continue(),
                    ),
                    Break(),
                ),
            ),
            instantiate=True,
        )
        xml = str(cue)
        self.assertIn('<event_game_saved/>', xml)
        self.assertIn('<do_while', xml)
        self.assertIn('<remove_from_list', xml)
        self.assertIn('<write_to_logbook', xml)
        self.assertIn('<continue/>', xml)
        self.assertIn('<break/>', xml)


class OnAbortMigrationTests(unittest.TestCase):
    """``OnAbort`` used to live in ``x4md.md.document``.

    ``md.xsd`` does not declare ``<on_abort>``; it is an AI-script
    element. The class was moved to :mod:`x4md.x4ai.nodes` and the
    MD-side import removed. These tests pin the migration so a future
    refactor does not silently re-introduce an unvalidatable MD cue
    child node.
    """

    def test_on_abort_no_longer_importable_from_md(self) -> None:
        from x4md import md

        self.assertFalse(
            hasattr(md, "OnAbort"),
            "OnAbort must not live in x4md.md; md.xsd has no "
            "<on_abort> element and the node belongs to x4md.x4ai.",
        )

    def test_on_abort_still_importable_from_top_level(self) -> None:
        from x4md import OnAbort
        from x4md.x4ai.types import OrderChildNode

        self.assertTrue(
            issubclass(OnAbort, OrderChildNode),
            "OnAbort should be an AI OrderChildNode, not an MD cue child.",
        )


class CuePollingAttributeTests(unittest.TestCase):
    """Tests for ``checkinterval`` / ``onfail`` on polling-only cues."""

    def test_checkinterval_renders_on_pure_check_cue(self) -> None:
        """A cue whose conditions are only non-event can poll with ``checkinterval``.

        X4's own error message for a bare ``<check_value>`` cue is
        "Found non-event condition 'check_value', event condition
        required!". The workaround documented in ``md.xsd`` is
        ``checkinterval``, which turns the cue into a polling cue.
        """

        from x4md import CheckValue

        cue = Cue(
            "AwaitPlayerShip",
            Conditions(CheckValue("player.ship? and player.ship != null")),
            checkinterval="5s",
        )
        xml = cue.to_xml()
        self.assertIn('checkinterval="5s"', xml)
        self.assertIn('<check_value value="player.ship? and player.ship != null"/>', xml)

    def test_checkinterval_with_event_condition_raises(self) -> None:
        """Mixing ``checkinterval`` with an event condition is rejected."""

        from x4md import CheckValue

        with self.assertRaises(ValueError) as ctx:
            Cue(
                "BadCue",
                Conditions(
                    EventPlayerCreated(),
                    CheckValue("player.ship?"),
                ),
                checkinterval="5s",
            )
        msg = str(ctx.exception)
        self.assertIn("checkinterval", msg)
        self.assertIn("event condition", msg)

    def test_onfail_with_event_condition_raises(self) -> None:
        """Mixing ``onfail`` with an event condition is also rejected."""

        with self.assertRaises(ValueError):
            Cue(
                "BadCue",
                Conditions(EventPlayerCreated()),
                onfail="cancel",
            )


if __name__ == "__main__":
    unittest.main()
