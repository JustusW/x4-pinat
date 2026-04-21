"""Tests for MD condition and event nodes."""

import unittest

from x4md import (
    CheckAll,
    CheckAny,
    CheckValue,
    Conditions,
    EventCueSignalled,
    EventGameLoaded,
    EventGameSaved,
    EventObjectAttacked,
    EventObjectChangedZone,
    EventObjectDestroyed,
    EventObjectOrderReady,
    EventObjectSignalled,
    EventObjectChangedSector,
    EventPlayerAssignedHiredActor,
    EventPlayerCreated,
    MatchDistance,
    MatchDock,
    Match,
    MatchRelationTo,
    EventUITriggered,
    PathExpr,
    TextExpr,
)


class BasicConditionTests(unittest.TestCase):
    """Tests for basic condition nodes."""

    def test_check_value_renders_correctly(self) -> None:
        """CheckValue renders with value attribute."""
        node = CheckValue("$ready")
        self.assertEqual(str(node), '<check_value value="$ready"/>')

    def test_check_any_renders_with_children(self) -> None:
        """CheckAny renders disjunction of conditions."""
        node = CheckAny(
            CheckValue("$a"),
            CheckValue("$b"),
        )
        xml = str(node)
        self.assertIn('<check_any>', xml)
        self.assertIn('<check_value value="$a"/>', xml)
        self.assertIn('<check_value value="$b"/>', xml)
        self.assertIn('</check_any>', xml)

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


class GameEventTests(unittest.TestCase):
    """Tests for game lifecycle event nodes."""

    def test_event_game_loaded_renders_self_closing(self) -> None:
        """EventGameLoaded renders as self-closing tag."""
        self.assertEqual(str(EventGameLoaded()), '<event_game_loaded/>')

    def test_event_player_created_renders_self_closing(self) -> None:
        """EventPlayerCreated renders as self-closing tag."""
        self.assertEqual(str(EventPlayerCreated()), '<event_player_created/>')

    def test_event_game_saved_renders_self_closing(self) -> None:
        """EventGameSaved renders as self-closing tag."""
        self.assertEqual(str(EventGameSaved()), '<event_game_saved/>')

    def test_event_player_assigned_hired_actor_renders_self_closing(self) -> None:
        """EventPlayerAssignedHiredActor renders as self-closing tag."""
        self.assertEqual(str(EventPlayerAssignedHiredActor()), '<event_player_assigned_hired_actor/>')


class CueEventTests(unittest.TestCase):
    """Tests for cue-related event nodes."""

    def test_event_cue_signalled_renders_self_closing(self) -> None:
        """EventCueSignalled renders as self-closing tag."""
        self.assertEqual(str(EventCueSignalled()), '<event_cue_signalled/>')


class ObjectEventTests(unittest.TestCase):
    """Tests for object-related event nodes."""

    def test_event_object_signalled_renders_correctly(self) -> None:
        """EventObjectSignalled renders with object and param."""
        node = EventObjectSignalled(PathExpr.of("player", "galaxy"), param=TextExpr.quote("GT_Test"))
        xml = str(node)
        self.assertIn('object="player.galaxy"', xml)
        self.assertIn("param=\"'GT_Test'\"", xml)

    def test_event_object_attacked_renders_correctly(self) -> None:
        """EventObjectAttacked renders with object attribute."""
        node = EventObjectAttacked(object="player.galaxy")
        self.assertEqual(str(node), '<event_object_attacked object="player.galaxy"/>')

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

    def test_event_object_changed_zone_renders_correctly(self) -> None:
        """EventObjectChangedZone renders with object attribute."""
        node = EventObjectChangedZone(object="$ship")
        self.assertIn('object="$ship"', str(node))

    def test_event_object_changed_sector_renders_correctly(self) -> None:
        """EventObjectChangedSector renders with object attribute."""
        node = EventObjectChangedSector(object="this.ship")
        self.assertEqual(str(node), '<event_object_changed_sector object="this.ship"/>')


class UIEventTests(unittest.TestCase):
    """Tests for UI-related event nodes."""

    def test_event_ui_triggered_renders_correctly(self) -> None:
        """EventUITriggered renders with screen and control."""
        node = EventUITriggered(screen="MapMenu", control="confirm_button")
        xml = str(node)
        self.assertIn('screen="MapMenu"', xml)
        self.assertIn('control="confirm_button"', xml)


class MatchConditionTests(unittest.TestCase):
    """Test match conditions added in Phase 1."""

    def test_match_buyer_basic(self):
        from x4md import MatchBuyer
        xml = MatchBuyer(friend=True).to_xml()
        self.assertIn("<match_buyer", xml)
        self.assertIn('friend="true"', xml)

    def test_match_buyer_full(self):
        from x4md import MatchBuyer
        xml = MatchBuyer(
            tradepartner="$faction",
            space="$sector",
            sector="$currentSector",
            friend=True,
            neutral=False,
            enemy=False
        ).to_xml()
        self.assertIn('tradepartner="$faction"', xml)
        self.assertIn('space="$sector"', xml)
        self.assertIn('sector="$currentSector"', xml)
        self.assertIn('friend="true"', xml)
        self.assertIn('neutral="false"', xml)
        self.assertIn('enemy="false"', xml)

    def test_match_seller_basic(self):
        from x4md import MatchSeller
        xml = MatchSeller(friend=True, space="$zone").to_xml()
        self.assertIn("<match_seller", xml)
        self.assertIn('friend="true"', xml)
        self.assertIn('space="$zone"', xml)

    def test_match_seller_enemy(self):
        from x4md import MatchSeller
        xml = MatchSeller(enemy=True).to_xml()
        self.assertIn('enemy="true"', xml)

    def test_match_gate_distance_basic(self):
        from x4md import MatchGateDistance
        xml = MatchGateDistance(object="player.ship", max="3").to_xml()
        self.assertIn("<match_gate_distance", xml)
        self.assertIn('object="player.ship"', xml)
        self.assertIn('max="3"', xml)

    def test_match_distance_relation_and_dock_render_correctly(self) -> None:
        """Additional match helpers render their explicit attributes."""
        self.assertEqual(
            str(Match(owner="faction.player", class_="ship_arg_m", max=5)),
            '<match owner="faction.player" class="ship_arg_m" max="5"/>',
        )
        self.assertEqual(
            str(MatchDistance(object="player.ship", min="5km", max="20km")),
            '<match_distance object="player.ship" min="5km" max="20km"/>',
        )
        self.assertEqual(
            str(MatchDock(object="$station", state="docking")),
            '<match_dock object="$station" state="docking"/>',
        )
        self.assertEqual(
            str(MatchRelationTo(object="faction.player", comparison="ge", relation=0)),
            '<match_relation_to object="faction.player" comparison="ge" relation="0"/>',
        )

    def test_match_gate_distance_range(self):
        from x4md import MatchGateDistance
        xml = MatchGateDistance(object="$station", min="2", max="5").to_xml()
        self.assertIn('object="$station"', xml)
        self.assertIn('min="2"', xml)
        self.assertIn('max="5"', xml)


if __name__ == "__main__":
    unittest.main()
