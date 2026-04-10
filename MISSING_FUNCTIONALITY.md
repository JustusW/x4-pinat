# Missing Functionality Assessment for Full GalaxyTrader Implementation

This document provides a comprehensive assessment of what's still needed to fully implement GalaxyTrader using the X4 MD Transpiler library.

## Summary Statistics

- **GalaxyTrader Size:** 45 MD files (~45,000 lines) + 25 AI-script files
- **Current Library Coverage:** ~70% of required nodes
- **Missing Node Classes:** ~35-40 nodes

---

## ✅ IMPLEMENTED - Core Framework (Complete)

### Document Structure
- [x] `MDScript` - MD document root
- [x] `Cues` / `Cue` - Cue containers and definitions
- [x] `Library` - Library definitions
- [x] `Params` / `Param` / `InputParam` - Parameter definitions
- [x] `Actions` / `Conditions` - Action/condition containers

### Expressions (Complete)
- [x] `Expr`, `TextExpr`, `PathExpr`, `ListExpr`, `TableExpr`, `MoneyExpr`, `BoolExpr`
- [x] `Dynamic`, `TableEntry`
- [x] Expression rendering and type safety

### Basic Actions (18/18)
- [x] `SetValue`, `RemoveValue`
- [x] `AppendToList`, `RemoveFromList`
- [x] `DoIf`, `DoElse`, `DoElseIf`, `DoAll`, `DoWhile`, `DoForEach`
- [x] `Break`, `Continue`
- [x] `Return`, `RunActions`
- [x] `DebugText`
- [x] `SignalCueInstantly`, `SignalCueAction`, `SignalObjects`
- [x] `CancelCue`

### Order Management (Complete for MD)
- [x] `CreateOrder` (MD version)
- [x] `CancelOrder`, `CancelAllOrders`

### UI & Notifications (Complete)
- [x] `WriteToLogbook`
- [x] `ShowNotification`

### Miscellaneous Actions
- [x] `SetObjectName`
- [x] `RaiseLuaEvent`

### Basic Conditions (10/10)
- [x] `CheckValue`, `CheckAny`, `CheckAll`
- [x] `EventGameLoaded`, `EventPlayerCreated`, `EventGameSaved`
- [x] `EventCueSignalled`, `EventObjectSignalled`
- [x] `EventObjectOrderReady`, `EventObjectDestroyed`
- [x] `EventObjectChangedZone`
- [x] `EventPlayerAssignedHiredActor`
- [x] `EventUITriggered`

### Recipe Helpers (Complete)
- [x] `EnsureTable`, `EnsureList`, `EnsureCounter`, `EnsurePath`
- [x] `ReturnIf`, `AbortIf`, `Guard`
- [x] `GameLoadedCue`, `PlayerCreatedCue`, `CueSignalledCue`
- [x] `SignalCue` (recipe), `SignalRouterCue`
- [x] `InitializeGlobalsCue`, `RequestRegistryLibrary`

### AI-Script (Basic - 8/8)
- [x] `AIScript`, `Order`, `Requires`, `Interrupts`, `Handler`
- [x] `Wait`, `Resume`, `Label`, `Goto`
- [x] `CreateOrder` (AI version)

---

## ❌ MISSING - Critical MD Actions (~20 nodes)

### Find/Query Actions (Priority: HIGH)
Used extensively throughout GalaxyTrader for finding game objects.

- [ ] `FindBuyOffer` - Find buy offers in sectors/stations
  - Usage: ~50+ times in GT
  - Attributes: `space`, `tradepartner`, `multiple`, `result`, child `<match>` nodes

- [ ] `FindSellOffer` - Find sell offers in sectors/stations
  - Usage: ~50+ times in GT
  - Similar to FindBuyOffer

- [ ] `FindStation` - Find stations matching criteria
  - Usage: ~20+ times
  - Attributes: `name`, `space`, `multiple`, `tradesknownto`, `sortbydistanceto`

- [ ] `FindSector` - Find sectors in range
  - Usage: ~10+ times
  - Attributes: `name`, `space`, `multiple`

- [ ] `FindGate` - Find gates in sector
  - Usage: ~5+ times
  - Attributes: `name`, `space`, `multiple`

