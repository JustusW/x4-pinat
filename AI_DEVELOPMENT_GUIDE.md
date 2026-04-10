# AI Development Guide for X4 MD Transpiler

This guide helps AI assistants maintain and extend the X4 MD Transpiler library with consistent quality, style, and patterns.

## Core Design Principles

### 1. IDE Autocomplete Friendly

**Always use explicit, typed constructors** that enable IDE autocomplete:

```python
# ✅ GOOD: Clear constructor with typed parameters
class SetValue(ActionNode):
    def __init__(
        self,
        name: str,
        *,
        exact: ExprLike | None = None,
        operation: Operation | None = None,
    ) -> None:
        super().__init__(
            tag="set_value",
            attrs=normalize_attrs({"name": name, "exact": exact, "operation": operation}),
        )

# ❌ BAD: Generic constructor that requires manual string typing
class SetValue(ActionNode):
    def __init__(self, **kwargs):
        super().__init__(tag="set_value", attrs=kwargs)
```

**Key patterns:**
- Required parameters come first as positional arguments
- Optional parameters use keyword-only arguments (after `*`)
- Use descriptive parameter names matching XML attribute names
- Always type hint all parameters and return values

### 2. Strong Relevant Typing

**Use semantic type hierarchies** to guide users and prevent errors:

```python
# Type hierarchy provides semantic guarantees
class MDNode(XmlElement):
    """Base class for Mission Director nodes."""

class ActionNode(CueChildNode):
    """Base class for action and flow nodes."""

class ConditionNode(MDNode):
    """Base class for condition and event nodes."""
```

**Type aliases for domain concepts:**

```python
Operation: TypeAlias = Literal["add", "subtract", "multiply", "divide"]
ExprLike: TypeAlias = Expr | str | int | float | bool
PathPart: TypeAlias = str | Dynamic
```

**Variadic children with type constraints:**

```python
class Actions(ActionNode):
    def __init__(self, *children: ActionNode) -> None:
        super().__init__(tag="actions", children=list(children))

class Conditions(ConditionNode):
    def __init__(self, *children: ConditionNode) -> None:
        super().__init__(tag="conditions", children=list(children))
```

This ensures `Actions(...)` only accepts `ActionNode` instances, not arbitrary nodes.

### 3. Expression Type Safety

**Use typed expression classes** instead of raw strings:

```python
# Expression type system
@dataclass(frozen=True, slots=True)
class Expr:
    """Base class for X4 expression objects."""
    source: str

    @staticmethod
    def render(value: ExprLike) -> str:
        if isinstance(value, Expr):
            return value.source
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

# Specialized expression types
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
```

**Usage examples:**

```python
# ✅ GOOD: Type-safe expressions
SetValue("$ship", exact=PathExpr.of("this", "ship"))
DebugText(text=TextExpr.quote("Hello world"))
SetValue("$config", exact=TableExpr.of(
    TableEntry("MaxDistance", 5),
    TableEntry("Debug", True)
))

# ⚠️ ACCEPTABLE: Raw strings for simple cases
SetValue("$count", exact=0)
CheckValue("$ready")
```

### 4. Immutable Expression Types

**All expression types are frozen dataclasses:**

```python
@dataclass(frozen=True, slots=True)
class Expr:
    source: str

@dataclass(frozen=True, slots=True)
class Dynamic:
    name: str

    def render(self) -> str:
        return "{" + self.name + "}"

@dataclass(frozen=True, slots=True)
class TableEntry:
    key: str
    value: ExprLike

    def render(self) -> str:
        return f"${self.key} = {Expr.render(self.value)}"
```

**Why frozen:**
- Expressions are values, not mutable state
- Safe to share and reuse
- Hashable for caching
- Prevents accidental modification

### 5. Documentation Standards

**Every public class and method needs a docstring:**

