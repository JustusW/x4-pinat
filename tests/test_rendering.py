import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from x4md import (
    AIScript,
    AbortIf,
    Actions,
    BoolExpr,
    CheckAny,
    CheckValue,
    Conditions,
    CreateOrder,
    Cue,
    CueSignalledCue,
    Cues,
    DebugText,
    DoAll,
    DoElse,
    DoElseIf,
    DoIf,
    Dynamic,
    EnsureCounter,
    EnsureList,
    EnsurePath,
    EnsureTable,
    EventGameLoaded,
    EventObjectSignalled,
    EventPlayerCreated,
    Expr,
    GameLoadedCue,
    Goto,
    Guard,
    Handler,
    InitializeGlobalsCue,
    InputParam,
    Interrupts,
    Label,
    MDScript,
    ListExpr,
    MoneyExpr,
    Order,
    Param,
    PlayerCreatedCue,
    PathExpr,
    RequestRegistryLibrary,
    Requires,
    Resume,
    Return,
    ReturnIf,
    RunActions,
    SignalCue,
    SignalCueInstantly,
    SetValue,
    SignalObjects,
    SignalRouterCue,
    TableEntry,
    TableExpr,
    TextExpr,
    Wait,
    XmlElement,
)
from x4md.md.common import normalize_attrs


