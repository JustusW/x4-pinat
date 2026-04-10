# X4-PINAT 🥬

**X4-PINAT** (pronounced like the German word "Spinat" / English "spinach") - **P**ython **I**nterface for **N**avigating **A**ggressive **T**ranspilation

A comprehensive, type-safe Python library for generating X4: Foundations Mission Director (MD) XML and AI-script XML from idiomatic Python code.

## 🎯 Purpose & Scope

X4-PINAT is designed to make X4 mod development faster, safer, and more maintainable by replacing hand-written XML with Python code that provides:

- **IDE Autocomplete**: Full IntelliSense/autocomplete support for all MD and AI nodes
- **Type Safety**: Strong typing prevents common XML errors at development time
- **Refactoring Support**: Rename variables, extract functions, and reorganize code with IDE support
- **Code Reuse**: Create reusable components, recipes, and patterns in Python
- **Version Control**: Python code diffs are more readable than XML diffs
- **Testing**: Write unit tests for your mod logic before deploying
- **Documentation**: Inline docstrings and examples for every node type

### What X4-PINAT Does

✅ **Transpiles** Python code to X4 MD/AI XML
✅ **Provides** 100+ node classes covering the entire MD/AI schema
✅ **Ensures** type-safe expression handling (text, paths, lists, tables, money, booleans)
✅ **Includes** high-level "recipe" helpers for common patterns
✅ **Supports** both Mission Director scripts (.xml) and AI-scripts (aiscripts/*.xml)

### What X4-PINAT Doesn't Do

❌ **Parse** existing XML back to Python (one-way transpiler only)
❌ **Execute** or simulate X4 game logic
❌ **Validate** game-specific IDs (wares, factions, sectors, etc.)
❌ **Handle** UI definitions, t-files, or other X4 data formats

## 🚀 Quick Start

### Installation

```bash
pip install x4-pinat
```

*Note: Not yet published to PyPI. For now, clone and install locally:*

```bash
git clone https://github.com/yourusername/x4-pinat.git
cd x4-pinat
pip install -e .
```

### Basic Example

```python
from x4md import (
    MDScript, Cues, Cue,
    Conditions, EventGameLoaded,
    Actions, DebugText,
    TextExpr,
)

# Create a simple MD script
script = MDScript(
    name="HelloWorld",
    cues=Cues(
        Cue(
            "Init",
            Conditions(EventGameLoaded()),
            Actions(
                DebugText(TextExpr.quote("Hello from Python!"))
            ),
        )
    ),
)

# Generate XML
print(script.to_document())
```

**Output:**
```xml
<?xml version="1.0" encoding="utf-8"?>
<mdscript name="HelloWorld" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="md.xsd">
  <cues>
    <cue name="Init">
      <conditions>
        <event_game_loaded/>
      </conditions>
      <actions>
        <debug_text text="'Hello from Python!'"/>
      </actions>
    </cue>
  </cues>
</mdscript>
```

### Trading Example (GalaxyTrader-style)

```python
from x4md import *

script = MDScript(
    name="TradeScanner",
    cues=Cues(
        Cue(
            "ScanForTrades",
            Conditions(
                EventGameLoaded()
            ),
            Actions(
                CreateList(name="$offers"),
                FindBuyOffer(
                    MatchBuyer(friend=True),
                    space="player.galaxy",
                    wares="[$energycells, $ore]",
                    result="$offers",
                    multiple=True,
                ),
                DoForEach(
                    "$offer",
                    in_="$offers",
                    DebugText(TextExpr.quote("Found trade: {$offer.ware}")),
                ),
            ),
        )
    ),
)
```

## 📦 Complete Feature Set

### Mission Director Nodes (80+ nodes)

**Document Structure:**
- `MDScript`, `Cues`, `Cue`, `Library`, `OnAbort`
- `Conditions`, `Actions`
- `Params`, `Param`, `InputParam`

**Control Flow:**
- `DoIf`, `DoElse`, `DoElseIf`, `DoAll`
- `DoWhile`, `DoForEach`, `Break`, `Continue`
- `Return`, `RunActions`

**Data Management:**
- `SetValue`, `RemoveValue`
- `CreateList`, `AppendToList`, `RemoveFromList`, `AppendListElements`
- `ShuffleList`, `SortList`, `SortTrades` (GalaxyTrader-specific)

**Find/Query Actions** (Critical for trading mods):
- `FindBuyOffer`, `FindSellOffer` (with `MatchBuyer`, `MatchSeller`)
- `FindStation`, `FindSector`, `FindGate`, `FindDockingbay`
- `FindShip`, `FindObject`
- `GetWareReservation`
- Match filters: `Match`, `MatchGateDistance`, `MatchDistance`, `MatchDock`, `MatchRelationTo`

**Orders:**
- `CreateOrder`, `CancelOrder`, `CancelAllOrders`
- `EditOrderParam`

**UI & Notifications:**
- `ShowNotification`, `WriteToLogbook`
- `DebugText`

**Object Management:**
- `SetObjectName`, `SetSkill`

**Text:**
- `SubstituteText`

**Player:**
- `RewardPlayer`

**Cues:**
- `SignalCueAction`, `SignalCueInstantly`, `SignalObjects`, `CancelCue`

**Events** (17+ event types):
- Game: `EventGameLoaded`, `EventGameSaved`, `EventPlayerCreated`
- Objects: `EventObjectDestroyed`, `EventObjectOrderReady`, `EventObjectChangedZone`, `EventObjectChangedSector`
- Cues: `EventCueSignalled`, `EventObjectSignalled`
- UI: `EventUITriggered`
- Player: `EventPlayerAssignedHiredActor`
- Conditions: `CheckValue`, `CheckAny`, `CheckAll`

**Delays:**
- `Delay` (exact/min/max timing)

### AI-Script Nodes (20+ nodes)

**Document:**
- `AIScript`, `Order`, `Requires`, `Interrupts`, `Handler`

**Control Flow:**
- `Wait`, `Resume`, `Label`, `Goto`
- `RunScript`, `Attention`, `IncludeInterruptActions`

**Orders:**
- `CreateOrder`, `CreateTradeOrder`
- `SetOrderFailed`, `SetOrderState`, `SetOrderSyncpointReached`, `ClearOrderFailure`

**Trading:**
- `AddWareReservation`, `RemoveWareReservation`
- `ClampTradeAmount`

**Navigation:**
- `CreatePosition`, `GetJumpPath`

**Commands:**
- `SetCommand`, `SetCommandAction`

### Expression Types (Type-Safe)

```python
from x4md import TextExpr, PathExpr, ListExpr, TableExpr, MoneyExpr, BoolExpr

# Text with proper quoting
TextExpr.quote("Hello")  # => "'Hello'"

# Paths to game objects
PathExpr.of("player", "ship")  # => "player.ship"

# Lists
ListExpr.of("ware.energycells", "ware.ore")  # => "[ware.energycells, ware.ore]"

# Tables
TableExpr.of(
    TableEntry("Ship", "$myShip"),
    TableEntry("Credits", 1000),
)  # => "table[$Ship = $myShip, $Credits = 1000]"

# Money
MoneyExpr.of(50000)  # => "50000Cr"

# Booleans
BoolExpr.TRUE  # => "true"
BoolExpr.FALSE  # => "false"
```

### Recipe Helpers (High-Level Patterns)

Simplify common patterns:

```python
from x4md import *

# Ensure a global counter exists
EnsureCounter("TradesCompleted", initial=0)

# Ensure a global list exists
EnsureList("$ActiveTrades")

# Conditional return
ReturnIf("$error")

# Abort cue if condition
AbortIf("not $initialized")

# Guard clause
Guard("$ready", "System not ready")

# Initialize globals on game load
InitializeGlobalsCue(
    SetValue("$version", exact="1.0.0"),
    CreateList(name="$traders"),
)

# Signal router pattern
SignalRouterCue("TradeRouter", ["ProcessTrade", "CancelTrade"])
```

## 🏗️ Architecture

X4-PINAT uses a layered architecture:

1. **Core XML** (`x4md.core`): Low-level XML element generation
2. **Expressions** (`x4md.expressions`): Type-safe expression rendering
3. **Node Types** (`x4md.md.types`, `x4md.x4ai.types`): Base classes for MD and AI nodes
4. **Node Implementations** (`x4md.md.*`, `x4md.x4ai.*`): All 100+ concrete node classes
5. **Recipes** (`x4md.md.recipes`): High-level helper patterns

All nodes are **immutable** (frozen dataclasses) for safety and **provide IDE autocomplete** through explicit constructors.

## 📊 Coverage

X4-PINAT provides **100% coverage** of nodes used in the GalaxyTrader mod (45 MD files + 25 AI-scripts, ~45,000 lines of XML).

### Implementation Phases (Completed)

- ✅ **Phase 1** (Trading Foundation): FindBuyOffer, FindSellOffer, GetWareReservation, Match conditions, SortTrades - **85% coverage**
- ✅ **Phase 2** (AI-Script Completion): Ware reservations, order management, RunScript, CreateTradeOrder - **95% coverage**
- ✅ **Phase 3** (Utilities): AppendListElements, CreatePosition, GetJumpPath, SetCommand, Delay - **98% coverage**
- ✅ **Phase 4** (Edge Cases): Additional match conditions, command actions - **100% coverage**

## 🧪 Testing

X4-PINAT maintains **100% test coverage** with 98+ unit tests.

Run tests:
```bash
pytest tests/
```

Run with coverage:
```bash
coverage run -m pytest tests/
coverage report
```

## 📖 Documentation

See [AI_DEVELOPMENT_GUIDE.md](AI_DEVELOPMENT_GUIDE.md) for:
- Coding standards
- Implementation patterns
- Testing requirements
- Common pitfalls
- Quick reference for adding new nodes

## 🤝 Contributing

Contributions are welcome! Please:

1. Follow the patterns in `AI_DEVELOPMENT_GUIDE.md`
2. Maintain 100% test coverage
3. Use type hints throughout
4. Document all public APIs with docstrings and examples
5. Run `pytest` and ensure all tests pass

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Egosoft for creating X4: Foundations
- The X4 modding community for documentation and examples
- GalaxyTrader mod by Nividica for providing comprehensive test cases

## 🔗 Related Projects

- [X4: Foundations](https://www.egosoft.com/games/x4/info_en.php)
- [X4 Wiki - Mission Director](https://www.x4wiki.com/)
- [GalaxyTrader Mod](https://www.nexusmods.com/x4foundations/mods/)

---

**X4-PINAT** - Making X4 mod development as smooth as spinach! 🥬
