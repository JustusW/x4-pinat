"""Typed classes for composing X4 Mission Director expressions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True, slots=True)
class Expr:
    """Base class for X4 expression objects."""

    source: str

    def __str__(self) -> str:
        return self.source

    @staticmethod
    def render(value: "ExprLike") -> str:
        if isinstance(value, Expr):
            return value.source
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    @classmethod
    def raw(cls, source: str) -> "Expr":
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
    @classmethod
    def quote(cls, text: str) -> "TextExpr":
        escaped = text.replace("\\", "\\\\").replace("'", "\\'")
        return cls(f"'{escaped}'")


class PathExpr(Expr):
    @classmethod
    def of(cls, *parts: PathPart) -> "PathExpr":
        rendered: list[str] = []
        for part in parts:
            if isinstance(part, Dynamic):
                rendered.append(part.render())
            else:
                rendered.append(part)
        return cls(".".join(rendered))


class ListExpr(Expr):
    @classmethod
    def of(cls, *values: ExprLike) -> "ListExpr":
        return cls("[" + ", ".join(Expr.render(value) for value in values) + "]")


class BoolExpr(Expr):
    @classmethod
    def of(cls, value: bool) -> "BoolExpr":
        return TRUE if value else FALSE


class MoneyExpr(Expr):
    @classmethod
    def of(cls, value: int | float, unit: str = "Cr") -> "MoneyExpr":
        return cls(f"{value}{unit}")


@dataclass(frozen=True, slots=True)
class TableEntry:
    key: str
    value: ExprLike

    def render(self) -> str:
        return f"${self.key} = {Expr.render(self.value)}"

class TableExpr(Expr):
    @classmethod
    def of(cls, *entries: TableEntry) -> "TableExpr":
        return cls("table[" + ", ".join(item.render() for item in entries) + "]")


TRUE = BoolExpr("true")
FALSE = BoolExpr("false")
NULL = Expr("null")
render_expr = Expr.render
