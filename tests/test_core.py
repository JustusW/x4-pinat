"""Tests for core XML and expression primitives."""

import warnings
import unittest
from unittest.mock import patch

from x4md import (
    Actions,
    CheckValue,
    Conditions,
    Cue,
    Cues,
    DoIf,
    Library,
    Params,
    Return,
    WriteToLogbook,
    BoolExpr,
    Dynamic,
    Expr,
    ListExpr,
    MoneyExpr,
    PathExpr,
    TableEntry,
    TableExpr,
    TextExpr,
    XmlElement,
)
from x4md.md.common import normalize_attrs


class XmlElementTests(unittest.TestCase):
    """Tests for XmlElement core functionality."""

    def test_empty_element_renders_self_closing_tag(self) -> None:
        """Empty element renders as self-closing tag."""
        self.assertEqual(str(XmlElement("node")), "<node/>")

    def test_xml_element_helpers_and_error_paths(self) -> None:
        """XmlElement helper methods work correctly."""
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

    def test_validate_types_checks_typed_children_and_wrappers(self) -> None:
        """validate_types handles correct children, wrappers, and warnings."""
        Conditions(CheckValue("$ready")).validate_types()
        Cue("Init", Conditions(CheckValue("$ready"))).validate_types()
        Cues(Cue("Init")).validate_types()

        bad = Params(CheckValue("$ready"))
        with self.assertRaises(TypeError):
            bad.validate_types()

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            bad.validate_types(strict=False)
        self.assertEqual(len(caught), 1)
        self.assertIn("expects children of type", str(caught[0].message))

    def test_validate_types_skips_unresolvable_or_uncheckable_annotations(self) -> None:
        """validate_types gracefully skips cases it cannot validate."""

        class UnresolvedChildren(XmlElement):
            def __init__(self, *children: "MissingType") -> None:
                super().__init__(tag="wrapper", children=list(children))

        class UncheckableChildren(XmlElement):
            def __init__(self, *children: tuple[str, ...]) -> None:
                super().__init__(tag="wrapper", children=list(children))

        class UntypedChildren(XmlElement):
            def __init__(self, *children) -> None:
                super().__init__(tag="wrapper", children=list(children))

        UnresolvedChildren(XmlElement("child")).validate_types()
        UncheckableChildren(XmlElement("child")).validate_types()
        UntypedChildren(XmlElement("child")).validate_types()

    def test_validate_types_covers_remaining_branch_paths(self) -> None:
        """validate_types covers non-XmlElement and fallback branches."""

        class WrapperWithItems(XmlElement):
            def __init__(self, *items: "MissingType") -> None:
                super().__init__(tag="wrapper", children=list(items))

        class NonModuleResolvable(XmlElement):
            __module__ = "x4md.nonexistent_module_for_test"

            def __init__(self, *children: "MissingType") -> None:
                super().__init__(tag="wrapper", children=list(children))

        class ObjectChildren(XmlElement):
            def __init__(self, *children: object) -> None:
                super().__init__(tag="wrapper", children=list(children))

        class ListChildren(XmlElement):
            def __init__(self, *children: list[int]) -> None:
                super().__init__(tag="wrapper", children=list(children))

        # Covers the no-*children-parameter recursion branch where non-XmlElement
        # children are ignored by recursive validation.
        WrapperWithItems(123, "abc").validate_types()

        # Covers module resolution fallback path when annotation cannot be resolved.
        NonModuleResolvable(XmlElement("child")).validate_types()

        # Covers typed-child loop path where child matches check_types but is not XmlElement.
        ObjectChildren(1, "x").validate_types()

        # Covers branch where get_origin is present but get_args is empty.
        with patch("x4md.core.xml.get_args", return_value=()):
            ListChildren([1, 2, 3]).validate_types()


