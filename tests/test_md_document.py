"""Tests for MD document structure and integration."""

import unittest

from x4md import (
    Actions,
    CheckAny,
    Conditions,
    Cue,
    Cues,
    DebugText,
    DoElse,
    DoIf,
    EventGameLoaded,
    EventObjectSignalled,
    EventPlayerCreated,
    InputParam,
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

    def test_library_and_flow_nodes_render_expected_xml(self) -> None:
        """Library references and flow control render correctly."""
        node = Cue(
            "HandleSignal",
            Conditions(
                EventObjectSignalled(PathExpr.of("player", "galaxy"), param=TextExpr.quote("GT_Test"))
            ),
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
            instantiate=True,
        )

        expected = """<cue name="HandleSignal" instantiate="true">
  <conditions>
    <event_object_signalled object="player.galaxy" param="'GT_Test'"/>
  </conditions>
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
</cue>"""

        self.assertEqual(str(node), expected)


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


if __name__ == "__main__":
    unittest.main()