```python
class DoIf(ActionNode):
    """Conditional action block that executes children if condition is true.

    Maps to X4 MD <do_if value="..."> element.

    Args:
        value: Boolean expression to evaluate
        *children: Action nodes to execute if condition is true
        comment: Optional comment for documentation

    Example:
        DoIf(
            "$count gt 0",
            DebugText("Count is positive"),
            SetValue("$ready", exact=True)
        )
    """
    def __init__(
        self,
        value: ExprLike,
        *children: ActionNode,
        comment: str | None = None
    ) -> None:
        super().__init__(
            tag="do_if",
            attrs=normalize_attrs({"value": value, "comment": comment}),
            children=list(children),
        )
```

**Documentation checklist:**
- [ ] One-line summary of purpose
- [ ] Mapping to X4 XML element (e.g., "Maps to `<do_if>`")
- [ ] Parameter descriptions using Args section
- [ ] Example usage showing typical patterns
- [ ] Note any special behaviors or constraints

### 6. Full Test Coverage

**Every node class must have tests:**

```python
class RenderingTests(unittest.TestCase):
    def test_set_value_with_exact_renders_correctly(self) -> None:
        """SetValue with exact parameter renders as <set_value>."""
        node = SetValue("$count", exact=5)
        expected = '<set_value name="$count" exact="5"/>'
        self.assertEqual(str(node), expected)

    def test_do_if_with_children_renders_nested(self) -> None:
        """DoIf with children renders nested action block."""
        node = DoIf(
            "$ready",
            SetValue("$result", exact=True),
            DebugText("Ready!")
        )
        xml = str(node)
        self.assertIn('<do_if value="$ready">', xml)
        self.assertIn('<set_value name="$result" exact="true"/>', xml)
        self.assertIn('<debug_text text="Ready!"/>', xml)
        self.assertIn('</do_if>', xml)
```

**Coverage requirements:**
- **100% line coverage** (run: `coverage run -m pytest && coverage report`)
- **100% branch coverage** where applicable
- Test both success and error paths
- Test with and without optional parameters
- Test edge cases (empty children, None values, etc.)

**Test organization:**
```
tests/
├── test_rendering.py        # XML rendering tests
├── test_expressions.py       # Expression type tests
├── test_md_actions.py        # MD action node tests
├── test_md_conditions.py     # MD condition node tests
├── test_ai_nodes.py          # AI-script node tests
└── test_recipes.py           # Recipe helper tests
```

## Implementation Patterns

### Pattern 1: Simple Leaf Node

For nodes with only attributes, no children:

```python
class Return(ActionNode):
    """Return a value from a library action.

    Maps to X4 MD <return value="..."/> element.

    Args:
        value: Expression to return

    Example:
        Return("$result")
    """
    def __init__(self, value: ExprLike) -> None:
        super().__init__(tag="return", attrs=normalize_attrs({"value": value}))
```

### Pattern 2: Container Node with Typed Children

For nodes that contain specific child types:

```python
class Actions(ActionNode):
    """Container for action nodes within a cue.

    Maps to X4 MD <actions> element.

    Args:
        *children: Action nodes to execute

    Example:
        Actions(
            SetValue("$count", exact=0),
            DebugText("Initialized")
        )
    """
    def __init__(self, *children: ActionNode) -> None:
        super().__init__(tag="actions", children=list(children))
```

### Pattern 3: Node with Required and Optional Parameters

Most common pattern - mix of required and optional attributes:

```python
class SignalObjects(ActionNode):
    """Signal one or more objects with parameters.

    Maps to X4 MD <signal_objects> element.

    Args:
        object: Object or list of objects to signal
        param: Primary signal parameter
        param2: Optional secondary parameter
        delay: Optional delay before signaling

    Example:
        SignalObjects(
            object="$ship",
            param=TextExpr.quote("GT_Trade_Complete"),
            param2=TableExpr.of(TableEntry("Profit", "$profit")),
            delay="1ms"
        )
    """
    def __init__(
        self,
        object: ExprLike,
        param: ExprLike,
        *,
        param2: ExprLike | None = None,
        delay: ExprLike | None = None,
    ) -> None:
        super().__init__(
            tag="signal_objects",
            attrs=normalize_attrs({
                "object": object,
                "param": param,
                "param2": param2,
                "delay": delay,
            }),
        )
```

**Note the `*` separator:** Everything after `*` must be passed as keyword arguments.

