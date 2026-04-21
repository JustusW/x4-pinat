"""XSD oracle helpers used by the schema-conformance and contract tests.

The two Egosoft-provided XSDs in ``.x4-refs/`` are the authoritative
description of MD and AI script structure. Loading an XSD with
``xmlschema`` is slow (~10 seconds per schema) so every loader in this
module is wrapped with ``functools.lru_cache`` to pay the cost exactly
once per test session.

Public entry points (kept deliberately small):

``md_schema()`` / ``ai_schema()``
    Return the parsed ``XMLSchema11`` objects.

``find_element(kind, name)``
    Locate the first ``XsdElement`` declaration matching ``name`` in the
    MD or AI schema, even if it lives inside an ``xs:group`` referenced
    via ``<xs:group ref=".../>``.

``required_attributes(elem)`` / ``allowed_attributes(elem)``
    Introspect attribute metadata derived straight from the schema.

``enum_values(attr)``
    Return the ``xs:enumeration`` values from the attribute's type, or
    ``None`` if the type is not an enumeration.

``child_element_names(elem)``
    Collect the tag names the schema permits as immediate children of a
    given element. Needed to assert our Python classes accept the right
    child nodes.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterable, Iterator

import xmlschema
from xmlschema import XsdElement
from xmlschema.validators import XsdGroup

_SCHEMA_DIR = Path(__file__).resolve().parents[2] / ".x4-refs"
_MD_PATH = _SCHEMA_DIR / "md.xsd"
_AI_PATH = _SCHEMA_DIR / "aiscripts.xsd"


@lru_cache(maxsize=1)
def md_schema() -> xmlschema.XMLSchema11:
    """Return the cached MD schema. First call takes ~10-15s."""
    return xmlschema.XMLSchema11(str(_MD_PATH))


@lru_cache(maxsize=1)
def ai_schema() -> xmlschema.XMLSchema11:
    """Return the cached AI-script schema. First call takes ~10-15s."""
    return xmlschema.XMLSchema11(str(_AI_PATH))


def _walk(component: object, seen: set[int]) -> Iterator[XsdElement]:
    """Recursively yield every ``XsdElement`` reachable from ``component``.

    xmlschema's built-in ``iter_components`` only walks top-level
    declarations; it does not cross ``xs:group`` boundaries that are
    referenced with ``ref=``. Most X4 action/condition elements live
    inside such groups, so we walk the schema graph ourselves.
    """

    if id(component) in seen:
        return
    seen.add(id(component))
    if isinstance(component, XsdElement):
        yield component
        if component.type is not None:
            yield from _walk(component.type, seen)
    if isinstance(component, XsdGroup):
        for particle in component:
            yield from _walk(particle, seen)
    content = getattr(component, "content", None)
    if content is not None and content is not component:
        yield from _walk(content, seen)


def _build_index(schema: xmlschema.XMLSchema11) -> dict[str, list[XsdElement]]:
    """Map every element local-name to every ``XsdElement`` that declares it."""

    seen: set[int] = set()
    index: dict[str, list[XsdElement]] = {}
    for root in schema.elements.values():
        for element in _walk(root, seen):
            name = element.local_name
            if name:
                index.setdefault(name, []).append(element)
    # Walk named groups too; some elements are only reachable that way.
    for group in schema.groups.values():
        for element in _walk(group, seen):
            name = element.local_name
            if name:
                bucket = index.setdefault(name, [])
                if element not in bucket:
                    bucket.append(element)
    return index


@lru_cache(maxsize=1)
def md_index() -> dict[str, list[XsdElement]]:
    return _build_index(md_schema())


@lru_cache(maxsize=1)
def ai_index() -> dict[str, list[XsdElement]]:
    return _build_index(ai_schema())


def find_element(
    kind: str,
    name: str,
    *,
    parent_type: str | None = None,
) -> XsdElement | None:
    """Return the first XSD element declaration matching ``name``.

    ``kind`` must be ``"md"`` or ``"ai"``. Declarations with the same
    local name can appear in multiple places with different rules
    (e.g. ``<handler>`` under ``interrupts`` has no required
    attributes, while ``<handler>`` under ``interrupt_library`` requires
    ``name``). Pass ``parent_type`` to pin the lookup to a specific
    enclosing complex-type name.
    """

    if kind not in {"md", "ai"}:
        raise ValueError(f"unknown schema kind {kind!r}")
    index = md_index() if kind == "md" else ai_index()
    bucket = index.get(name)
    if not bucket:
        return None
    if parent_type is None:
        return bucket[0]
    for candidate in bucket:
        ancestor = candidate.parent
        while ancestor is not None:
            ancestor_name = getattr(ancestor, "name", None) or getattr(ancestor, "local_name", None)
            if ancestor_name == parent_type:
                return candidate
            ancestor = getattr(ancestor, "parent", None)
    return None


def required_attributes(element: XsdElement) -> set[str]:
    return {name for name, attr in element.attributes.items() if attr.use == "required"}


def allowed_attributes(element: XsdElement) -> set[str]:
    return set(element.attributes.keys())


def enum_values(attr) -> list[str] | None:
    """Return the enumeration values for an attribute, or ``None``."""

    attr_type = attr.type
    facets = getattr(attr_type, "facets", None) or {}
    for facet in facets.values():
        values = getattr(facet, "enumeration", None)
        if values:
            return list(values)
    return None


def child_element_names(element: XsdElement) -> set[str]:
    """Collect names of elements the schema permits as immediate children."""

    children: set[str] = set()
    element_type = element.type
    if element_type is None or element_type.content is None:
        return children
    # Walk only one level; avoid recursion into grandchildren.
    for particle in _iter_direct_children(element_type.content):
        if isinstance(particle, XsdElement) and particle.local_name:
            children.add(particle.local_name)
    return children


def _iter_direct_children(node: object) -> Iterable[object]:
    """Yield top-level particles of a content model, flattening groups."""

    if isinstance(node, XsdGroup):
        for particle in node:
            if isinstance(particle, XsdGroup):
                yield from _iter_direct_children(particle)
            else:
                yield particle
    else:
        yield node