- [ ] `FindDockingbay` - Find available docking bays
  - Usage: ~5+ times
  - Attributes: `name`, `object`, `checkoperational`, `multiple`

- [ ] `FindShip` - Find ships matching criteria
  - Usage: ~3+ times
  - Attributes: `name`, `space`, `multiple`, child `<match>` nodes

- [ ] `FindShipByTrueOwner` - Find ships by true owner
  - Usage: ~2+ times

- [ ] `FindObject` - Generic object finder
  - Usage: ~5+ times

- [ ] `FindClusterInRange` - Find clusters within range
  - Usage: ~1+ times

### Get/Retrieve Actions (Priority: HIGH)
- [ ] `GetWareReservation` - Get ware reservation amount
  - Usage: ~10+ times
  - Attributes: `object`, `ware`, `type`, `virtual`, `result`

- [ ] `GetWareDefinition` - Get ware definition data
  - Usage: ~2+ times

### List Manipulation (Priority: MEDIUM)
- [ ] `CreateList` - Create a new list variable
  - Usage: ~10+ times
  - Attributes: `name`

- [ ] `ShuffleList` - Randomize list order
  - Usage: ~2+ times
  - Attributes: `list`

- [ ] `SortList` - Sort list by criteria
  - Usage: ~2+ times
  - Attributes: `list`, child sort criteria

- [ ] `AppendListElements` - Append multiple elements
  - Usage: ~2+ times
  - Attributes: `name`, `other`

### Trade-Specific Actions (Priority: HIGH for GT)
- [ ] `SortTrades` - Sort trade opportunities
  - Usage: ~5+ times (GT-specific library)
  - Custom sorting logic for trade evaluation

- [ ] `StoreTradOfferSnapshot` - Store trade offer state
  - Usage: ~2+ times

- [ ] `CreateTradeOrder` - Create trade-specific order
  - Usage: AI-scripts only

### Text/String Actions (Priority: MEDIUM)
- [ ] `SubstituteText` - String substitution/formatting
  - Usage: ~3+ times
  - Attributes: `text`, `source`

### Order Manipulation (Priority: MEDIUM)
- [ ] `EditOrderParam` - Modify order parameters
  - Usage: ~5+ times
  - Attributes: `object`, `param`, `value`

### Equipment/Modification (Priority: LOW)
- [ ] `AddEquipmentMods` - Add equipment modifications
  - Usage: ~1+ times
  - Attributes: `object`, `macro`

### Skill/Progression (Priority: MEDIUM)
- [ ] `SetSkill` - Set NPC skill level
  - Usage: ~5+ times
  - Attributes: `object`, `skill`, `value`, `min`, `max`, `comment`

- [ ] `RewardPlayer` - Give player rewards
  - Usage: ~1+ times
  - Attributes: `money`, `notificationtext`

### Trade Subscriptions (Priority: LOW)
- [ ] `AddTradeSubscription` - Subscribe to trade events
  - Usage: ~1+ times

---

## ❌ MISSING - MD Events/Conditions (~10 nodes)

### Object Events (Priority: HIGH)
- [ ] `EventObjectAttacked` - Object under attack
  - Usage: ~2+ times

- [ ] `EventObjectDocked` - Object completed docking
  - Usage: ~2+ times

- [ ] `EventObjectIncomingMissile` - Missile warning
  - Usage: ~1+ times

- [ ] `EventObjectOrderCancelled` - Order was cancelled
  - Usage: ~2+ times

- [ ] `EventObjectSubordinateRemoved` - Subordinate removed
  - Usage: ~1+ times

- [ ] `EventObjectCommanderSet` - Commander assigned
  - Usage: ~1+ times

### Faction Events (Priority: LOW)
- [ ] `EventFactionActivated` - Faction becomes active
  - Usage: ~1+ times

- [ ] `EventFactionDeactivated` - Faction becomes inactive
  - Usage: ~1+ times

### Game Events (Priority: LOW)
- [ ] `EventGameStarted` - New game started (vs loaded)
  - Usage: ~1+ times

- [ ] `EventUniverseGenerated` - Universe generation complete
  - Usage: ~1+ times

- [ ] `EventPlayerBuildFinishedComponents` - Player construction complete
  - Usage: ~1+ times

---

## ❌ MISSING - AI-Script Nodes (~25 nodes)