### Pattern 4: Node with Mixed Children and Attributes

For nodes with both attributes and children:

```python
class RunActions(ActionNode):
    """Call a library action with parameters.

    Maps to X4 MD <run_actions ref="..."> element.

    Args:
        ref: Reference to library action (e.g., "md.MyLib.MyAction")
        *params: Parameter nodes to pass to the action
        result: Optional variable to store return value

    Example:
        RunActions(
            "md.GT_Trading.FindTrade",
            Param("ship", value="$ship"),
            Param("maxDistance", value=5),
            result="$trade"
        )
    """
    def __init__(
        self,
        ref: str,
        *params: Param,
        result: str | None = None,
    ) -> None:
        super().__init__(
            tag="run_actions",
            attrs=normalize_attrs({"ref": ref, "result": result}),
            children=list(params),
        )
```

### Pattern 5: Recipe Helper Classes

High-level helpers that generate common patterns:

```python
class EnsureTable:
    """Recipe for ensuring a table exists with initialization.

    Generates a DoIf check that initializes a table if it doesn't exist.

    Args:
        path: Path to table variable (e.g., "global.$GT_Config")

    Returns:
        DoIf node that checks and initializes if needed

    Example:
        cue = Cue(
            "Init",
            conditions=Conditions(EventGameLoaded()),
            actions=Actions(
                EnsureTable("global.$GT_Ships"),
                EnsureTable("global.$GT_Config")
            )
        )
    """
    @staticmethod
    def __new__(cls, path: str) -> DoIf:
        return DoIf(
            f"not {path}?",
            SetValue(path, exact="table[]")
        )
```

**Recipe guidelines:**
- Use `__new__` to return actual node instances
- Document what pattern they generate
- Show the expansion in examples
- Keep them simple and composable

## Adding New Nodes

When adding support for a new X4 MD or AI element:

### Step 1: Determine Node Type

Identify the semantic category:
- **Action node?** Extends `ActionNode` (goes in `<actions>`)
- **Condition/event?** Extends `ConditionNode` (goes in `<conditions>`)
- **Cue child?** Extends `CueChildNode` (goes directly under `<cue>`)
- **Parameter?** Extends `ParamNode` (used for parameters)
- **AI-script?** Extends appropriate AI type

### Step 2: Analyze XML Structure

From X4 documentation or examples:
```xml
<append_to_list name="$myList" exact="$newValue"/>
```

- Tag: `append_to_list`
- Required attributes: `name`, `exact`
- Children: None
- Category: Action

### Step 3: Implement Class

```python
class AppendToList(ActionNode):
    """Append a value to a list variable.

    Maps to X4 MD <append_to_list> element.

    Args:
        name: Name of list variable to append to
        exact: Value to append to the list

    Example:
        AppendToList("$errors", exact=TextExpr.quote("Validation failed"))
    """
    def __init__(self, name: str, *, exact: ExprLike) -> None:
        super().__init__(
            tag="append_to_list",
            attrs=normalize_attrs({"name": name, "exact": exact}),
        )
```

### Step 4: Add to Module __init__.py

```python
# In src/x4md/md/actions.py - add the class

# In src/x4md/md/__init__.py - add to imports and __all__
from .actions import (
    Actions,
    AppendToList,  # ← Add here
    DebugText,
    # ...
)

__all__ = [
    "Actions",
    "AppendToList",  # ← Add here
    "DebugText",
    # ...
]
```

### Step 5: Write Tests

```python
def test_append_to_list_renders_correctly(self) -> None:
    """AppendToList renders with name and exact attributes."""
    node = AppendToList("$errors", exact=TextExpr.quote("Error message"))
    xml = str(node)
    self.assertIn('<append_to_list', xml)
    self.assertIn('name="$errors"', xml)
    self.assertIn("exact='Error message'", xml)
    self.assertIn('/>', xml)

def test_append_to_list_with_expression(self) -> None:
    """AppendToList accepts expression objects."""
    node = AppendToList("$ships", exact=PathExpr.of("this", "ship"))
    xml = str(node)
    self.assertIn('exact="this.ship"', xml)
```

### Step 6: Verify Coverage

