"""Whole-document schema conformance tests.

Where ``test_xsd_contract.py`` asserts per-class properties at the
element level, this module asserts that *entire rendered documents*
validate against ``md.xsd`` and ``aiscripts.xsd``. That catches
structural bugs the per-class tests cannot see - in particular,
ordering constraints expressed as ``xs:sequence`` under the root
element.

The "sibling/child" bug in ``AIScript`` that took the previous session
to find would have been caught here immediately: the bad version of
``AIScript`` nested ``<interrupts>`` and ``<actions>`` under ``<order>``
and the schema would have rejected the output with *Unexpected child
with tag 'interrupts' at position 1*.
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

import pytest
import xmlschema

from x4md import (
    AIScript,
    Actions,
    AppendToList,
    Attention,
    CheckValue,
    ClearOrderFailure,
    Conditions,
    Cue,
    Cues,
    DebugText,
    DoIf,
    EventObjectAttacked,
    EventPlayerCreated,
    Handler,
    Interrupts,
    MDScript,
    MoveTo,
    Order,
    PathExpr,
    Resume,
    SetOrderSyncpointReached,
    SetValue,
    TextExpr,
    Wait,
    WriteToLogbook,
)

from xsd_support import ai_schema, md_schema


def _validate(schema: xmlschema.XMLSchema11, xml_text: str) -> list[xmlschema.XMLSchemaValidationError]:
    """Return all schema violations found in ``xml_text``."""

    return list(schema.iter_errors(xml_text))


def _format_errors(errors: list[xmlschema.XMLSchemaValidationError]) -> str:
    return "\n".join(f"  - {e.reason}" for e in errors[:10])


# Sample MD document -----------------------------------------------------------


def _sample_md_document() -> str:
    """Build a compact MD script that exercises common node types."""

    doc = MDScript(
        "GalaxyProtectorConformanceDemo",
        Cues(
            Cue(
                "InitPlayerReady",
                Conditions(EventPlayerCreated()),
                Actions(
                    SetValue("$gp", exact="table[]"),
                    DebugText(TextExpr.quote("player ready")),
                    WriteToLogbook(
                        category="general",
                        title=TextExpr.quote("Galaxy Protector"),
                        text=TextExpr.quote("Initialized"),
                    ),
                ),
            ),
            Cue(
                "PollForDistress",
                Conditions(CheckValue("player.ship? and player.ship != null")),
                Actions(
                    DoIf(
                        "player.ship.owner == faction.player",
                        AppendToList("$gp.$log", exact=TextExpr.quote("tick")),
                    )
                ),
                checkinterval="5s",
            ),
            Cue(
                "OnPlayerShipAttacked",
                Conditions(EventObjectAttacked(object="player.ship")),
                Actions(DebugText(TextExpr.quote("attacked"))),
            ),
        ),
    )
    return str(doc)


# Sample AI script --------------------------------------------------------------


def _sample_ai_document() -> str:
    """Build a compact AI script that exercises the full aiscript sequence.

    This exercises the portion of ``aiscripts.xsd`` that the previous
    structural bug lived in: the ordering of ``<order>``, ``<interrupts>``,
    ``<actions>``, ``<attention>`` as siblings under ``<aiscript>``.
    """

    script = AIScript(
        "order.conformance.demo",
        Order(
            "ConformanceOrder",
            Interrupts(
                Handler(
                    Conditions(EventObjectAttacked(object="player.ship")),
                    Actions(
                        ClearOrderFailure(),
                        Resume("poll"),
                    ),
                )
            ),
            SetOrderSyncpointReached(),
            MoveTo(
                object=PathExpr.of("this", "ship"),
                destination=PathExpr.of("$target"),
            ),
            Wait(max="5s"),
            Attention(Actions(Wait(max="1s")), min="unknown"),
            name=TextExpr.quote("Conformance"),
            description=TextExpr.quote("Demo order"),
            category="combat",
            infinite=True,
        ),
    )
    return str(script)


# Tests ------------------------------------------------------------------------


def test_sample_md_document_validates_against_md_xsd() -> None:
    """A complete MD script built from common x4md nodes must validate."""

    xml = _sample_md_document()
    errors = _validate(md_schema(), xml)
    assert not errors, (
        "Sample MD document failed md.xsd validation:\n"
        + _format_errors(errors)
        + "\n\nDocument:\n"
        + xml
    )


def test_sample_ai_document_validates_against_aiscripts_xsd() -> None:
    """A complete AI script with the full sequence must validate.

    This is the document-level regression test for the sibling/child
    bug: if ``AIScript`` ever goes back to nesting ``<interrupts>`` or
    ``<actions>`` inside ``<order>``, the schema will report
    *Unexpected child with tag 'interrupts' at position 1*.
    """

    xml = _sample_ai_document()
    errors = _validate(ai_schema(), xml)
    assert not errors, (
        "Sample AI document failed aiscripts.xsd validation:\n"
        + _format_errors(errors)
        + "\n\nDocument:\n"
        + xml
    )


def test_aiscript_child_ordering_is_enforced_by_schema() -> None:
    """Document-level regression: reordering order/interrupts/actions fails.

    We synthesize a broken document where ``<interrupts>`` is moved
    *before* ``<order>``, confirming that the schema does reject the
    structural bug. If this test stops rejecting the bad document, the
    schema has been weakened and the conformance tests above lose their
    value.
    """

    good = _sample_ai_document()
    root = ET.fromstring(good)
    order_elem = root.find("order")
    interrupts_elem = root.find("interrupts")
    assert order_elem is not None and interrupts_elem is not None
    root.remove(order_elem)
    root.remove(interrupts_elem)
    root.insert(0, interrupts_elem)
    root.insert(1, order_elem)

    broken = ET.tostring(root, encoding="unicode")
    errors = _validate(ai_schema(), broken)
    assert errors, (
        "Schema accepted a reordered AI script with <interrupts> before "
        "<order>. Without this check the document-level conformance "
        "tests cannot detect ordering regressions."
    )