### AI Control Flow (Priority: HIGH)
- [ ] `RunScript` - Execute another script
  - Usage: ~10+ times in AI

- [ ] `Attention` - Set attention object
  - Usage: ~5+ times

- [ ] `IncludeInterruptActions` - Include interrupt handlers
  - Usage: ~5+ times

### AI Order Management (Priority: HIGH)
- [ ] `SetOrderFailed` - Mark order as failed
  - Usage: ~10+ times

- [ ] `SetOrderState` - Set order state
  - Usage: ~5+ times

- [ ] `SetOrderSyncpointReached` - Mark synchronization point
  - Usage: ~5+ times

- [ ] `ClearOrderFailure` - Clear failure state
  - Usage: ~2+ times

### AI Movement/Navigation (Priority: HIGH)
- [ ] `CreatePosition` - Create position object
  - Usage: ~5+ times

- [ ] `GetJumpPath` - Calculate jump route
  - Usage: ~3+ times

### AI Trading (Priority: HIGH for GT)
- [ ] `ClampTradeAmount` - Limit trade quantity
  - Usage: ~5+ times

- [ ] `CreateTradeOrder` - Create trade order (AI-specific)
  - Usage: ~5+ times

### AI Resource Management (Priority: MEDIUM)
- [ ] `FindAsteroidWithYieldInSector` - Find minable asteroids
  - Usage: ~2+ times

- [ ] `FindClosestResource` - Find nearest resource
  - Usage: ~2+ times

- [ ] `FindResource` - Find resource by criteria
  - Usage: ~2+ times

### AI Ware Reservations (Priority: HIGH for GT)
- [ ] `AddWareReservation` - Reserve ware amount
  - Usage: ~10+ times

- [ ] `RemoveWareReservation` - Remove ware reservation
  - Usage: ~10+ times

- [ ] `AddYieldReservation` - Reserve mining yield
  - Usage: ~2+ times

### AI Cargo Management (Priority: MEDIUM)
- [ ] `DropCargo` - Jettison cargo
  - Usage: ~2+ times

### AI Command/Commander (Priority: MEDIUM)
- [ ] `SetCommand` - Set command interface
  - Usage: ~5+ times

- [ ] `SetCommandAction` - Set command action
  - Usage: ~5+ times

- [ ] `SetObjectCommander` - Assign commander
  - Usage: ~3+ times

- [ ] `RemoveObjectCommander` - Remove commander
  - Usage: ~3+ times

### AI Debugging (Priority: LOW)
- [ ] `DebugToFile` - Write debug to file
  - Usage: ~2+ times

- [ ] `GenerateShortageReports` - Generate trade reports
  - Usage: ~1+ times (GT-specific)

### AI Gravidar (Priority: LOW)
- [ ] `CountGravidarContacts` - Count detected objects
  - Usage: ~1+ times

- [ ] `EventGravidarHasScanned` - Scan completion event
  - Usage: ~1+ times

### AI Misc Events (Priority: MEDIUM)
- [ ] `EventObjectChangedSector` - Sector change event
  - Usage: ~5+ times

- [ ] `EventObjectEnteredAnomaly` - Anomaly entry event
  - Usage: ~1+ times

- [ ] `EventObjectEnteredGate` - Gate transit event
  - Usage: ~1+ times

---

## ❌ MISSING - Match Conditions (~8 nodes)

Used as children of find/requires nodes for filtering:

- [ ] `Match` - Generic match condition
  - Usage: ~20+ times

- [ ] `MatchBuyer` - Match buyer criteria
  - Usage: ~10+ times (GT-specific)

- [ ] `MatchSeller` - Match seller criteria
  - Usage: ~10+ times (GT-specific)

- [ ] `MatchDistance` - Match distance range
  - Usage: ~5+ times

- [ ] `MatchGateDistance` - Match gate jumps
  - Usage: ~15+ times (GT-specific)

- [ ] `MatchDock` - Match docking criteria
  - Usage: ~5+ times

- [ ] `MatchRelationTo` - Match faction relation
  - Usage: ~3+ times

- [ ] `MatchContext` - Match context criteria
  - Usage: ~2+ times (AI-scripts)

---

## ❌ MISSING - Cue Children (~3 nodes)

