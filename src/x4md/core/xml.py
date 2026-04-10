"""Generic XML tree primitives."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Iterable, get_args, get_origin
from xml.sax.saxutils import escape

from x4md.expressions import Expr


def _render_attribute_value(value: object) -> str:
    if isinstance(value, Expr):
        value = value.source
    elif isinstance(value, bool):
        value = "true" if value else "false"
    return escape(str(value), {'"': "&quot;"})


@dataclass(slots=True)
class XmlElement:
    """Simple XML element that renders itself and its children."""

    tag: str
    attrs: dict[str, object] = field(default_factory=dict)
    children: list["XmlElement"] = field(default_factory=list)
    text: str | None = None

    def __post_init__(self) -> None:
        self.children = list(self.children)

    def add(self, *children: "XmlElement") -> "XmlElement":
        self.children.extend(children)
        return self

    def set(self, **attrs: object) -> "XmlElement":
        self.attrs.update(
            {name.replace("__", ":").rstrip("_"): value for name, value in attrs.items()}
        )
        return self

    def to_xml(self, *, indent: str = "  ", level: int = 0) -> str:
        spacing = indent * level
        attributes = "".join(
            f' {name}="{_render_attribute_value(value)}"'
            for name, value in self.attrs.items()
            if value is not None
        )

        if not self.children and self.text is None:
            return f"{spacing}<{self.tag}{attributes}/>"

        if self.text is not None and self.children:
            raise ValueError(f"{self.tag} cannot render both text and child elements")

        if self.text is not None:
            return f"{spacing}<{self.tag}{attributes}>{escape(self.text)}</{self.tag}>"

        rendered_children = "\n".join(
            child.to_xml(indent=indent, level=level + 1) for child in self.children
        )
        return f"{spacing}<{self.tag}{attributes}>\n{rendered_children}\n{spacing}</{self.tag}>"

    def __str__(self) -> str:
        return self.to_xml()

    def validate_types(self, *, strict: bool = True) -> None:
        """Recursively validate that children match expected types from __init__ signature.

        Args:
            strict: If True, raises TypeError on mismatch. If False, only warns.

        Raises:
            TypeError: If strict=True and type mismatches are found.
        """
        # Get the __init__ signature for this class
        init_method = self.__class__.__init__
        sig = inspect.signature(init_method)

        # Find the children parameter type hint
        # Only validate if parameter is actually named "children" to avoid
        # validating wrapper classes with differently-named variadic params
        children_param = None
        for param_name, param in sig.parameters.items():
            if param_name in ('self', 'args', 'kwargs'):
                continue
            # Look for *children parameter (VAR_POSITIONAL)
            if param.kind == inspect.Parameter.VAR_POSITIONAL and param_name == 'children':
                children_param = param
                break

        # Skip validation if no *children parameter found (wrapper/recipe classes)
        if not children_param:
            # Still recursively validate children
            for child in self.children:
                if isinstance(child, XmlElement):
                    child.validate_types(strict=strict)
            return

        # If we found a *children parameter with type hints, validate
        if children_param.annotation != inspect.Parameter.empty:
            expected_type = children_param.annotation

            # Handle string annotations (forward references)
            if isinstance(expected_type, str):
                # Try to resolve from module globals
                try:
                    import sys
                    module = sys.modules.get(self.__class__.__module__)
                    if module:
                        expected_type = eval(expected_type, vars(module))
                except:
                    pass  # Can't resolve, skip validation

            # Skip validation if we couldn't resolve the type
            if isinstance(expected_type, str):
                return

            # Convert to tuple for isinstance check if needed
            check_types = expected_type
            origin = get_origin(expected_type)

            # Handle Union types (e.g., Type1 | Type2)
            if origin is not None:
                args = get_args(expected_type)
                if args:
                    check_types = args

            # Ensure check_types is valid for isinstance
            try:
                # Test if we can use it with isinstance
                isinstance(self, check_types)
            except TypeError:
                # Can't use with isinstance, skip validation
                return

            # Validate each child
            for i, child in enumerate(self.children):
                if not isinstance(child, check_types):
                    type_name = (
                        expected_type.__name__ if hasattr(expected_type, '__name__')
                        else str(expected_type)
                    )
                    error_msg = (
                        f"{self.__class__.__name__} expects children of type "
                        f"{type_name}, "
                        f"but child at index {i} is {child.__class__.__name__}"
                    )
                    if strict:
                        raise TypeError(error_msg)
                    else:
                        import warnings
                        warnings.warn(error_msg, stacklevel=2)

                # Recursively validate children
                if isinstance(child, XmlElement):
                    child.validate_types(strict=strict)

    @classmethod
    def many(cls, tag: str, items: Iterable["XmlElement"]) -> "XmlElement":
        return cls(tag=tag, children=list(items))
