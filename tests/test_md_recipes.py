"""Tests for MD recipe helper classes."""

import unittest

from x4md import (
    AbortIf,
    CueSignalledCue,
    DebugText,
    EnsureCounter,
    EnsureList,
    EnsurePath,
    EnsureTable,
    GameLoadedCue,
    Guard,
    InitializeGlobalsCue,
    PathExpr,
    PlayerCreatedCue,
    RequestRegistryLibrary,
    ReturnIf,
    SignalCue,
    SignalRouterCue,
    TableEntry,
    TableExpr,
    TextExpr,
)


class RecipeBasicTests(unittest.TestCase):
    """Tests for basic recipe classes."""

    def test_recipe_classes_render_expected_xml(self) -> None:
        """Recipe classes generate expected patterns."""
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
        """Additional recipe helpers render correctly."""
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


class RecipeUtilityTests(unittest.TestCase):
    """Tests for utility recipe classes."""

    def test_ensure_recipes_render_correctly(self) -> None:
        """Ensure* recipes generate proper initialization checks."""
        ensure_list = EnsureList("global.$Items")
        ensure_path = EnsurePath("global.$Items.$Current", PathExpr.of("this", "ship"))

        self.assertIn('exact="[]"', str(ensure_list))
        self.assertIn('exact="this.ship"', str(ensure_path))

    def test_return_if_renders_correctly(self) -> None:
        """ReturnIf generates conditional return."""
        return_if = ReturnIf("$done", True)
        self.assertIn('<return value="true"/>', str(return_if))

    def test_abort_if_renders_correctly(self) -> None:
        """AbortIf generates conditional return false."""
        abort_if = AbortIf("$stop", DebugText(TextExpr.quote("stopping")))
        self.assertIn('<return value="false"/>', str(abort_if))

    def test_guard_renders_with_else(self) -> None:
        """Guard generates if/else pattern."""
        guard = Guard("$ok", DebugText(TextExpr.quote("yes")), else_=(DebugText(TextExpr.quote("no")),))
        xml = str(guard)
        self.assertIn("<do_else>", xml)

    def test_guard_renders_without_else(self) -> None:
        """Guard works without else branch."""
        guard_without_else = Guard("$ok", DebugText(TextExpr.quote("yes")))
        self.assertNotIn("<do_else>", str(guard_without_else))


class RecipeLibraryTests(unittest.TestCase):
    """Tests for library recipe classes."""

    def test_request_registry_library_renders(self) -> None:
        """RequestRegistryLibrary generates complete library."""
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
        """SignalRouterCue generates signal routing pattern."""
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


if __name__ == "__main__":
    unittest.main()