- [ ] `OnAbort` - Actions to run when cue is aborted
  - Usage: ~10+ times
  - Contains action nodes

- [ ] `Delay` - Delay before cue activation
  - Usage: ~5+ times
  - Attributes: `exact`, `min`, `max`

---

## 📊 PRIORITY ASSESSMENT

### **Critical Path (Must Have for GT):**
1. **Find actions** (FindBuyOffer, FindSellOffer, FindStation, FindSector) - ~50% of GT logic
2. **GetWareReservation** - Core trading logic
3. **Match conditions** (MatchBuyer, MatchSeller, MatchGateDistance) - Trade filtering
4. **AI ware reservations** (AddWareReservation, RemoveWareReservation) - AI trading
5. **SetSkill** - Pilot progression system

### **High Priority (Needed for full GT):**
1. **SortTrades** - Trade opportunity ranking
2. **CreateList** - Data structure management
3. **AI order management** (SetOrderFailed, SetOrderState)
4. **RunScript** - AI script composition
5. **OnAbort** - Error handling

### **Medium Priority (Used but not critical):**
1. **EditOrderParam** - Order modification
2. **FindDockingbay, FindGate** - Navigation
3. **ShuffleList, SortList** - List utilities
4. **SubstituteText** - String formatting
5. **AI movement** (CreatePosition, GetJumpPath)

### **Low Priority (Rarely used):**
1. **Faction events** - Edge cases
2. **AddEquipmentMods** - Ship customization
3. **Gravidar** - Specialized detection
4. **RewardPlayer** - Player rewards
5. **Debug utilities** - Development tools

---

## 📈 IMPLEMENTATION ROADMAP

### Phase 1: Trading Foundation (Critical - 15 nodes)
- FindBuyOffer, FindSellOffer
- GetWareReservation
- MatchBuyer, MatchSeller, MatchGateDistance
- FindStation, FindSector
- CreateList
- SortTrades
- SetSkill
- OnAbort
- **Estimated effort:** 2-3 days
- **Coverage after:** ~85%

### Phase 2: AI-Script Completion (High - 12 nodes)
- AddWareReservation, RemoveWareReservation
- SetOrderFailed, SetOrderState, ClearOrderFailure
- RunScript
- CreateTradeOrder, ClampTradeAmount
- Attention, IncludeInterruptActions
- EventObjectChangedSector
- Match (generic)
- **Estimated effort:** 2-3 days
- **Coverage after:** ~95%

### Phase 3: Utilities & Polish (Medium - 15 nodes)
- EditOrderParam
- FindDockingbay, FindGate, FindObject
- ShuffleList, SortList, AppendListElements
- SubstituteText
- CreatePosition, GetJumpPath
- MatchDistance, MatchDock, MatchRelationTo
- Delay
- Additional object events
- **Estimated effort:** 2-3 days
- **Coverage after:** ~98%

### Phase 4: Edge Cases (Low - 10 nodes)
- All remaining events
- Faction events
- Gravidar nodes
- Equipment/build nodes
- Debug utilities
- **Estimated effort:** 1-2 days
- **Coverage after:** 100%

---

## 🎯 RECOMMENDATIONS

### For Basic GalaxyTrader Transpilation:
Implement **Phase 1 only** (15 nodes). This provides the critical trading infrastructure and gets you to ~85% coverage, sufficient for transpiling most GT files.

### For Full GalaxyTrader Implementation:
Complete **Phases 1-2** (27 nodes total). This gets you to ~95% coverage and handles all core MD files and AI-scripts.

### For Complete X4 MD Library:
Complete all 4 phases (~52 additional nodes). This makes the library suitable for any X4 mod, not just GalaxyTrader.

---

## 📝 NOTES

1. **Match conditions** are used as child elements of find/requires nodes and need special handling
2. **OnAbort** is a cue child node, similar to Actions/Conditions
3. Many AI-script nodes are **very similar to MD nodes** - can reuse patterns
4. **SortTrades** and **GenerateShortageReports** are GT-specific custom library calls
5. Some nodes like **MatchGateDistance** are heavily used in GT but rare elsewhere

---

**Total Missing Nodes:** ~52
**Critical for GT:** ~15
**Current Coverage:** 70%
**After Phase 1:** 85%
**After Phase 2:** 95%
