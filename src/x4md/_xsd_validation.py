"""Render-time XSD validation for generated MD and AI XML.

The library historically emitted XML and trusted the caller to check
validity out-of-band. That trust got us burned repeatedly: `<handler>`
accepting loose actions, `<get_jump_path>` using attributes where the
schema wants children, `<goto>` surviving in the XSD gap, and so on.
The XSD-backed test layers catch those issues for classes registered
in ``tests/test_xsd_contract.py``, but they never see the ad-hoc XML
downstream extensions produce at build time.

This module plugs that gap. :func:`validate_document` takes a rendered
XML string, loads the right schema based on the root element, and
returns a list of human-readable issues. :class:`XsdValidationError`
bundles those issues into a single exception that
:meth:`x4md.MDScript.to_document` / :meth:`x4md.AIScript.to_document`
raise when called with ``validate=True``.

Design notes
------------

- **Lazy loading.** ``xmlschema`` is a test/build-only dependency and
  parsing the MD XSD takes ~10-15s. We import ``xmlschema`` inside
  :func:`_load_schema` so normal rendering still works in environments
  where the dependency is not installed (we simply refuse to validate
  instead of crashing on import).

- **Caching.** Schemas are cached per interpreter. Calling
  ``validate_document`` many times in a build only pays the parse cost
  once.

- **Known XSD gaps.** Some tags are legitimately missing from the
  shipped XSDs (most notably ``<goto>`` in ``aiscripts.xsd``) even
  though X4 itself accepts them. :data:`KNOWN_XSD_GAPS` documents each
  gap and :func:`validate_document` drops the matching schema errors so
  a strict build does not trip on them. The issues still show up in
  :func:`validate_document_raw` for anyone who wants the unfiltered
  view.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable


# Schema roots shipped by Egosoft. The ``.x4-refs`` directory is
# searched for in the first ancestor directory that contains it,
# starting from this module's location. This handles both the source
# checkout layout (``GalaxyTrader/.x4-refs``) and an installed wheel
# that vendored the XSDs alongside the package.
def _find_schema_dir() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".x4-refs"
        if candidate.is_dir():
            return candidate
    return None


_SCHEMA_DIR = _find_schema_dir()


def _schema_path(name: str) -> Path | None:
    if _SCHEMA_DIR is None:
        return None
    return _SCHEMA_DIR / name


def _schema_paths() -> dict[str, Path | None]:
    return {
        "mdscript": _schema_path("md.xsd"),
        "aiscript": _schema_path("aiscripts.xsd"),
    }


# Elements that the shipped XSDs do not declare but X4 itself accepts.
# Each entry is a tag -> human-readable justification string. The
# validator drops schema errors that reference exactly these tags so a
# well-behaved script does not fail purely because of a shipping gap in
# Egosoft's reference XSDs.
#
# Do not use this as a general-purpose escape hatch: every entry here
# is a real gap in ``.x4-refs/aiscripts.xsd`` / ``.x4-refs/md.xsd`` and
# should be removed the moment the upstream schema catches up.
KNOWN_XSD_GAPS: dict[str, str] = {
    "goto": (
        "aiscripts.xsd does not declare <goto>, but vanilla X4 AI scripts "
        "use it throughout to loop back to <label> markers inside the main "
        "<actions> block. Treated as a shipped-XSD gap rather than a "
        "library bug."
    ),
}


@dataclass(frozen=True)
class XsdValidationIssue:
    """Single XSD validation issue.

    ``reason`` carries the message ``xmlschema`` produced; ``path`` is
    the XPath-ish location of the offending element inside the rendered
    document (``None`` if ``xmlschema`` did not supply one). ``tag`` is
    the local name of the element the error is attached to, or ``None``
    if the error is document-level.
    """

    reason: str
    path: str | None
    tag: str | None

    def __str__(self) -> str:
        loc = f" at {self.path}" if self.path else ""
        return f"{self.reason}{loc}"


class XsdValidationError(Exception):
    """Raised when a rendered document fails XSD validation.

    The exception exposes :attr:`issues` so callers can iterate over
    each individual failure in addition to reading the pre-formatted
    ``str(exc)`` summary. :attr:`document` holds the XML that was
    validated so downstream build scripts can include the offending
    file in a developer-facing error report without re-rendering.
    """

    def __init__(
        self,
        issues: list[XsdValidationIssue],
        *,
        document: str,
        schema_kind: str,
    ) -> None:
        self.issues = list(issues)
        self.document = document
        self.schema_kind = schema_kind
        bullet = "\n  - "
        pretty = bullet.join(str(issue) for issue in self.issues)
        super().__init__(
            f"{len(self.issues)} XSD error(s) against "
            f"{schema_kind}.xsd:{bullet}{pretty}"
        )


@lru_cache(maxsize=None)
def _load_schema(kind: str) -> object:
    """Return the cached ``XMLSchema11`` for ``kind``.

    ``kind`` must be one of ``KNOWN_XSD_GAPS`` top-level roots (i.e.
    ``"mdscript"`` or ``"aiscript"``). The import is performed inside
    the function so missing ``xmlschema`` / missing ``.x4-refs``
    surface as :class:`RuntimeError` at the validation call site,
    never at package import.
    """

    paths = _schema_paths()
    if kind not in paths:
        raise ValueError(f"no XSD schema registered for root {kind!r}")
    path = paths[kind]
    if path is None or not path.exists():
        raise RuntimeError(
            f"XSD schema for {kind!r} is missing; cannot validate. "
            "Install .x4-refs/ alongside the package (it lives at the "
            "repository root in source checkouts)."
        )
    try:
        import xmlschema  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "xmlschema is required for render-time XSD validation "
            "(install it via `pip install xmlschema` or "
            "`pip install x4md[validate]`)."
        ) from exc
    return xmlschema.XMLSchema11(str(path))


def _detect_root_tag(document: str) -> str | None:
    """Extract the root element local-name from a rendered XML string.

    Cheap sniff - we do not build a full parse tree because the only
    signal we need is which schema to load. Returns ``None`` if the
    document does not begin with a recognisable root tag.
    """

    for line in document.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<?") or stripped.startswith("<!--"):
            continue
        if not stripped.startswith("<"):
            return None
        tag_end = stripped.find(">")
        if tag_end == -1:
            return None
        token = stripped[1:tag_end]
        # Strip attributes and self-closing slash.
        name = token.split()[0].rstrip("/")
        return name or None
    return None


def _issue_tag(error: object) -> str | None:
    """Extract the offending element's local-name from an xmlschema error."""

    tag = getattr(error, "elem", None)
    if tag is not None:
        local = getattr(tag, "tag", None)
        if isinstance(local, str):
            # ElementTree uses ``{ns}tag`` for qualified names; we only
            # ever hit unqualified tags because the X4 docs do not use
            # namespaces, but strip defensively anyway.
            return local.rsplit("}", 1)[-1]
    return None


