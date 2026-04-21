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
    Params,
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