class RenderingTests(unittest.TestCase):
    def test_empty_element_renders_self_closing_tag(self) -> None:
        self.assertEqual(str(XmlElement("node")), "<node/>")

    def test_xml_element_helpers_and_error_paths(self) -> None:
        child = XmlElement("child")
        node = XmlElement("node")
        self.assertIs(node.add(child), node)
        self.assertIs(node.set(xmlns__xsi="uri", value_=1), node)
        self.assertEqual(node.attrs["xmlns:xsi"], "uri")
        self.assertEqual(node.attrs["value"], 1)

        text_node = XmlElement("text", attrs={"enabled": True}, text="a & b")
        self.assertEqual(str(text_node), '<text enabled="true">a &amp; b</text>')

        combined = XmlElement("bad", children=[XmlElement("child")], text="x")
        with self.assertRaises(ValueError):
            combined.to_xml()

        many = XmlElement.many("wrapper", [XmlElement("one"), XmlElement("two")])
        self.assertEqual(
            str(many),
            "<wrapper>\n  <one/>\n  <two/>\n</wrapper>",
        )

    def test_expression_helpers_render_expected_strings(self) -> None:
        self.assertEqual(str(TextExpr.quote("hello")), "'hello'")
        self.assertEqual(str(PathExpr.of("global", "$GT", Dynamic("ship"))), "global.$GT.{ship}")
        self.assertEqual(str(ListExpr.of(1, True, TextExpr.quote("x"))), "[1, true, 'x']")
        self.assertEqual(
            str(TableExpr.of(TableEntry("Ship", PathExpr.of("this", "ship")), TableEntry("Ready", True))),
            "table[$Ship = this.ship, $Ready = true]",
        )
        self.assertEqual(str(Expr.raw("player.age")), "player.age")
        self.assertEqual(str(BoolExpr.of(True)), "true")
        self.assertEqual(str(BoolExpr.of(False)), "false")
        self.assertEqual(str(MoneyExpr.of(42)), "42Cr")

    def test_basic_md_document_renders_expected_structure(self) -> None:
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

    def test_recipe_classes_render_expected_xml(self) -> None:
        cue = CueSignalledCue(
            "InitializeState",
            EnsureTable("global.$GT_State"),
            EnsureCounter("global.$GT_Counter", 1),
        )

        expected = """<cue name="InitializeState" instantiate="true">
  <conditions>
    <event_cue_signalled/>
  </conditions>
  <actions>
    <do_if value="not global.$GT_State?">
      <set_value name="global.$GT_State" exact="table[]"/>
    </do_if>
    <do_if value="not global.$GT_Counter?">
      <set_value name="global.$GT_Counter" exact="1"/>
    </do_if>
  </actions>
</cue>"""

        self.assertEqual(str(cue), expected)

    def test_additional_recipe_classes_render(self) -> None:
        game_loaded = GameLoadedCue("Boot", DebugText(TextExpr.quote("boot")))
        self.assertEqual(
            str(game_loaded),
            """<cue name="Boot" instantiate="true">
  <conditions>
    <event_game_loaded/>
  </conditions>
  <actions>
    <debug_text text="'boot'"/>
  </actions>
</cue>""",
        )

        player_created = PlayerCreatedCue("Start", DebugText(TextExpr.quote("start")), instantiate=False)
        self.assertEqual(player_created.attrs["instantiate"], "false")

        signal_cue = SignalCue(
            "OnTrade",
            object_expr=PathExpr.of("player", "galaxy"),
            signal_name=TextExpr.quote("GT_Trade"),
            actions=(DebugText(TextExpr.quote("handled")),),
        )
        self.assertIn("event_object_signalled", str(signal_cue))

        init_globals = InitializeGlobalsCue("Init", EnsureTable("global.$Registry"))
        self.assertIn('version="1"', str(init_globals))

        ensure_list = EnsureList("global.$Items")
        ensure_path = EnsurePath("global.$Items.$Current", PathExpr.of("this", "ship"))
        return_if = ReturnIf("$done", True)
        abort_if = AbortIf("$stop", DebugText(TextExpr.quote("stopping")))
        guard = Guard("$ok", DebugText(TextExpr.quote("yes")), else_=(DebugText(TextExpr.quote("no")),))
        guard_without_else = Guard("$ok", DebugText(TextExpr.quote("yes")))

        self.assertIn('exact="[]"', str(ensure_list))
        self.assertIn('exact="this.ship"', str(ensure_path))
        self.assertIn('<return value="true"/>', str(return_if))
        self.assertIn('<return value="false"/>', str(abort_if))
        self.assertIn("<do_else>", str(guard))
        self.assertNotIn("<do_else>", str(guard_without_else))

    def test_request_registry_library_renders(self) -> None:
        library = RequestRegistryLibrary()

        expected = """<library name="RequestRegistryAcquire" purpose="run_actions">
  <params>
    <param name="ship"/>
    <param name="traceId" default="''"/>
  </params>
  <actions>
    <do_if value="not global.$RequestRegistry?">
      <set_value name="global.$RequestRegistry" exact="table[]"/>
    </do_if>
    <set_value name="global.$RequestRegistry.{$ship}" exact="table[$TraceId = traceId]"/>
    <debug_text text="'Request registry acquired'"/>
    <return value="true"/>
  </actions>
</library>"""

        self.assertEqual(str(library), expected)

    def test_signal_router_cue_renders(self) -> None:
        cue = SignalRouterCue(
            "RouteTradeFound",
            listen_object=PathExpr.of("player", "galaxy"),
            listen_param=TextExpr.quote("GT_Trade_Found"),
            emit_object=PathExpr.of("this", "ship"),
            emit_param=TextExpr.quote("GT_Trade_Found_Local"),
            payload=TableExpr.of(TableEntry("Ship", PathExpr.of("this", "ship"))),
        )

        expected = """<cue name="RouteTradeFound" instantiate="true">
  <conditions>
    <event_object_signalled object="player.galaxy" param="'GT_Trade_Found'"/>
  </conditions>
  <actions>
    <signal_objects object="this.ship" param="'GT_Trade_Found_Local'" param2="table[$Ship = this.ship]"/>
  </actions>
</cue>"""

        self.assertEqual(str(cue), expected)

    def test_remaining_md_nodes_render(self) -> None:
        check_value = CheckValue("$ready")
        self.assertEqual(str(check_value), '<check_value value="$ready"/>')

        do_elseif = DoElseIf("$other", DebugText(TextExpr.quote("other")))
        self.assertEqual(
            str(do_elseif),
            """<do_elseif value="$other">
  <debug_text text="'other'"/>
</do_elseif>""",
        )

        do_all = DoAll("5", DebugText(TextExpr.quote("tick")), counter="$i", reverse=True)
        self.assertEqual(
            str(do_all),
            """<do_all exact="5" counter="$i" reverse="true">
  <debug_text text="'tick'"/>
</do_all>""",
        )

        signal_cue = SignalCueInstantly("NextCue", param=PathExpr.of("player", "age"))
        self.assertEqual(
            str(signal_cue),
            '<signal_cue_instantly cue="NextCue" param="player.age"/>',
        )

        param = Param("foo", default="bar")
        input_param = InputParam("class", "[class.ship]")
        self.assertEqual(str(param), '<param name="foo" default="bar"/>')
        self.assertEqual(str(input_param), '<input_param name="class" value="[class.ship]"/>')

    def test_ai_script_renders_expected_structure(self) -> None:
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

    def test_remaining_ai_nodes_render(self) -> None:
        requires = Requires(CheckValue("$ok"))
        self.assertEqual(
            str(requires),
            """<requires>
  <check_value value="$ok"/>
</requires>""",
        )

        label = Label("main_loop")
        goto = Goto("main_loop")
        self.assertEqual(str(label), '<label name="main_loop"/>')
        self.assertEqual(str(goto), '<goto label="main_loop"/>')

    def test_normalize_attrs_covers_object_passthrough(self) -> None:
        marker = object()
        attrs = normalize_attrs({"x": marker, "flag": True, "none": None})
        self.assertIs(attrs["x"], marker)
        self.assertEqual(attrs["flag"], "true")
        self.assertNotIn("none", attrs)


if __name__ == "__main__":
    unittest.main()