def _error_mentions_tag(error: object, tag: str) -> bool:
    """Return True if a validation error is caused by a given local tag.

    We check both ``error.elem.tag`` and the human-readable message -
    some xmlschema errors (e.g. ``Unexpected child with tag 'goto'``)
    describe the offending tag by name in ``error.reason`` rather than
    attaching ``elem``.
    """

    if _issue_tag(error) == tag:
        return True
    reason = getattr(error, "reason", None) or str(error)
    return f"'{tag}'" in reason


def _to_issue(error: object) -> XsdValidationIssue:
    reason = getattr(error, "reason", None) or str(error)
    path = getattr(error, "path", None)
    return XsdValidationIssue(
        reason=str(reason).strip(),
        path=str(path) if path else None,
        tag=_issue_tag(error),
    )


def validate_document_raw(document: str) -> list[XsdValidationIssue]:
    """Validate a rendered XML document, returning every XSD error.

    Unlike :func:`validate_document` this does **not** filter
    :data:`KNOWN_XSD_GAPS`. Use it when you want the unvarnished
    schema feedback, e.g. for "how bad is it?" reporting.
    """

    kind = _detect_root_tag(document)
    if kind is None:
        raise ValueError(
            "Could not detect a root element; refusing to validate. "
            "Pass a fully-rendered MD or AI document."
        )
    schema = _load_schema(kind)
    return [_to_issue(err) for err in schema.iter_errors(document)]  # type: ignore[attr-defined]


def validate_document(document: str) -> list[XsdValidationIssue]:
    """Validate a rendered XML document, filtering known XSD gaps.

    This is the default entry point used by
    :meth:`MDScript.to_document` / :meth:`AIScript.to_document` when
    ``validate=True``. Entries in :data:`KNOWN_XSD_GAPS` are excluded
    so a legitimate ``<goto>`` jump does not block the build.
    """

    kind = _detect_root_tag(document)
    if kind is None:
        raise ValueError(
            "Could not detect a root element; refusing to validate. "
            "Pass a fully-rendered MD or AI document."
        )
    schema = _load_schema(kind)
    filtered: list[XsdValidationIssue] = []
    for err in schema.iter_errors(document):  # type: ignore[attr-defined]
        skip = False
        for gap_tag in KNOWN_XSD_GAPS:
            if _error_mentions_tag(err, gap_tag):
                skip = True
                break
        if skip:
            continue
        filtered.append(_to_issue(err))
    return filtered


def raise_if_invalid(
    document: str,
    *,
    include_known_gaps: bool = False,
) -> None:
    """Validate ``document`` and raise :class:`XsdValidationError` on failure.

    ``include_known_gaps=True`` makes the check strict: even the
    tags listed in :data:`KNOWN_XSD_GAPS` raise. Use it in regression
    tests that want to keep the gap list honest.
    """

    issues = (
        validate_document_raw(document) if include_known_gaps else validate_document(document)
    )
    if not issues:
        return
    kind = _detect_root_tag(document) or "unknown"
    raise XsdValidationError(issues, document=document, schema_kind=kind)


def _iter_known_gap_tags() -> Iterable[str]:
    return KNOWN_XSD_GAPS.keys()


__all__ = [
    "KNOWN_XSD_GAPS",
    "XsdValidationError",
    "XsdValidationIssue",
    "raise_if_invalid",
    "validate_document",
    "validate_document_raw",
]