```bash
coverage run -m pytest
coverage report
```

Target: 100% coverage on new code.

## Code Quality Checklist

Before submitting new code, verify:

- [ ] All classes have type hints on `__init__` parameters
- [ ] All classes have `-> None` return type on `__init__`
- [ ] Required parameters come before `*` separator
- [ ] Optional parameters use `| None` type and default to `None`
- [ ] All attributes passed through `normalize_attrs()`
- [ ] Children converted to lists: `children=list(children)` or `list(params)`
- [ ] Docstring includes:
  - [ ] One-line summary
  - [ ] Mapping to X4 XML element
  - [ ] Args section with all parameters
  - [ ] Example showing typical usage
- [ ] Added to module `__init__.py` and `__all__`
- [ ] Tests written covering:
  - [ ] Basic rendering
  - [ ] Optional parameters
  - [ ] Expression types
  - [ ] Edge cases
- [ ] 100% test coverage verified
- [ ] Examples updated if adding major features

## Style Guide

### Import Organization

```python
"""Module docstring."""

from __future__ import annotations  # Always first

from typing import Literal, TypeAlias  # Standard library
from dataclasses import dataclass

from x4md.expressions import ExprLike  # Cross-package
from x4md.core import XmlElement

from .common import normalize_attrs  # Same package
from .types import ActionNode, ParamNode
```

### Naming Conventions

- **Classes:** PascalCase matching X4 semantic concept (`SetValue`, `DoIf`)
- **Functions/methods:** snake_case (`normalize_attrs`, `render`)
- **Type aliases:** PascalCase (`ExprLike`, `Operation`)
- **Constants:** UPPER_SNAKE_CASE (`TRUE`, `FALSE`, `NULL`)

### Formatting

- Line length: 100 characters (hard limit)
- Indentation: 4 spaces
- Use trailing commas in multiline structures
- Use `black` or similar formatter (optional but recommended)

### Type Hints

```python
# Always use modern union syntax (Python 3.11+)
def __init__(self, value: str | int | None = None) -> None:  # ✅ GOOD
def __init__(self, value: Optional[Union[str, int]] = None):  # ❌ BAD

# Use ExprLike for X4 expression parameters
def __init__(self, exact: ExprLike) -> None:  # ✅ GOOD
def __init__(self, exact: str) -> None:       # ❌ BAD - too restrictive
```

## Testing Standards

### Test Structure

```python
class NodeTests(unittest.TestCase):
    """Tests for {NodeName} class."""

    def test_{node}_{scenario}_behaves_correctly(self) -> None:
        """{NodeName} {expected behavior} when {scenario}."""
        # Arrange
        node = NodeClass(param1, param2=value)

        # Act
        result = str(node)

        # Assert
        self.assertEqual(result, expected)
        # or
        self.assertIn(expected_substring, result)
```

### Test Naming

Pattern: `test_{class}_{scenario}_{expected}`

Examples:
- `test_set_value_with_exact_renders_attribute`
- `test_do_if_without_children_renders_self_closing`
- `test_path_expr_with_dynamic_renders_braces`

### Coverage Verification

```bash
# Run tests with coverage
coverage run -m pytest

# Generate report
coverage report --show-missing

# Generate HTML report for detailed analysis
coverage html
# Open htmlcov/index.html in browser
```

**Target: 100% coverage** for all new code.

## Common Pitfalls

### 1. Forgetting normalize_attrs()

```python
# ❌ WRONG - None values create invalid XML
super().__init__(
    tag="node",
    attrs={"value": value, "optional": optional}  # optional=None → optional="None"
)

# ✅ CORRECT - normalize_attrs filters None
super().__init__(
    tag="node",
    attrs=normalize_attrs({"value": value, "optional": optional})
)
```

### 2. Not Converting Children to List

```python
# ❌ WRONG - variadic args is a tuple
def __init__(self, *children: ActionNode) -> None:
    super().__init__(tag="actions", children=children)  # tuple, not list!

# ✅ CORRECT - convert to list
def __init__(self, *children: ActionNode) -> None:
    super().__init__(tag="actions", children=list(children))
```

