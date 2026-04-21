"""Render-time XSD validation tests for MDScript/AIScript.

These tests exercise the ``validate=True`` path added to
``to_document`` and the ``validate()`` method. They also pin the
:data:`KNOWN_XSD_GAPS` contract, so a regression that silently starts
reporting ``<goto>`` as an error (or, worse, stops reporting genuine
errors) fails here instead of downstream.
"""

from __future__ import annotations

import unittest

from x4md import (
    AIScript,
    Actions,
    CheckValue,
    ClearOrderFailure,
    Conditions,
    Cue,
    Cues,
    DebugText,
    EventPlayerCreated,
    Goto,
    Handler,
    Interrupts,
    KNOWN_XSD_GAPS,
    Label,
    MDScript,
    Order,
    Resume,
    SetOrderSyncpointReached,
    SetValue,
    Wait,
    XsdValidationError,
    XsdValidationIssue,
    validate_document,
    validate_document_raw,
)


def _valid_md() -> MDScript:
    return MDScript(
        name="TestMd",
        cues=Cues(
            Cue(
                "ConfigureOnStart",
                Conditions(EventPlayerCreated()),
                Actions(
                    SetValue(name="$ready", exact=True),
                    DebugText("ready"),
                ),
            )
        ),
    )


def _valid_ai() -> AIScript:
    return AIScript(
        "order.test.valid",
        Order(
            "TestOrder",
            Interrupts(
                Handler(
                    Conditions(CheckValue("$go")),
                    ClearOrderFailure(),
                    Resume("poll"),
                )
            ),
            SetOrderSyncpointReached(),
            Label("poll"),
            Wait(max="1s"),
            Goto("poll"),
            category="combat",
            infinite=True,
        ),
    )


class RenderTimeValidationTests(unittest.TestCase):
    """``to_document(validate=True)`` must round-trip clean documents."""

    def test_valid_md_document_passes_validation(self) -> None:
        script = _valid_md()
        document = script.to_document(validate=True)
        self.assertTrue(document.startswith("<?xml"))
        self.assertEqual(script.validate(), [])

    def test_valid_ai_document_passes_validation_despite_goto(self) -> None:
        """``<goto>`` is a shipped-XSD gap, not a genuine error."""

        script = _valid_ai()
        document = script.to_document(validate=True)
        self.assertIn("<goto", document)
        self.assertEqual(script.validate(), [])

    def test_validate_returns_empty_list_for_clean_documents(self) -> None:
        self.assertEqual(_valid_md().validate(), [])
        self.assertEqual(_valid_ai().validate(), [])


class KnownXsdGapTests(unittest.TestCase):
    """``KNOWN_XSD_GAPS`` is the contract between x4md and the shipped XSDs."""

    def test_goto_is_listed_as_known_gap(self) -> None:
        self.assertIn("goto", KNOWN_XSD_GAPS)
        self.assertTrue(KNOWN_XSD_GAPS["goto"])

    def test_validate_document_filters_known_gaps(self) -> None:
        """Default ``validate_document`` drops ``<goto>`` complaints."""

        document = _valid_ai().to_document()
        filtered = validate_document(document)
        self.assertEqual(
            filtered, [], f"Expected no remaining issues, got: {filtered}"
        )

    def test_validate_document_raw_still_reports_known_gaps(self) -> None:
        """The raw variant must keep the gap list honest.

        If the upstream XSD ever starts declaring ``<goto>``,
        ``validate_document_raw`` will return zero issues on the same
        document and this test will fail - prompting us to remove the
        ``goto`` entry from :data:`KNOWN_XSD_GAPS`.
        """

        document = _valid_ai().to_document()
        raw = validate_document_raw(document)
        self.assertTrue(
            any(issue.tag == "goto" or "'goto'" in issue.reason for issue in raw),
            "validate_document_raw should surface the <goto> XSD gap; "
            "if upstream added <goto> to aiscripts.xsd, drop it from "
            "KNOWN_XSD_GAPS.",
        )


class ValidationFailureTests(unittest.TestCase):
    """Confirm ``to_document(validate=True)`` raises on genuine failures."""

    def test_aiscript_with_bogus_root_element_raises(self) -> None:
        """Synthesise a broken document directly and feed it through the
        validator; the helpers expose the same code path as
        ``to_document`` without needing a Python class that happens to
        emit bad XML."""

        broken = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<aiscript name="order.broken" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:noNamespaceSchemaLocation="aiscripts.xsd" version="1">\n'
            "  <interrupts/>\n"
            '  <order id="BrokenOrder" category="combat"/>\n'
            "</aiscript>\n"
        )
        issues = validate_document(broken)
        self.assertTrue(
            issues,
            "Interrupts-before-order must fail validation; got empty list.",
        )
        self.assertTrue(
            any("order" in str(issue).lower() or "interrupts" in str(issue).lower()
                for issue in issues),
            f"Expected order/interrupts sequence error in issues: {issues}",
        )

    def test_xsd_validation_error_exposes_structured_issues(self) -> None:
        broken = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<aiscript name="order.broken" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:noNamespaceSchemaLocation="aiscripts.xsd" version="1">\n'
            "  <interrupts/>\n"
            '  <order id="BrokenOrder" category="combat"/>\n'
            "</aiscript>\n"
        )
        from x4md._xsd_validation import raise_if_invalid

        with self.assertRaises(XsdValidationError) as ctx:
            raise_if_invalid(broken)
        err = ctx.exception
        self.assertEqual(err.schema_kind, "aiscript")
        self.assertTrue(err.issues)
        self.assertIsInstance(err.issues[0], XsdValidationIssue)
        self.assertIn("aiscript.xsd", str(err))


if __name__ == "__main__":
    unittest.main()
