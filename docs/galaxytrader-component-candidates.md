# GalaxyTrader Component Candidates

This note analyzes `GoAhead-at/galaxy_trader_v9` and uses the Mk4 supply routine as a concrete example for reusable framework components.

## Important scope note

The Mk4 routine itself is an AI script, not an MD script:

- `order.trade.galaxytradermk4.xml` defines an `aiscript` order with parameters, interrupts, and long-running control flow.
- The mod's `md/` folder provides orchestration, state, queues, caches, and reusable `library` actions that the AI script talks to through signals.

That means the clean framework split is:

- an MD framework for `mdscript`, `cue`, `library`, `conditions`, `actions`, `run_actions`, and signal wiring
- an optional later X4 XML framework layer for AI scripts (`aiscript`, `order`, `interrupts`, `wait`, `resume`, `create_order`, etc.)

## What GalaxyTrader tells us about good abstractions

GalaxyTrader is already structured the way a Python DSL should encourage authors to think:

- top-level orchestration in instantiate cues
- small reusable `library` blocks with parameters and return values
- event-driven communication via `signal_objects` and `event_object_signalled`
- defensive state initialization and migration logic
- table/list-heavy data passing between modules

The strongest reusable patterns are below.

## Best MD component candidates

### 1. Document and library primitives

GalaxyTrader leans heavily on `library` nodes with `purpose="run_actions"`:

- `GT_CalculateTradeEfficiency` in `gt_libraries_general.xml`
- `GT_RequestRegistry_Acquire`, `GT_RequestStatus_Init`, `GT_RequestRegistry_Release` in `gt_libraries_general.xml`
- `GLX_GenerateTradeKey`, `GLX_InitializeTradeIndex`, `GLX_AddTradeToIndex` in `glx_lib_reservations.xml`
- `GLX_PurgeCacheOfferPair_AllHomes` in `glx_lib_cache.xml`

Framework candidates:

- `Library(name, purpose="run_actions", params=[...], actions=[...])`
- `Param(name, default=None, comment=None)`
- `Return(value)`
- `RunActions(ref, params=[...], result=None)`

Why this belongs in the framework:

- this is the main modularity mechanism in real MD-heavy mods
- hand-writing parameter and `run_actions` blocks is repetitive and error-prone

## 2. Instantiate cue patterns

GalaxyTrader uses many `instantiate="true"` cues as persistent event processors and initializers:

