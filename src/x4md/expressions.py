"""Typed classes for composing X4 Mission Director expressions."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import TypeAlias
import warnings


# Matches the infamous ``not $var in LIST`` precedence trap. In X4's
# expression grammar, unary ``not`` binds tighter than the binary ``in``
# operator, so ``not $asset in $list`` parses as
# ``(not $asset) in $list`` and then fails at load time with
# ``Error while parsing expression: Operator expected``. The fix is
# always to parenthesise the membership test, e.g.
# ``not ($asset in $list)``. To avoid false positives on string
# literals that happen to contain the word "not", the regex only
# triggers when the operand looks like a ``$``-prefixed X4 variable
# reference (which is what ``in`` membership tests almost always
# operate on).
_NOT_IN_PRECEDENCE_RE = re.compile(
    r"""
    (?<![A-Za-z0-9_$.])     # `not` must start on a word boundary
    not\s+                  # literal operator + whitespace
    (?!\()                  # reject already-parenthesised operands
    \$[A-Za-z_][A-Za-z0-9_.{}]*  # $variable-like operand
    \s+in\s                 # unparenthesised binary `in`
    """,
    re.VERBOSE,
)


def _warn_suspicious_expression(source: str) -> None:
    """Emit ``X4ExpressionWarning`` for well-known precedence traps.

    Only static, obviously broken patterns are flagged. The goal is to
    prevent silent ``Operator expected`` parse failures at load time
    without producing false positives on legitimate expressions.
    """

    if _NOT_IN_PRECEDENCE_RE.search(source):
        warnings.warn(
            (
                "Suspicious X4 expression: `not X in Y` parses as "
                "`(not X) in Y` due to operator precedence and "
                "triggers 'Error while parsing expression: Operator "
                f"expected' in X4. Use `not (X in Y)` instead. "
                f"Offending source: {source!r}"
            ),
            X4ExpressionWarning,
            stacklevel=3,
        )


class X4ExpressionWarning(UserWarning):
    """Warning category for suspicious X4 expression source text.

    Users who want their build to fail on these warnings can run Python
    with ``-W error::x4md.expressions.X4ExpressionWarning`` (or call
    :func:`warnings.simplefilter` from application code).
    """


@dataclass(frozen=True, slots=True)
class Expr:
    """Base class for X4 expression objects."""

    source: str

    def __str__(self) -> str:
        return self.source

    @staticmethod
    def render(value: "ExprLike") -> str:
        """Render an expression-like value into X4 source text."""

        if isinstance(value, Expr):
            rendered = value.source
        elif isinstance(value, bool):
            return "true" if value else "false"
        else:
            rendered = str(value)
        _warn_suspicious_expression(rendered)
        return rendered

    @classmethod
    def raw(cls, source: str) -> "Expr":
        """Wrap an already-formed X4 expression without modification."""

        return cls(source)


@dataclass(frozen=True, slots=True)
class Dynamic:
    """A dynamic path segment rendered as ``{name}``."""

    name: str

    def render(self) -> str:
        return "{" + self.name + "}"


PathPart: TypeAlias = str | Dynamic
ExprLike: TypeAlias = Expr | str | int | float | bool


class TextExpr(Expr):
    """Helpers for X4 text expressions.

    Use :meth:`quote` for literal string expressions and :meth:`ref` for
    t-file text references such as ``{77000, 10002}``.
    """

    @classmethod
    def quote(cls, text: str) -> "TextExpr":
        """Build a quoted string literal expression for X4."""

        escaped = text.replace("\\", "\\\\").replace("'", "\\'")
        return cls(f"'{escaped}'")

    @classmethod
    def ref(cls, page_id: int, text_id: int) -> "TextExpr":
        """Build a t-file text reference such as ``{77000, 10002}``."""

        return cls(f"{{{page_id}, {text_id}}}")


class PathExpr(Expr):
    """Helpers for X4 path expressions such as ``this.ship``."""

    @classmethod
    def of(cls, *parts: PathPart) -> "PathExpr":
        """Join path parts into one X4 path expression."""

        rendered: list[str] = []
        for part in parts:
            if isinstance(part, Dynamic):
                rendered.append(part.render())
            else:
                rendered.append(part)
        return cls(".".join(rendered))


class ListExpr(Expr):
    """Helpers for X4 list expressions such as ``[1, 2, 3]``."""

    @classmethod
    def of(cls, *values: ExprLike) -> "ListExpr":
        """Build a list expression from expression-like values."""

        return cls("[" + ", ".join(Expr.render(value) for value in values) + "]")


class BoolExpr(Expr):
    """Helpers for normalized X4 boolean expressions."""

    @classmethod
    def of(cls, value: bool) -> "BoolExpr":
        """Return the canonical shared X4 boolean expression."""

        return TRUE if value else FALSE


class MoneyExpr(Expr):
    """Helpers for X4 money literals such as ``100Cr``."""

    @classmethod
    def of(cls, value: int | float, unit: str = "Cr") -> "MoneyExpr":
        """Build a money expression using the given unit suffix."""

        return cls(f"{value}{unit}")


@dataclass(frozen=True, slots=True)
class TableEntry:
    """Single key/value entry inside a table expression."""

    key: str
    value: ExprLike

    def render(self) -> str:
        """Render this entry as X4 table assignment syntax."""
        key = self.key
        if key.startswith("$"):
            warnings.warn(
                (
                    "TableEntry key should not be prefixed with '$'; "
                    f"got {key!r}. Normalizing to avoid '$$' output."
                ),
                stacklevel=2,
            )
            key = key.lstrip("$")
        return f"${key} = {Expr.render(self.value)}"

class TableExpr(Expr):
    """Helpers for X4 table expressions."""

    @classmethod
    def of(cls, *entries: TableEntry) -> "TableExpr":
        """Build a table expression from ``TableEntry`` items."""

        return cls("table[" + ", ".join(item.render() for item in entries) + "]")


TRUE = BoolExpr("true")
FALSE = BoolExpr("false")
NULL = Expr("null")
render_expr = Expr.render
