# X4-PINAT

Python helpers for generating X4: Foundations Mission Director and AI-script XML from readable, testable Python code.

## API Style

X4-PINAT is designed to be IDE-friendly first:

- Required values are positional where that improves clarity
- Optional values are keyword-only where that improves autocomplete
- Constructors use explicit parameter names that mirror X4 concepts
- Expression helpers make it obvious when you are passing quoted text, t-file references, paths, or raw tokens

That means the preferred workflow is to compose XML through typed Python calls such as `Order(...)`, `SetValue(...)`, `TextExpr.ref(...)`, and `ExtensionProject(...)` rather than building attribute dictionaries by hand.

## What It Solves

X4 mods often end up with large XML files that are tedious to refactor and easy to break. X4-PINAT gives you:

- Typed Python builders for MD and AI nodes
- Reusable expression helpers for X4 syntax
- Cleaner diffs and easier refactors than hand-written XML
- Unit-testable generation logic

## Installation

```bash
pip install -e .
```

For test tooling:

```bash
pip install -e ".[test]"
```

## Quoting Rules

The most important rule is that X4 uses several different kinds of attribute values. X4-PINAT keeps them distinct, but you need to choose the right helper.

```python
from x4md import Expr, PathExpr, TextExpr

# Literal string expression used by MD or AI
TextExpr.quote("Hello")          # -> "'Hello'"

# T-file reference for visible UI text
TextExpr.ref(77000, 10002)       # -> "{77000, 10002}"

# Object path / variable path
PathExpr.of("this", "ship")      # -> "this.ship"

# Raw X4 token or raw expression
Expr.raw("command.trade")        # -> "command.trade"
Expr.raw("$trade.count gt 0")    # -> "$trade.count gt 0"
```

Practical guidance:

- Use `TextExpr.quote(...)` for string literals that X4 should evaluate as text.
- Use `TextExpr.ref(page, id)` for visible labels such as AI order names and descriptions.
- Use raw tokens like `command.trade` or raw expressions like `$value + 1` without extra quotes.

## Quick Start

### Mission Director Example

```python
from x4md import Actions, Conditions, Cue, Cues, DebugText, EventGameLoaded, MDScript, TextExpr

script = MDScript(
    name="HelloWorld",
    cues=Cues(
        Cue(
            "Init",
            Conditions(EventGameLoaded()),
            Actions(
                DebugText(TextExpr.quote("Hello from X4-PINAT!"))
            ),
        )
    ),
)

print(script.to_document())
```

### AI Order Example

```python
from x4md import AIScript, Interrupts, Order, Resume, TextExpr, Wait

script = AIScript(
    "order.trade.demo",
    Order(
        "DemoOrder",
        Interrupts(),
        Wait(max="5s"),
        name=TextExpr.ref(20001, 1101),
        description=TextExpr.ref(20001, 1102),
        category="trade",
        infinite=True,
    ),
    version=1,
)
```

## Extension Projects

X4-PINAT can also assemble a full extension folder, including `content.xml`,
generated MD/AI files, and `t/` localization pages.

```python
from x4md import (
    ContentText,
    ExtensionContent,
    ExtensionProject,
    TranslationEntry,
    TranslationPage,
)

content = ExtensionContent(
    id="my_extension",
    name="My Extension",
    description="Example extension built entirely from Python",
    author="You",
    texts=(
        ContentText(
            language=44,
            name="My Extension",
            description="Example extension built entirely from Python",
            author="You",
        ),
    ),
)

project = ExtensionProject(
    content=content,
    md_scripts={"main.xml": script},
    translations=[
        TranslationPage(
            language_id=44,
            page_id=77000,
            title="My Extension",
            description="Localization",
            entries=(TranslationEntry(1001, "My Order"),),
        )
    ],
)

project.write("out/my_extension")
project.install("E:/SteamLibrary/steamapps/common/X4 Foundations/extensions")
```

## Common Building Blocks

### Expressions

- `TextExpr.quote(...)`
- `TextExpr.ref(...)`
- `PathExpr.of(...)`
- `ListExpr.of(...)`
- `TableExpr.of(...)`
- `MoneyExpr.of(...)`
- `BoolExpr.of(...)`
- `Expr.raw(...)`

### Mission Director

- `MDScript`, `Cues`, `Cue`, `Library`
- `Conditions`, `Actions`
- `SetValue`, `CreateList`, `AppendToList`
- `FindBuyOffer`, `FindSellOffer`, `FindStation`, `FindShip`
- `RunActions`, `SignalCueAction`, `WriteToLogbook`, `ShowNotification`

### AI Scripts

- `AIScript`, `Order`, `Requires`, `Interrupts`, `Handler`
- `Wait`, `Resume`, `Goto`, `Label`
- `RunScript`, `CreateOrder`, `CreateTradeOrder`
- `Attention`, `CreatePosition`, `GetJumpPath`
- `SetCommand`, `SetCommandAction`

## Usage Notes

### Visible Order Labels

Visible AI order labels should generally use t-file references:

```python
Order(
    "GalaxyTraderMK3",
    name=TextExpr.ref(77000, 10002),
    description=TextExpr.ref(77000, 10102),
)
```

### Command Tokens

`SetCommand` and `SetCommandAction` expect raw X4 tokens, not quoted text:

```python
SetCommand(command="command.trade")
SetCommandAction(commandaction="commandaction.searchingtrades")
```

### Order Creation

When creating orders from MD or AI, the `id` attribute is typically a string expression:

```python
CreateOrder(
    object="this.ship",
    id=TextExpr.quote("DockAndTrain"),
    immediate=True,
)
```

## Testing

Run the full test suite:

```bash
pytest tests/
```

Run with coverage:

```bash
coverage run -m pytest tests/
coverage report
```

## Repository Layout

```text
src/x4md/
  core/        XML primitives
  md/          Mission Director nodes and helpers
  x4ai/        AI-script nodes
  expressions.py

examples/      Small reference scripts
tests/         Unit tests
```

## Status

The library is in good shape for real mod generation work, especially around XML composition, expressions, and
the MD/AI node surface. The main thing to watch is choosing the right X4 value form for each attribute: quoted
text, t-file reference, path, or raw token.