### 3. Incorrect Type Constraints

```python
# ❌ WRONG - too permissive
class Actions(ActionNode):
    def __init__(self, *children: MDNode) -> None:  # Accepts any MDNode!
        super().__init__(tag="actions", children=list(children))

# ✅ CORRECT - semantic constraint
class Actions(ActionNode):
    def __init__(self, *children: ActionNode) -> None:  # Only ActionNode
        super().__init__(tag="actions", children=list(children))
```

### 4. Missing Keyword-Only Marker

```python
# ❌ WRONG - optional params can be positional
def __init__(self, name: str, exact: ExprLike | None = None) -> None:
    # Can call: DoSomething("foo", "bar") - unclear what "bar" is

# ✅ CORRECT - optional params must be keywords
def __init__(self, name: str, *, exact: ExprLike | None = None) -> None:
    # Must call: DoSomething("foo", exact="bar") - clear intent
```

### 5. Mutable Default Arguments

```python
# ❌ WRONG - shared mutable default
def __init__(self, items: list[str] = []) -> None:
    self.items = items

# ✅ CORRECT - use None and create new instance
def __init__(self, items: list[str] | None = None) -> None:
    self.items = items if items is not None else []
```

## Performance Considerations

### 1. Use Slots for Data Classes

```python
@dataclass(frozen=True, slots=True)  # ← slots=True reduces memory
class Expr:
    source: str
```

### 2. Precompute Constants

```python
# Define once at module level
TRUE = BoolExpr("true")
FALSE = BoolExpr("false")
NULL = Expr("null")

# Reuse in code
SetValue("$ready", exact=TRUE)  # ✅ Fast
SetValue("$ready", exact=BoolExpr("true"))  # ⚠️ Slower, creates instance
```

### 3. Lazy Rendering

Don't render XML until `str()` or `.to_xml()` is called - keep as object tree.

## Resources

### X4 Documentation
- Mission Director Guide: https://wiki.egosoft.com/X%20Rebirth%20Wiki/Modding%20support/Mission%20Director%20Guide/
- AI Script Documentation: (in X4 SDK)

### Project Files
- `docs/galaxytrader-component-candidates.md` - Analysis of GalaxyTrader v9
- `examples/` - Working examples of library usage
- `tests/test_rendering.py` - Reference implementation patterns

### Python References
- Type hints: https://docs.python.org/3/library/typing.html
- Dataclasses: https://docs.python.org/3/library/dataclasses.html
- Coverage.py: https://coverage.readthedocs.io/

---

## Quick Reference Card

**Adding a new action node:**

```python
# 1. Implement class in src/x4md/md/actions.py
class NewAction(ActionNode):
    """Description.

    Maps to X4 MD <new_action> element.

    Args:
        required: Required parameter
        optional: Optional parameter

    Example:
        NewAction("value", optional=True)
    """
    def __init__(self, required: str, *, optional: bool | None = None) -> None:
        super().__init__(
            tag="new_action",
            attrs=normalize_attrs({"required": required, "optional": optional}),
        )

# 2. Add to src/x4md/md/__init__.py
from .actions import NewAction
__all__ = [..., "NewAction"]

# 3. Write test in tests/test_md_actions.py
def test_new_action_renders_correctly(self) -> None:
    node = NewAction("test")
    self.assertEqual(str(node), '<new_action required="test"/>')

# 4. Verify coverage
coverage run -m pytest && coverage report
```

**Type annotations quick ref:**

```python
ExprLike              # Accepts Expr, str, int, float, bool
str | None            # Optional string
*children: ActionNode # Variadic typed children
Literal["a", "b"]     # Enumerated string values
```

**Expression helpers:**

```python
TextExpr.quote("text")                    # 'text'
PathExpr.of("global", "$GT", Dynamic("ship"))  # global.$GT.{ship}
ListExpr.of(1, 2, 3)                      # [1, 2, 3]
TableExpr.of(TableEntry("Key", "value"))  # table[$Key = value]
MoneyExpr.of(1000)                        # 1000Cr
BoolExpr.of(True)                         # true
TRUE, FALSE, NULL                         # Constants
```
