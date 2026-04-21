# X4-PINAT Capability Status (Auto-Generated)

This snapshot is generated from exported class symbols in `x4md.__all__`.

Last refreshed: 2026-04-21

## Coverage Position

- Core MD and AI generation primitives are broadly available.
- Remaining gaps are mostly niche/specialized nodes outside the common scaffolding path.

## Core XML

- Total exported classes: 1
- Symbols: `XmlElement`

## Expressions

- Total exported classes: 10
- Symbols: `BoolExpr`, `Dynamic`, `Expr`, `ListExpr`, `MoneyExpr`, `PathExpr`, `TableEntry`, `TableExpr`, `TextExpr`, `X4ExpressionWarning`

## Project and Extension Files

- Total exported classes: 8
- Symbols: `ContentDependency`, `ContentLibrary`, `ContentText`, `ExtensionContent`, `ExtensionProject`, `GeneratedFile`, `TranslationEntry`, `TranslationPage`

## Mission Director

- Total exported classes: 96
- Symbols: `AbortIf`, `ActionNode`, `Actions`, `AppendListElements`, `AppendToList`, `Break`, `CancelAllOrders`, `CancelCue`, `CancelOrder`, `CheckAll`, `CheckAny`, `CheckValue`, `ConditionNode`, `Conditions`, `Continue`, `CreateList`, `Cue`, `CueChildNode`, `CueSignalledCue`, `Cues`, `DebugText`, `Delay`, `DoAll`, `DoElse`, `DoElseIf`, `DoForEach`, `DoIf`, `DoWhile`, `EditOrderParam`, `EnsureCounter`, `EnsureList`, `EnsurePath`, `EnsureTable`, `EventCueSignalled`, `EventGameLoaded`, `EventGameSaved`, `EventObjectAttacked`, `EventObjectChangedSector`, `EventObjectChangedZone`, `EventObjectDestroyed`, `EventObjectOrderReady`, `EventObjectSignalled`, `EventPlayerAssignedHiredActor`, `EventPlayerCreated`, `EventUITriggered`, `FindBuyOffer`, `FindDockingbay`, `FindGate`, `FindObject`, `FindSector`, `FindSellOffer`, `FindShip`, `FindStation`, `GameLoadedCue`, `GetWareReservation`, `Guard`, `InitializeGlobalsCue`, `InputParam`, `Library`, `MDCreateOrder`, `MDNode`, `MDScript`, `Match`, `MatchBuyer`, `MatchDistance`, `MatchDock`, `MatchGateDistance`, `MatchRelationTo`, `MatchSeller`, `OnAbort`, `Param`, `ParamNode`, `Params`, `PlayerCreatedCue`, `RaiseLuaEvent`, `RemoveFromList`, `RemoveValue`, `RequestRegistryLibrary`, `Return`, `ReturnIf`, `RewardPlayer`, `RunActions`, `SetObjectName`, `SetSkill`, `SetValue`, `ShowNotification`, `ShuffleList`, `SignalCue`, `SignalCueAction`, `SignalCueInstantly`, `SignalObjects`, `SignalRouterCue`, `SortList`, `SortTrades`, `SubstituteText`, `WriteToLogbook`

## AI Script

- Total exported classes: 30
- Symbols: `AINode`, `AIScript`, `AddWareReservation`, `Attention`, `ClampTradeAmount`, `ClearOrderFailure`, `CreateOrder`, `CreatePosition`, `CreateTradeOrder`, `GetJumpPath`, `Goto`, `Handler`, `IncludeInterruptActions`, `InterruptNode`, `Interrupts`, `Label`, `MoveTo`, `Order`, `OrderChildNode`, `RemoveWareReservation`, `Requires`, `Resume`, `RunScript`, `SetCommand`, `SetCommandAction`, `SetOrderFailed`, `SetOrderState`, `SetOrderSyncpointReached`, `Wait`, `X4OrderCategoryWarning`

## Notes

- This matrix reflects exported API surface, not semantic parity with every X4 node variant.
- Use downstream mod needs to prioritize any additional node additions.

## Build-Time Validators

These validators raise or warn at node construction so latent X4
debuglog failures never ship:

- `validate_md_lvalue` (enforced by `SetValue`, `RemoveValue`,
  `AppendToList`, `RemoveFromList`, `CreateList`, `ShuffleList`,
  `SortList`): rejects bareword keys under a `$`-prefixed owner.
  Prevents silent `Failed to set table[].<key>` failures at run time.
- `WriteToLogbook` (`VALID_LOGBOOK_CATEGORIES`,
  `VALID_LOGBOOK_INTERACTIONS`): rejects unknown category and
  interaction values.
- `Order` (`infinite=True` requires a reachable
  `<set_order_syncpoint_reached/>`): prevents the
  ``"returned but no new order"`` log flood.
- `Order` `category` (`X4OrderCategoryWarning`): warns when the
  category is outside the `ordercategorylookup` enum.
- `Attention` (`VALID_ATTENTION_LEVELS`): rejects non-`attentionlookup`
  values, and its signature now enforces the correct
  *attention-level section* shape rather than the invalid
  ``<attention object="…"/>`` action shape. Use `MoveTo` for travel.
- `Cue` (no `<return>`): rejects early-return actions in cue bodies
  where they would silently abort the cue.
