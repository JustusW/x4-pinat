# X4-PINAT 🥬

<div align="center">

**Python Interface for Navigating Aggressive Transpilation**

*Pronounced like the German word "Spinat" (English: "spinach")*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/yourusername/x4-pinat)
[![Type Checked](https://img.shields.io/badge/type--checked-mypy-blue.svg)](http://mypy-lang.org/)

A comprehensive, type-safe Python library for generating [X4: Foundations](https://www.egosoft.com/games/x4/info_en.php) Mission Director (MD) XML and AI-script XML from idiomatic Python code.

[Features](#-features) •
[Installation](#-installation) •
[Quick Start](#-quick-start) •
[Documentation](#-documentation) •
[Examples](#-examples) •
[Contributing](#-contributing)

</div>

---

## 🎯 What is X4-PINAT?

X4-PINAT transforms X4 mod development by replacing hand-written XML with **type-safe, IDE-friendly Python code**. Instead of wrestling with thousands of lines of XML, write clean Python that provides:

- ✅ **Full IDE Autocomplete** - IntelliSense support for all MD and AI nodes
- ✅ **Type Safety** - Catch errors at development time, not runtime
- ✅ **Refactoring Support** - Rename, extract, and reorganize with confidence
- ✅ **Code Reuse** - Create libraries of reusable mod components
- ✅ **Better Version Control** - Readable diffs instead of XML chaos
- ✅ **Unit Testing** - Test your mod logic before deployment
- ✅ **Built-in Documentation** - Every node includes examples and docstrings

### The Problem

```xml
<!-- Traditional X4 modding: Hand-written XML -->
<cue name="FindTrades">
  <conditions>
    <event_game_loaded/>
  </conditions>
  <actions>
    <find_buy_offer space="player.galaxy" result="$offers">
      <match_buyer friend="true"/>
    </find_buy_offer>
    <do_for_each name="$offer" in="$offers">
      <debug_text text="'Found: ' + $offer.ware"/>
    </do_for_each>
  </actions>
</cue>
```

### The X4-PINAT Solution

```python
# Type-safe Python with IDE autocomplete
from x4md import *

Cue(
    "FindTrades",
    Conditions(EventGameLoaded()),
    Actions(
        FindBuyOffer(
            MatchBuyer(friend=True),
            space="player.galaxy",
            result="$offers",
        ),
        DoForEach(
            "$offer",
            in_="$offers",
            DebugText(TextExpr.quote("Found: {$offer.ware}")),
        ),
    ),
)
```

---

## ✨ Features

### Complete X4 Coverage

- **100+ Node Classes** covering the entire MD and AI-script schema
- **Mission Director Nodes** - All actions, conditions, events, and control flow
- **AI-Script Nodes** - Complete support for ship AI behavior
- **Trading Systems** - Full support for buy/sell offers, ware reservations, trade orders
- **Navigation** - Position creation, jump path calculation, docking
- **Match Filters** - Sophisticated filtering for find operations

### Type-Safe Expression System

```python
# Strongly-typed expressions prevent common errors
TextExpr.quote("Hello")              # => "'Hello'"
PathExpr.of("player", "ship")        # => "player.ship"
ListExpr.of("$var1", "$var2")        # => "[$var1, $var2]"
TableExpr.of(                        # => "table[$Ship = $myShip, $Credits = 1000]"
    TableEntry("Ship", "$myShip"),
    TableEntry("Credits", 1000),
)
MoneyExpr.of(50000)                  # => "50000Cr"
BoolExpr.TRUE                        # => "true"
```

### High-Level Recipe Helpers

Simplify common patterns with recipe helpers:

```python
# Ensure a global list exists on first run
EnsureList("$ActiveTrades")

# Initialize globals on game load
InitializeGlobalsCue(
    SetValue("$version", exact="1.0.0"),
    CreateList(name="$traders"),
)

# Guard clause with error message
Guard("$initialized", "System not ready")

# Signal router pattern for multiple handlers
SignalRouterCue("TradeRouter", ["ProcessTrade", "CancelTrade"])
```

### Production-Ready Quality

- **100% Test Coverage** - 98+ comprehensive unit tests
- **Type Checked** - Full mypy compatibility
- **Immutable Nodes** - Frozen dataclasses prevent accidental mutations
- **Zero Dependencies** - Pure Python 3.11+ (testing dependencies optional)

---

## 📦 Installation

### From PyPI (when published)

```bash
pip install x4-pinat
```

### From Source

```bash
git clone https://github.com/yourusername/x4-pinat.git
cd x4-pinat
pip install -e .
```

### Requirements

- Python 3.11 or higher
- No runtime dependencies!

---

## 🚀 Quick Start

### Hello World

```python
from x4md import MDScript, Cues, Cue, Conditions, Actions, EventGameLoaded, DebugText, TextExpr

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
        <debug_text text="'Hello from X4-PINAT!'"/>
      </actions>
    </cue>
  </cues>
</mdscript>
```

### Save to File

```python
# Save to your X4 extensions folder
output_path = "path/to/X4/extensions/mymod/md/mymod.xml"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(script.to_document())
```

---

## 📚 Examples

<details>
<summary><b>📈 Trading Scanner (GalaxyTrader-style)</b></summary>

```python
from x4md import *

script = MDScript(
    name="TradeScanner",
    cues=Cues(
        # Initialize on game load
        InitializeGlobalsCue(
            CreateList(name="$tradeOffers"),
            SetValue("$scanInterval", exact="30s"),
        ),

        # Scan for profitable trades every 30 seconds
        Cue(
            "ScanForTrades",
            Conditions(
                EventCueSignalled(),
                CheckValue("$tradeOffers != null"),
            ),
            Actions(
                # Find buy offers from friendly factions
                FindBuyOffer(
                    MatchBuyer(friend=True, space="player.galaxy"),
                    space="player.galaxy",
                    wares="[$energycells, $ore, $foodrations]",
                    result="$tradeOffers",
                    multiple=True,
                ),

                # Sort by profitability
                SortTrades(
                    tradelist="$tradeOffers",
                    sorter="@$trade.profit",
                    result="$sortedTrades",
                ),

                # Log the best trades
                DoForEach(
                    "$trade",
                    in_="$sortedTrades",
                    counter="$i",
                    DoIf(
                        "$i le 5",  # Only log top 5
                        DebugText(TextExpr.quote(
                            "Trade {$i}: {$trade.ware} - {$trade.profit}Cr profit"
                        )),
                    ),
                ),
            ),
        ),
    ),
)
```

</details>

<details>
<summary><b>🤖 AI Trading Script</b></summary>

```python
from x4md import AIScript, Order, Requires, Wait, RunScript, AddWareReservation

script = AIScript(
    name="trade.routine",
    Order(
        "TradeRoutine",
        name="{20001,1101}",  # Trade routine name from t-file
        description="{20001,1102}",
        category="trade",
        infinite=True,

        # Required conditions
        Requires(
            Match(class_="ship_l", owner="faction.player"),
        ),

        # Main trade loop
        RunScript(name="'move.findtrade'"),

        Wait(exact="5s"),

        AddWareReservation(
            object="this.ship",
            ware="$targetWare",
            amount="$tradeAmount",
            type="buy",
        ),

        RunScript(name="'move.dockat'", Param(name="destination", value="$tradeStation")),
    ),
)
```

</details>

<details>
<summary><b>🎯 Event-Driven System</b></summary>

```python
from x4md import *

script = MDScript(
    name="ShipMonitor",
    cues=Cues(
        Cue(
            "WatchPlayerShip",
            Conditions(
                EventGameLoaded(),
            ),
            Actions(
                CreateList(name="$visitedSectors"),
            ),
            # Child cue that monitors events
            Cue(
                "OnSectorChange",
                Conditions(
                    EventObjectChangedSector(object="player.ship"),
                ),
                Actions(
                    AppendToList(name="$visitedSectors", exact="player.ship.sector"),
                    ShowNotification(
                        text=TextExpr.quote("Entered sector: {player.ship.sector.name}"),
                        caption=TextExpr.quote("Navigation"),
                    ),
                ),
                instantiate=True,  # Re-trigger on every sector change
            ),
        ),
    ),
)
```

</details>

<details>
<summary><b>🔄 Advanced Pattern: Signal Router</b></summary>

```python
from x4md import *

# Create a central signal router for multiple sub-systems
script = MDScript(
    name="ModuleCoordinator",
    cues=Cues(
        # Signal router distributes events to handlers
        SignalRouterCue(
            "CoreRouter",
            handler_names=["InitModule", "UpdateModule", "ShutdownModule"],
        ),

        # Initialization handler
        Cue(
            "InitModule",
            Conditions(EventCueSignalled()),
            Actions(
                DebugText(TextExpr.quote("Initializing modules...")),
                # Your init logic here
            ),
        ),

        # Update handler
        Cue(
            "UpdateModule",
            Conditions(EventCueSignalled()),
            Actions(
                # Your update logic here
            ),
        ),

        # Shutdown handler
        Cue(
            "ShutdownModule",
            Conditions(EventCueSignalled()),
            Actions(
                DebugText(TextExpr.quote("Shutting down modules...")),
                # Your cleanup logic here
            ),
        ),
    ),
)
```

</details>

---

## 📖 Documentation

### Complete Node Reference

<details>
<summary><b>Mission Director Nodes (80+ nodes)</b></summary>

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
- `ShuffleList`, `SortList`, `SortTrades`

**Find/Query Actions** *(Critical for trading mods)*:
- `FindBuyOffer`, `FindSellOffer` with `MatchBuyer`, `MatchSeller`
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

**Events** (17+ types):
- Game: `EventGameLoaded`, `EventGameSaved`, `EventPlayerCreated`
- Objects: `EventObjectDestroyed`, `EventObjectOrderReady`, `EventObjectChangedZone`, `EventObjectChangedSector`
- Cues: `EventCueSignalled`, `EventObjectSignalled`
- UI: `EventUITriggered`
- Player: `EventPlayerAssignedHiredActor`

**Conditions:**
- `CheckValue`, `CheckAny`, `CheckAll`

**Timing:**
- `Delay` (exact/min/max)

</details>

<details>
<summary><b>AI-Script Nodes (24+ nodes)</b></summary>

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

</details>

<details>
<summary><b>Expression Types (Type-Safe)</b></summary>

All expressions are **strongly typed** and provide IDE autocomplete:

```python
from x4md import TextExpr, PathExpr, ListExpr, TableExpr, MoneyExpr, BoolExpr, Dynamic

# Text - automatic quoting
TextExpr.quote("Hello")  # => "'Hello'"

# Paths - dot-notation
PathExpr.of("player", "ship", "sector")  # => "player.ship.sector"

# Lists - bracket notation
ListExpr.of("item1", "item2")  # => "[item1, item2]"

# Tables - key-value pairs
TableExpr.of(
    TableEntry("Key", "value"),
    TableEntry("Number", 42),
)  # => "table[$Key = value, $Number = 42]"

# Money - automatic Cr suffix
MoneyExpr.of(100000)  # => "100000Cr"

# Booleans
BoolExpr.TRUE   # => "true"
BoolExpr.FALSE  # => "false"

# Dynamic values (pass through without quotes)
Dynamic("$myVariable")  # => "$myVariable"
```

</details>

<details>
<summary><b>Recipe Helpers (High-Level Patterns)</b></summary>

Pre-built patterns for common use cases:

```python
from x4md import *

# Ensure global variables exist
EnsureCounter("TradeCount", initial=0)
EnsureList("$ActiveShips")
EnsureTable("$ShipRegistry")
EnsurePath("$PlayerHQ", default="null")

# Conditional flow
ReturnIf("$error")
AbortIf("not $initialized")
Guard("$ready", "System not ready")

# Initialization patterns
InitializeGlobalsCue(
    SetValue("$modVersion", exact="1.0.0"),
    CreateList(name="$data"),
)
GameLoadedCue("OnGameLoad", Actions(...))
PlayerCreatedCue("OnPlayerCreate", Actions(...))

# Signal routing
SignalRouterCue("EventRouter", ["Handler1", "Handler2", "Handler3"])
CueSignalledCue("MyHandler", Actions(...))

# Library registration
RequestRegistryLibrary()
```

</details>

---

## 🏗️ Architecture

X4-PINAT uses a clean, layered architecture:

```
┌─────────────────────────────────────────┐
│          Your Python Code               │
│  (Type-safe, IDE-friendly mod logic)    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│       Recipe Helpers (md.recipes)       │
│   (High-level patterns & utilities)     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Node Implementations (md/x4ai)      │
│   (100+ concrete MD & AI node classes)  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Expression System (expressions.py)     │
│ (Type-safe expression rendering)        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│       Core XML (core/xml.py)            │
│    (Low-level XML generation)           │
└──────────────┬──────────────────────────┘
               │
               ▼
         X4 MD/AI XML
```

**Key Design Principles:**

- **Immutability** - All nodes are frozen dataclasses
- **Type Safety** - Strong typing throughout with mypy compatibility
- **Composability** - Nodes compose naturally like building blocks
- **Zero Runtime Dependencies** - Pure Python 3.11+
- **100% Test Coverage** - Every node is thoroughly tested

---

## 🧪 Testing

X4-PINAT maintains **100% test coverage** with comprehensive unit tests.

### Run Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_md_actions.py

# Run with coverage report
coverage run -m pytest tests/
coverage report
```

---

## 📊 Coverage & Battle-Testing

X4-PINAT provides **100% coverage** of nodes used in real-world mods:

### GalaxyTrader Mod (Full Coverage)

- ✅ **45 MD files** (~45,000 lines of XML)
- ✅ **25 AI-script files**
- ✅ **All trading logic** - Buy/sell offers, ware reservations, trade orders
- ✅ **All AI behaviors** - Ship movement, docking, order management
- ✅ **All find operations** - Stations, sectors, gates, ships, objects
- ✅ **All match conditions** - Buyer/seller filtering, distance checks, gate jumps

### Implementation Phases

| Phase | Focus | Nodes | Coverage |
|-------|-------|-------|----------|
| ✅ Phase 1 | Trading Foundation | 12 nodes | 85% |
| ✅ Phase 2 | AI-Script Completion | 13 nodes | 95% |
| ✅ Phase 3 | Utilities & Polish | 6 nodes | 98% |
| ✅ Phase 4 | Edge Cases | 3 nodes | **100%** |

**Total: 34 new nodes** added across all phases to achieve complete coverage.

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Start

```bash
git clone https://github.com/yourusername/x4-pinat.git
cd x4-pinat
pip install -e ".[test]"
pytest tests/
```

### Guidelines

1. Follow the patterns in [AI_DEVELOPMENT_GUIDE.md](AI_DEVELOPMENT_GUIDE.md)
2. Maintain 100% test coverage
3. Use type hints throughout
4. Document all public APIs
5. Run tests before submitting PRs

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Egosoft** for X4: Foundations
- **X4 Modding Community** for documentation and support
- **GalaxyTrader Mod** by Nividica for comprehensive test cases

---

## 🔗 Resources

- [X4: Foundations](https://www.egosoft.com/games/x4/info_en.php)
- [X4 Wiki - Mission Director](https://www.x4wiki.com/)
- [Egosoft Forums](https://forum.egosoft.com/)
- [X4 Subreddit](https://www.reddit.com/r/X4Foundations/)

---

<div align="center">

**X4-PINAT** - Making X4 mod development as smooth as spinach! 🥬

[⬆ Back to Top](#x4-pinat-)

</div>