class ExpressionTests(unittest.TestCase):
    """Tests for typed expression classes."""

    def test_expression_helpers_render_expected_strings(self) -> None:
        """Expression helpers render correct X4 syntax."""
        self.assertEqual(str(TextExpr.quote("hello")), "'hello'")
        self.assertEqual(str(TextExpr.ref(77000, 10002)), "{77000, 10002}")
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

    def test_table_entry_warns_and_normalizes_prefixed_keys(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            rendered = str(TableExpr.of(TableEntry("$Sector", "arg1")))
        self.assertEqual(rendered, "table[$Sector = arg1]")
        self.assertEqual(len(caught), 1)
        self.assertIn("should not be prefixed with '$'", str(caught[0].message))


class IdentifierValidationTests(unittest.TestCase):
    """Tests for MD cue and library name validation.

    X4 rejects cue/library names containing ``.`` (or any character
    outside ``[A-Za-z_][A-Za-z0-9_]*``) with a cryptic error message.
    The constructors validate up-front so we fail fast in Python.
    """

    def test_cue_rejects_dotted_name(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            Cue("GalacticTradeProtector.Initialize")
        self.assertIn("cue name", str(ctx.exception))

    def test_cue_rejects_empty_name(self) -> None:
        with self.assertRaises(ValueError):
            Cue("")

    def test_cue_rejects_leading_digit(self) -> None:
        with self.assertRaises(ValueError):
            Cue("1Bad")

    def test_cue_rejects_non_string_name(self) -> None:
        with self.assertRaises(ValueError):
            Cue(None)  # type: ignore[arg-type]

    def test_cue_accepts_valid_identifier(self) -> None:
        Cue("GalacticTradeProtector_Initialize")
        Cue("_underscore_ok")
        Cue("Name123")

    def test_library_rejects_dotted_name(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            Library("GalacticTradeProtector.Reactions")
        self.assertIn("library name", str(ctx.exception))

    def test_library_rejects_space_in_name(self) -> None:
        with self.assertRaises(ValueError):
            Library("Bad Name")

    def test_library_accepts_valid_identifier(self) -> None:
        Library("GalacticTradeProtector_Reactions")


class ReturnInCueValidationTests(unittest.TestCase):
    """Tests for the rule that ``<return>`` cannot appear in Cue actions.

    X4 rejects ``<return>`` outside of ``<library>`` with the error
    ``Script node 'return' is not allowed in this context.`` and then
    silently refuses to execute the cue. ``Cue`` therefore raises at
    construction time instead of emitting invalid XML.
    """

    def test_direct_return_in_cue_actions_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            Cue("Capture", Actions(Return(False)))
        self.assertIn("<return>", str(ctx.exception))

    def test_nested_return_inside_do_if_raises(self) -> None:
        with self.assertRaises(ValueError):
            Cue(
                "Capture",
                Actions(DoIf("not event.object?", Return(False))),
            )

    def test_library_may_contain_return(self) -> None:
        # Sanity: libraries are still allowed to use <return>.
        Library("Helper", Actions(Return(True)))

    def test_cue_containing_library_ignores_library_returns(self) -> None:
        # Although not semantically valid X4 nesting, the traversal
        # must stop at <library> boundaries so that legitimate
        # <return> usage inside a nested library does not trip the
        # Cue-level check. This exercises the library-skip branch.
        library = Library("Helper", Actions(Return(True)))
        Cue("Capture", library)


class LogbookCategoryValidationTests(unittest.TestCase):
    """Tests for the :class:`WriteToLogbook` category enum.

    Passing an invalid category causes X4 to log "Invalid or missing
    log category" and drop the write, so the entry never reaches the
    player's logbook. The constructor now rejects unknown categories
    up-front.
    """

    def test_singular_alert_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            WriteToLogbook(category="alert", title="'Test'")
        self.assertIn("alert", str(ctx.exception))
        self.assertIn("alerts", str(ctx.exception))

    def test_unknown_category_rejected(self) -> None:
        with self.assertRaises(ValueError):
            WriteToLogbook(category="dangerzone", title="'Test'")

    def test_all_known_categories_accepted(self) -> None:
        # ``missions`` was historically missing from x4md's allow list
        # even though ``common.xsd`` has accepted it for years; make
        # sure every XSD-sanctioned category round-trips.
        for category in ("general", "missions", "news", "upkeep", "alerts", "tips"):
            WriteToLogbook(category=category, title="'Test'")

    def test_missions_category_accepted(self) -> None:
        """The ``missions`` category used by vanilla missions must be
        accepted; regression test for a past allow-list oversight."""
        WriteToLogbook(category="missions", title="'Test'")


class LogbookInteractionValidationTests(unittest.TestCase):
    """Tests for the :class:`WriteToLogbook` ``interaction`` enum.

    X4's ``<write_to_logbook>`` element accepts an optional
    ``interaction`` attribute restricted to ``guidance``, ``showonmap``
    and ``showlocationonmap`` (``loginteractionlookup`` in
    ``common.xsd``). Unknown values cause X4 to reject the entire
    logbook entry at load time, so we reject them in Python.
    """

    def test_unknown_interaction_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            WriteToLogbook(
                category="alerts",
                title="'Test'",
                interaction="focus",
            )
        self.assertIn("interaction", str(ctx.exception))
        self.assertIn("guidance", str(ctx.exception))

    def test_all_known_interactions_accepted(self) -> None:
        for interaction in ("guidance", "showonmap", "showlocationonmap"):
            WriteToLogbook(
                category="alerts",
                title="'Test'",
                interaction=interaction,
            )

    def test_no_interaction_is_allowed(self) -> None:
        # ``interaction`` is optional; omitting it must not raise.
        WriteToLogbook(category="alerts", title="'Test'")


class CancelOrderSchemaTests(unittest.TestCase):
    """Tests for the MD ``<cancel_order>`` attribute schema.

    The element requires the ``order`` attribute (an order reference);
    using ``object`` surfaces in ``debuglog.txt`` as
    ``Required attribute 'order' is missing in <cancel_order>`` and
    aborts the enclosing cue. The helper must therefore refuse the
    legacy ``object=`` call pattern by virtue of Python's keyword-only
    argument typing.
    """

    def test_renders_order_attribute(self) -> None:
        from x4md import CancelOrder

        node = CancelOrder(order="$order")
        self.assertEqual(str(node), '<cancel_order order="$order"/>')

    def test_rejects_legacy_object_keyword(self) -> None:
        from x4md import CancelOrder

        with self.assertRaises(TypeError):
            CancelOrder(object="$ship")  # type: ignore[call-arg]

    def test_keepinloop_round_trips(self) -> None:
        from x4md import CancelOrder

        self.assertEqual(
            str(CancelOrder(order="$order", keepinloop=False)),
            '<cancel_order order="$order" keepinloop="false"/>',
        )


class ExpressionHeuristicTests(unittest.TestCase):
    """Tests for the ``not $x in $y`` precedence warning.

    X4's grammar binds unary ``not`` tighter than binary ``in``, so
    ``not $asset in $list`` fails at load time with
    ``Error while parsing expression: Operator expected``. Every time
    an expression is rendered we run a cheap regex check and warn so
    the mistake is visible at build time instead of silently breaking
    the script at runtime.
    """

    def test_warning_emitted_for_unparenthesised_not_in(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Expr.render("not $asset in $known")
        messages = [str(w.message) for w in caught]
        self.assertTrue(
            any("not X in Y" in m for m in messages),
            f"Expected precedence warning, got: {messages!r}",
        )

    def test_no_warning_when_parenthesised(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Expr.render("not ($asset in $known)")
        messages = [str(w.message) for w in caught]
        self.assertFalse(
            any("not X in Y" in m for m in messages),
            f"Did not expect precedence warning, got: {messages!r}",
        )

    def test_no_warning_for_unrelated_not_usage(self) -> None:
        """``not`` used without a later ``in`` must not trigger."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Expr.render("not $ship.exists")
        messages = [str(w.message) for w in caught]
        self.assertFalse(
            any("not X in Y" in m for m in messages),
            f"Unexpected precedence warning: {messages!r}",
        )

    def test_no_warning_for_string_literal_containing_not(self) -> None:
        """String literals such as ``'not in stock'`` must not trigger.

        The heuristic requires the operand between ``not`` and ``in``
        to look like a ``$``-prefixed variable, so plain English text
        should never false-positive.
        """
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            Expr.render("'not in stock'")
        messages = [str(w.message) for w in caught]
        self.assertFalse(
            any("not X in Y" in m for m in messages),
            f"Unexpected precedence warning for literal: {messages!r}",
        )


class UtilityTests(unittest.TestCase):
    """Tests for utility functions."""

    def test_normalize_attrs_covers_object_passthrough(self) -> None:
        """normalize_attrs handles different value types correctly."""
        marker = object()
        attrs = normalize_attrs({"x": marker, "flag": True, "none": None})
        self.assertIs(attrs["x"], marker)
        self.assertEqual(attrs["flag"], "true")
        self.assertNotIn("none", attrs)


if __name__ == "__main__":
    unittest.main()