- `SystemInitV3` in [gt_trading_ai.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/md/gt_trading_ai.xml#L16)
- `HandleAITradeRequest` in [gt_trading_ai.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/md/gt_trading_ai.xml#L224)
- `ProcessDelayedTradeRequest` in [gt_trading_ai.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/md/gt_trading_ai.xml#L357)
- `ExecuteTrade` in [gt_trading_execution.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/md/gt_trading_execution.xml#L10)

Framework candidates:

- `Cue(name, instantiate=True, version=None, comment=None)`
- helper builders such as `on_game_loaded(...)`, `on_player_created(...)`, `on_signal(...)`, `on_cue_signalled(...)`
- `CheckAny(...)`, `CheckValue(...)`, `DoIf(...)`, `DoElse(...)`, `DoAll(...)`

Why this belongs in the framework:

- it is the backbone of MD event systems
- it creates a readable Python mapping from "when this event happens, run these actions"

## 3. Signal bus and event routing

The Mk4 AI script and MD modules communicate through named signals:

- AI listens for `GT_Trade_Found` and `GT_Search_Go` in [order.trade.galaxytradermk4.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/aiscripts/order.trade.galaxytradermk4.xml#L138) and [order.trade.galaxytradermk4.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/aiscripts/order.trade.galaxytradermk4.xml#L182)
- AI emits `GT_Station_Detected` and `GT_Threat_Warning` in [order.trade.galaxytradermk4.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/aiscripts/order.trade.galaxytradermk4.xml#L268) and [order.trade.galaxytradermk4.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/aiscripts/order.trade.galaxytradermk4.xml#L384)
- MD receives `GT_Legacy_Trade_Request` in [gt_trading_ai.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/md/gt_trading_ai.xml#L224)
- MD emits `GT_Trade_Found` in [gt_trading_execution.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/md/gt_trading_execution.xml#L1137)

Framework candidates:

- `EventObjectSignalled(object_expr, param)`
- `SignalObjects(object_expr, param, param2=None, delay=None)`
- `SignalCueInstantly(cue, param=None)`
- optional `SignalNames` constants module

Why this belongs in the framework:

- cross-file signal contracts are central to larger X4 mods
- a typed or semi-typed helper for signal payloads would make mods safer to evolve

## 4. State initialization and "ensure table exists" helpers

GalaxyTrader spends a lot of MD code on safely initializing nested global tables:

- scheduler/bootstrap work in [gt_trading_ai.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/md/gt_trading_ai.xml#L16)
- trade index initialization in [glx_lib_reservations.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/md/glx_lib_reservations.xml#L141)

Framework candidates:

- `SetValue(name, exact=None, operation=None)`
- helper macros such as `ensure_table("global.$GT_Scheduler")`
- helper macros such as `ensure_list("global.$GT_Scheduler.$WorkQueue")`
- helper macros such as `ensure_counter("global.$GT_TraceIdCounter", 1)`

Why this belongs in the framework:

- this is repetitive boilerplate
- it makes large MD systems verbose and hard to audit

## 5. Table and list expression helpers

GalaxyTrader passes structured data everywhere:

- `table[...]` payloads for signals and caches
- `[]` lists for queues, homes, failed trades, and fallbacks
- object-keyed global tables like `global.$GT_TradeIndex.{tradeKey}`

Framework candidates:

- expression helpers:
  - `TableExpr(...)`
  - `ListExpr(...)`
  - `Ref("global.$GT_Scheduler.$WorkQueue")`
  - `Path("global", "GT_TradeIndex", Dynamic("tradeKey"))`
- value wrappers:
  - `Null`
  - `Bool`
  - `Money`
  - raw expression passthrough for advanced cases

Why this belongs in the framework:

- most MD authoring pain is not XML syntax, it is safely composing X4 expression strings

## 6. Defensive validation and error/reporting blocks

The trade pipeline contains repeated validation patterns:

- null trade and invalid trade checks in [gt_trading_execution.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/md/gt_trading_execution.xml#L43) and [gt_trading_execution.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/md/gt_trading_execution.xml#L82)
- trade-key validation in [glx_lib_reservations.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/md/glx_lib_reservations.xml#L9)
- cache invalidation validation in [glx_lib_cache.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/md/glx_lib_cache.xml#L60)

Framework candidates:

- `DebugText(text, chance="100")`
- `AbortIf(condition, actions=[...])`
- `Guard(condition, then=[...], else_=[...])`
- `ReturnIf(condition, value)`

Why this belongs in the framework:

- X4 XML commonly needs "check, log, early return" flows
- composable helpers keep complex cues readable

## 7. Domain-specific MD helpers worth providing later

These come directly from recurring GalaxyTrader libraries and are strong "component pack" candidates rather than XML primitives:

- request registry
- request status tracker
- trade-key generation
- trade-index maintenance
- cache invalidation by offer-pair
- trade-efficiency scoring

These are higher-level than the XML builder, but a framework can ship them as optional recipes or reusable Python factories.

## What should not be MD-only

The Mk4 routine also highlights features that do not belong in an MD-only API, because they are AI-script concepts:

- `aiscript`
- `order`
- `interrupts` and AI `handler`
- `wait`, `resume`, `goto`, labels
- `create_order`

Examples:

- order parameters and interrupts in [order.trade.galaxytradermk4.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/aiscripts/order.trade.galaxytradermk4.xml#L3)
- training order creation in [order.trade.galaxytradermk4.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/aiscripts/order.trade.galaxytradermk4.xml#L212)
- pre-request signal wait in [order.trade.galaxytradermk4.xml](C:/Users/winge/OneDrive/Documents/Egosoft/Galaxy%20Trader/PythonToMDTranspiler/.tmp-galaxy-trader-v9-2/aiscripts/order.trade.galaxytradermk4.xml#L3107)

Recommendation:

- keep the current project focused on MD first
- design the generic XML layer so an `x4ai` package can be added later without rework

## Concrete framework roadmap from this analysis

### Phase 1: core MD syntax

- `MDScript`
- `Cues`
- `Cue`
- `Library`
- `Conditions`
- `Actions`
- `Param`
- `RunActions`
- `Return`
- `SetValue`
- `DebugText`
- `DoIf`
- `DoElse`
- `DoAll`
- `CheckAny`
- `CheckValue`
- `EventGameLoaded`
- `EventPlayerCreated`
- `EventCueSignalled`
- `EventObjectSignalled`
- `SignalCueInstantly`
- `SignalObjects`

### Phase 2: expression builders

- `TableExpr`
- `ListExpr`
- expression/path builders for `global.$Foo.{bar}`
- safe raw-expression escape hatch

### Phase 3: reusable MD recipes

- initializer cues
- request/lock registry libraries
- signal router helpers
- cache/index helper libraries

### Phase 4: optional `x4ai` module

- `AIScript`
- `Order`
- `Interrupts`
- `Handler`
- `Wait`
- `Resume`
- `CreateOrder`

## Bottom line

If we follow GalaxyTrader as the reference mod, the most valuable early framework components are not "every XML tag".

They are:

- strong MD library/cue primitives
- event and signal wiring helpers
- expression/table builders
- reusable guard and initialization macros

That will cover the real complexity in large X4 mods while keeping the door open for AI-script support later.
