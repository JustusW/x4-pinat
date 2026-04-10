import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from x4md import (
    AIScript,
    AbortIf,
    Actions,
    AppendToList,
    BoolExpr,
    Break,
    CancelAllOrders,
    CancelCue,
    CancelOrder,
    CheckAll,
    CheckAny,
    CheckValue,
    Conditions,
    Continue,
    CreateOrder,
    Cue,
    CueSignalledCue,
    Cues,
    DebugText,
    DoAll,
    DoElse,
    DoElseIf,
    DoForEach,
    DoIf,
    DoWhile,
    Dynamic,
    EnsureCounter,
    EnsureList,
    EnsurePath,
    EnsureTable,
    EventGameLoaded,
    EventGameSaved,
    EventObjectChangedZone,
    EventObjectDestroyed,
    EventObjectOrderReady,
    EventObjectSignalled,
    EventPlayerAssignedHiredActor,
    EventPlayerCreated,
    EventUITriggered,
    Expr,
    GameLoadedCue,
    Goto,
    Guard,
    Handler,
    InitializeGlobalsCue,
    InputParam,
    Interrupts,
    Label,
    ListExpr,
    MDCreateOrder,
    MDScript,
    MoneyExpr,
    Order,
    Param,
    PathExpr,
    PlayerCreatedCue,
    RaiseLuaEvent,
    RemoveFromList,
    RemoveValue,
    RequestRegistryLibrary,
    Requires,
    Resume,
    Return,
    ReturnIf,
    RunActions,
    SetObjectName,
    SetValue,
    ShowNotification,
    SignalCue,
    SignalCueAction,
    SignalCueInstantly,
    SignalObjects,
    SignalRouterCue,
    TableEntry,
    TableExpr,
    TextExpr,
    Wait,
    WriteToLogbook,
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

    def test_remove_value_renders_correctly(self) -> None:
        """RemoveValue renders with name attribute."""
        node = RemoveValue("$tempData")
        self.assertEqual(str(node), '<remove_value name="$tempData"/>')

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

    def test_cancel_cue_renders_correctly(self) -> None:
        """CancelCue renders with cue attribute."""
        node = CancelCue("ProcessingLoop")
        self.assertEqual(str(node), '<cancel_cue cue="ProcessingLoop"/>')

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

    def test_check_all_renders_with_children(self) -> None:
        """CheckAll renders conjunction of conditions."""
        node = CheckAll(
            CheckValue("$ready"),
            CheckValue("$count gt 0"),
        )
        xml = str(node)
        self.assertIn('<check_all>', xml)
        self.assertIn('<check_value value="$ready"/>', xml)
        self.assertIn('<check_value value="$count gt 0"/>', xml)
        self.assertIn('</check_all>', xml)

    def test_event_object_order_ready_renders_correctly(self) -> None:
        """EventObjectOrderReady renders with object and optional comment."""
        node = EventObjectOrderReady(object="player.galaxy", comment="Monitor orders")
        xml = str(node)
        self.assertIn('object="player.galaxy"', xml)
        self.assertIn('comment="Monitor orders"', xml)

    def test_event_object_order_ready_without_comment(self) -> None:
        """EventObjectOrderReady works without comment."""
        node = EventObjectOrderReady(object="$ship")
        xml = str(node)
        self.assertNotIn('comment=', xml)

    def test_event_object_destroyed_renders_correctly(self) -> None:
        """EventObjectDestroyed renders with object attribute."""
        node = EventObjectDestroyed(object="$targetShip")
        self.assertIn('object="$targetShip"', str(node))

    def test_event_game_saved_renders_self_closing(self) -> None:
        """EventGameSaved renders as self-closing tag."""
        self.assertEqual(str(EventGameSaved()), '<event_game_saved/>')

    def test_event_player_assigned_hired_actor_renders_self_closing(self) -> None:
        """EventPlayerAssignedHiredActor renders as self-closing tag."""
        self.assertEqual(str(EventPlayerAssignedHiredActor()), '<event_player_assigned_hired_actor/>')

    def test_event_object_changed_zone_renders_correctly(self) -> None:
        """EventObjectChangedZone renders with object attribute."""
        node = EventObjectChangedZone(object="$ship")
        self.assertIn('object="$ship"', str(node))

    def test_event_ui_triggered_renders_correctly(self) -> None:
        """EventUITriggered renders with screen and control."""
        node = EventUITriggered(screen="MapMenu", control="confirm_button")
        xml = str(node)
        self.assertIn('screen="MapMenu"', xml)
        self.assertIn('control="confirm_button"', xml)

    def test_complex_workflow_with_new_nodes(self) -> None:
        """Test complex workflow using multiple new nodes together."""
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
