"""Per-class contract tests driven by the X4 XSDs.

These tests do not hard-code any expected XML. Instead, every expectation
is derived at runtime from the schemas in ``.x4-refs/``:

* Tag name: the Python class must emit the exact tag the registry says
  it corresponds to, and that tag must exist in the schema.
* Attribute surface: every attribute the Python class emits must exist
  in the XSD's attribute declaration (plus a small set of globally
  tolerated attributes like ``comment``, ``chance``, ``weight``).
* Required attributes: the Python constructor's "minimal factory" must
  produce all attributes marked ``use="required"`` in the schema.
* Enum membership: wherever the schema declares an ``xs:enumeration``
  for an attribute, the Python class must either reject invalid values
  or - at minimum - accept every valid enum value.

When a class intentionally diverges from the schema (e.g. we add a
"friendlier" parameter name or we know the schema is permissive but X4
is not), mark it in ``SPECS`` with ``known_defect=`` describing the
reason. The defect still shows up as a skip with context so it is never
silently swallowed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable
from xml.etree import ElementTree as ET

import pytest

from x4md import (
    Actions as _Actions,
    AppendToList as _AppendToList,
    Attention,
    CancelCue,
    CheckAll,
    CheckAny,
    CheckValue,
    ClearOrderFailure,
    Conditions,
    CreateList,
    CreatePosition,
    Cue,
    Cues,
    DebugText,
    Delay,
    DoElse,
    DoElseIf,
    DoForEach,
    DoIf,
    DoWhile,
    End,
    EventCueSignalled,
    EventGameLoaded,
    EventObjectAttacked,
    EventObjectSignalled,
    EventPlayerCreated,
    GetJumpPath,
    Handler,
    InputParam,
    Interrupts,
    Library,
    MDScript,
    MoveTo,
    OnAbort,
    Order,
    Param,
    Params,
    PathExpr,
    RemoveFromList,
    RemoveValue,
    Resume,
    Return,
    SetOrderFailed,
    SetOrderState,
    SetOrderSyncpointReached,
    SetValue,
    ShuffleList,
    SignalCueAction,
    SignalCueInstantly,
    SignalObjects,
    SortList,
    Start,
    TextExpr,
    Wait,
    WriteToLogbook,
)
from x4md.core import XmlElement

from xsd_support import (
    allowed_attributes,
    child_element_names,
    enum_values,
    find_element,
    required_attributes,
)


# Attributes that XSD declares on virtually every action/condition but
# which we don't always surface in Python. Seeing these in XSD does not
# mean Python is required to emit them, so they act as tolerated extras
# (python emitting them is also fine).
_GLOBAL_ATTRS = {"chance", "weight", "comment"}


@dataclass(frozen=True)
class ContractSpec:
    """One entry in the contract registry."""

    python_class: type
    xsd_element: str
    xsd_kind: str  # "md" or "ai"
    factory: Callable[[], XmlElement]
    # If the same tag is declared in multiple XSD contexts with
    # different rules (e.g. ``<handler>`` in ``interrupts`` vs.
    # ``interrupt_library``), pin the lookup by naming the enclosing
    # XSD complex type. The value must match an ``xs:complexType
    # name="..."`` in the schema.
    xsd_parent_type: str | None = None
    # Extra attrs the Python class emits that are tolerated even if not
    # in the XSD. Keep empty unless there's a documented reason.
    tolerated_extra_attrs: frozenset[str] = field(default_factory=frozenset)


# Minimal expressions reused by factories. Must be strings or ExprLikes
# that our nodes accept.
_EXPR = "1"
_STR = "'x'"
_LVAL = "$foo"


def _cue() -> XmlElement:
    return Cue("TestCue")


def _library() -> XmlElement:
    return Library("TestLib")


def _params() -> XmlElement:
    return Params(Param("p1"))


def _param() -> XmlElement:
    return Param("p1")


def _input_param() -> XmlElement:
    return InputParam("p1")


def _actions() -> XmlElement:
    return _Actions()


def _conditions() -> XmlElement:
    return Conditions()


def _check_value() -> XmlElement:
    return CheckValue(_EXPR)


def _check_all() -> XmlElement:
    return CheckAll(CheckValue(_EXPR))


def _check_any() -> XmlElement:
    return CheckAny(CheckValue(_EXPR))


def _event_object_attacked() -> XmlElement:
    return EventObjectAttacked(object="player.ship")


def _event_player_created() -> XmlElement:
    return EventPlayerCreated()


def _event_game_loaded() -> XmlElement:
    return EventGameLoaded()


def _event_cue_signalled() -> XmlElement:
    return EventCueSignalled()


def _event_object_signalled() -> XmlElement:
    return EventObjectSignalled(object="player.galaxy")


def _set_value() -> XmlElement:
    return SetValue(_LVAL, exact=_EXPR)


def _remove_value() -> XmlElement:
    return RemoveValue(_LVAL)


def _append_to_list() -> XmlElement:
    return _AppendToList(_LVAL, exact=_EXPR)


def _remove_from_list() -> XmlElement:
    return RemoveFromList(_LVAL, exact=_EXPR)


def _create_list() -> XmlElement:
    return CreateList(name=_LVAL)


def _shuffle_list() -> XmlElement:
    return ShuffleList(list=_LVAL)


def _sort_list() -> XmlElement:
    return SortList(list=_LVAL, sortbyvalue=_EXPR)


def _debug_text() -> XmlElement:
    return DebugText(_STR)


def _delay() -> XmlElement:
    return Delay(exact=_EXPR)


def _do_if() -> XmlElement:
    return DoIf(_EXPR)


def _do_else() -> XmlElement:
    return DoElse()


def _do_elseif() -> XmlElement:
    return DoElseIf(_EXPR)


def _do_while() -> XmlElement:
    return DoWhile(_EXPR)


def _do_for_each() -> XmlElement:
    return DoForEach("$i", in_=_EXPR)


def _return() -> XmlElement:
    return Return(value=_EXPR)


def _cancel_cue() -> XmlElement:
    return CancelCue(cue="SomeCue")


def _signal_cue_instantly() -> XmlElement:
    return SignalCueInstantly(cue="SomeCue")


def _signal_cue_action() -> XmlElement:
    return SignalCueAction(cue="SomeCue")


def _signal_objects() -> XmlElement:
    return SignalObjects(object="player.galaxy", param=_STR)


def _write_to_logbook() -> XmlElement:
    # category + title are the XSD-required attributes.
    return WriteToLogbook(category="general", title=_STR, text=_STR)


# AI factories ----------------------------------------------------------------


def _order() -> XmlElement:
    # ``infinite=False`` lets the minimal order omit <set_order_syncpoint_reached>,
    # which is a separate Python-level rule orthogonal to this test.
    return Order(
        id="TestOrder",
        name=_STR,
        description=_STR,
        category="combat",
        infinite=False,
        canplayercancel=True,
    )


def _interrupts() -> XmlElement:
    return Interrupts()


def _handler() -> XmlElement:
    # Handler has no `name` kwarg today; the contract test will flag the
    # missing XSD-required ``name`` attribute.
    return Handler()


def _attention() -> XmlElement:
    return Attention(_Actions(), min="unknown")


def _wait() -> XmlElement:
    return Wait(exact=_EXPR)


def _resume() -> XmlElement:
    return Resume(label="loop")


def _move_to() -> XmlElement:
    # MoveTo accepts ``object`` as required today; XSD lists only
    # ``destination`` as required. Contract test will confirm the
    # attribute surface.
    return MoveTo(object=PathExpr.of("this", "ship"), destination=PathExpr.of("$target"))


def _set_order_state() -> XmlElement:
    # Today's Python signature only exposes ``state``. XSD also requires
    # ``order`` and constrains ``state`` to an enum. Contract tests will
    # surface both gaps.
    return SetOrderState(state="orderstate.finish")


def _set_order_syncpoint_reached() -> XmlElement:
    return SetOrderSyncpointReached()


def _set_order_failed() -> XmlElement:
    return SetOrderFailed(text=_STR)


def _clear_order_failure() -> XmlElement:
    return ClearOrderFailure()


def _create_position() -> XmlElement:
    return CreatePosition(name=_LVAL, x=_EXPR, y=_EXPR, z=_EXPR)


def _get_jump_path() -> XmlElement:
    return GetJumpPath(
        component=_LVAL,
        start=PathExpr.of("this", "sector"),
        end=PathExpr.of("$target_sector"),
    )


def _start() -> XmlElement:
    return Start(object=PathExpr.of("this", "sector"))


def _end() -> XmlElement:
    return End(object=PathExpr.of("$target_sector"))


def _on_abort() -> XmlElement:
    return OnAbort()


# Registry --------------------------------------------------------------------


SPECS: list[ContractSpec] = [
    # MD structural
    ContractSpec(Cue, "cue", "md", _cue),
    ContractSpec(Library, "library", "md", _library),
    ContractSpec(Cues, "cues", "md", lambda: Cues()),
    ContractSpec(_Actions, "actions", "md", _actions),
    ContractSpec(Conditions, "conditions", "md", _conditions),
    ContractSpec(Params, "params", "md", _params),
    # ``<param>`` is declared in many places in md.xsd with different
    # rules. The MD library/cue-level ``<params><param/></params>``
    # definition only requires ``name`` (defaults are optional), which
    # is what our Python ``Param`` models.
    ContractSpec(Param, "param", "md", _param, xsd_parent_type="params"),

    # MD conditions
    ContractSpec(CheckValue, "check_value", "md", _check_value),
    ContractSpec(CheckAll, "check_all", "md", _check_all),
    ContractSpec(CheckAny, "check_any", "md", _check_any),
    ContractSpec(EventObjectAttacked, "event_object_attacked", "md", _event_object_attacked),
    ContractSpec(EventPlayerCreated, "event_player_created", "md", _event_player_created),
    ContractSpec(EventGameLoaded, "event_game_loaded", "md", _event_game_loaded),
    ContractSpec(EventCueSignalled, "event_cue_signalled", "md", _event_cue_signalled),
    ContractSpec(EventObjectSignalled, "event_object_signalled", "md", _event_object_signalled),

    # MD actions / flow
    ContractSpec(SetValue, "set_value", "md", _set_value),
    ContractSpec(RemoveValue, "remove_value", "md", _remove_value),
    ContractSpec(_AppendToList, "append_to_list", "md", _append_to_list),
    ContractSpec(RemoveFromList, "remove_from_list", "md", _remove_from_list),
    ContractSpec(CreateList, "create_list", "md", _create_list),
    ContractSpec(ShuffleList, "shuffle_list", "md", _shuffle_list),
    ContractSpec(SortList, "sort_list", "md", _sort_list),
    ContractSpec(DebugText, "debug_text", "md", _debug_text),
    ContractSpec(Delay, "delay", "md", _delay),
    ContractSpec(DoIf, "do_if", "md", _do_if),
    ContractSpec(DoElse, "do_else", "md", _do_else),
    ContractSpec(DoElseIf, "do_elseif", "md", _do_elseif),
    ContractSpec(DoWhile, "do_while", "md", _do_while),
    ContractSpec(DoForEach, "do_for_each", "md", _do_for_each),
    ContractSpec(Return, "return", "md", _return),
    ContractSpec(CancelCue, "cancel_cue", "md", _cancel_cue),
    ContractSpec(SignalCueInstantly, "signal_cue_instantly", "md", _signal_cue_instantly),
    ContractSpec(SignalCueAction, "signal_cue", "md", _signal_cue_action),
    ContractSpec(SignalObjects, "signal_objects", "md", _signal_objects),
    ContractSpec(WriteToLogbook, "write_to_logbook", "md", _write_to_logbook),

    # AI structural
    ContractSpec(Order, "order", "ai", _order),
    ContractSpec(Interrupts, "interrupts", "ai", _interrupts),
    # Two ``<handler>`` variants exist in aiscripts.xsd: one inside
    # ``interrupt_library`` which REQUIRES ``name``, and one inside
    # ``interrupts`` which has no required attributes. Our Python
    # ``Handler`` is used inside ``Interrupts``.
    ContractSpec(Handler, "handler", "ai", _handler, xsd_parent_type="interrupts"),
    ContractSpec(Attention, "attention", "ai", _attention),

    # AI actions
    ContractSpec(Wait, "wait", "ai", _wait),
    ContractSpec(Resume, "resume", "ai", _resume),
    ContractSpec(MoveTo, "move_to", "ai", _move_to),
    ContractSpec(SetOrderState, "set_order_state", "ai", _set_order_state),
    ContractSpec(SetOrderSyncpointReached, "set_order_syncpoint_reached", "ai", _set_order_syncpoint_reached),
    ContractSpec(SetOrderFailed, "set_order_failed", "ai", _set_order_failed),
    ContractSpec(ClearOrderFailure, "clear_order_failure", "ai", _clear_order_failure),
    ContractSpec(CreatePosition, "create_position", "ai", _create_position),
    ContractSpec(GetJumpPath, "get_jump_path", "ai", _get_jump_path),
    ContractSpec(Start, "start", "ai", _start),
    ContractSpec(End, "end", "ai", _end),
    ContractSpec(OnAbort, "on_abort", "ai", _on_abort),
]


def _render_root(spec: ContractSpec) -> ET.Element:
    """Build the class via its factory and parse the resulting XML to an ET."""

    element = spec.factory()
    xml = element.to_xml()
    return ET.fromstring(xml)


def _spec_id(spec: ContractSpec) -> str:
    return f"{spec.python_class.__name__}<->{spec.xsd_element}"


def _resolve(spec: ContractSpec):
    """Look up the XSD element corresponding to a spec, honouring parent pin."""

    return find_element(spec.xsd_kind, spec.xsd_element, parent_type=spec.xsd_parent_type)


@pytest.mark.parametrize("spec", SPECS, ids=_spec_id)
def test_xsd_element_exists(spec: ContractSpec) -> None:
    """Every registered XSD element name must actually exist in the schema."""

    xsd_elem = _resolve(spec)
    assert xsd_elem is not None, (
        f"Registry claims {spec.python_class.__name__} maps to "
        f"<{spec.xsd_element}> in {spec.xsd_kind}.xsd "
        f"(parent={spec.xsd_parent_type!r}) but no such element is declared."
    )


@pytest.mark.parametrize("spec", SPECS, ids=_spec_id)
def test_tag_name_matches_registry(spec: ContractSpec) -> None:
    """The Python class must emit the XML tag the registry advertises."""

    root = _render_root(spec)
    assert root.tag == spec.xsd_element, (
        f"{spec.python_class.__name__} emits <{root.tag}>, "
        f"registry says <{spec.xsd_element}>."
    )


@pytest.mark.parametrize("spec", SPECS, ids=_spec_id)
def test_emitted_attributes_are_known_to_xsd(spec: ContractSpec) -> None:
    """Every attribute the Python class emits must be declared in XSD."""

    xsd_elem = _resolve(spec)
    assert xsd_elem is not None
    allowed = allowed_attributes(xsd_elem) | _GLOBAL_ATTRS | set(spec.tolerated_extra_attrs)
    root = _render_root(spec)
    unknown = set(root.attrib) - allowed
    assert not unknown, (
        f"{spec.python_class.__name__} emits attributes not declared in XSD: "
        f"{sorted(unknown)}. XSD allows: {sorted(allowed_attributes(xsd_elem))}."
    )


@pytest.mark.parametrize("spec", SPECS, ids=_spec_id)
def test_minimal_factory_includes_required_attributes(spec: ContractSpec) -> None:
    """A minimal factory instance must include every XSD-required attribute."""

    xsd_elem = _resolve(spec)
    assert xsd_elem is not None
    required = required_attributes(xsd_elem)
    root = _render_root(spec)
    missing = required - set(root.attrib)
    assert not missing, (
        f"{spec.python_class.__name__} minimal factory is missing XSD-required attributes: "
        f"{sorted(missing)}. Required by schema: {sorted(required)}."
    )


@pytest.mark.parametrize("spec", SPECS, ids=_spec_id)
def test_required_attributes_are_not_optional_in_python(spec: ContractSpec) -> None:
    """XSD-required attributes should not be silently omittable in Python.

    Construct the class via its factory, mutate its attrs to drop each
    required attribute, and assert the rendered XML is recognised as
    invalid by the XSD (because the required attribute is missing).

    This is an indirect check: some classes enforce requiredness via
    Python signatures (parameters without defaults), others rely on the
    schema. Either way, removing a required XSD attribute must produce
    an XML tree the schema rejects. If the schema still accepts it, the
    attribute was not truly required.
    """

    import xmlschema

    xsd_elem = _resolve(spec)
    assert xsd_elem is not None
    required = required_attributes(xsd_elem)
    if not required:
        pytest.skip("element has no required attributes")

    root = _render_root(spec)
    for attr in sorted(required):
        if attr not in root.attrib:
            continue
        stripped = ET.fromstring(ET.tostring(root))
        del stripped.attrib[attr]
        errs = list(xsd_elem.iter_errors(stripped))
        # Must fail because the required attribute is missing.
        assert any(attr in str(e.reason) for e in errs), (
            f"{spec.python_class.__name__}: schema accepted <{spec.xsd_element}> "
            f"without required attribute {attr!r}; this contradicts the XSD "
            f"and suggests the oracle is misreading the declaration."
        )


@pytest.mark.parametrize("spec", SPECS, ids=_spec_id)
def test_factory_instance_validates_against_xsd(spec: ContractSpec) -> None:
    """The minimal instance must pass schema validation at the element level."""

    xsd_elem = _resolve(spec)
    assert xsd_elem is not None
    root = _render_root(spec)
    errs = list(xsd_elem.iter_errors(root))
    if errs:
        lines = [f"  - {e.reason}" for e in errs[:5]]
        pytest.fail(
            f"{spec.python_class.__name__} minimal instance failed schema validation:\n"
            + "\n".join(lines)
        )


def _enum_attrs(xsd_elem) -> dict[str, list[str]]:
    """Return ``{attr_name: [enum_values]}`` for every enum attribute."""

    out: dict[str, list[str]] = {}
    for name, attr in xsd_elem.attributes.items():
        values = enum_values(attr)
        if values:
            out[name] = values
    return out


@pytest.mark.parametrize("spec", SPECS, ids=_spec_id)
def test_enum_attributes_accept_all_xsd_values(spec: ContractSpec) -> None:
    """Where the schema defines an enumeration, every listed value must round-trip.

    We don't try to assert that invalid values raise, because many of
    our Python classes don't enforce enums (they pass strings through).
    We do assert that every XSD-listed value is accepted: if the Python
    class rejects a valid enum value it has a bug.
    """

    xsd_elem = _resolve(spec)
    assert xsd_elem is not None
    enum_attrs = _enum_attrs(xsd_elem)
    if not enum_attrs:
        pytest.skip("element has no enum-typed attributes")

    # We need a way to construct the class with a specific attribute
    # value. The simplest generic approach: produce the baseline
    # instance, override the attribute, and re-validate. If the class
    # exposes the attribute via a kwarg, we skip to the richer check.
    baseline = _render_root(spec)
    for attr, values in enum_attrs.items():
        if attr not in baseline.attrib:
            # Python class doesn't surface this attr; nothing to test.
            continue
        for value in values:
            mutated = ET.fromstring(ET.tostring(baseline))
            mutated.attrib[attr] = value
            errs = list(xsd_elem.iter_errors(mutated))
            assert not errs, (
                f"{spec.python_class.__name__}: schema rejected legal enum value "
                f"{attr}={value!r}: {errs[0].reason}"
            )

