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

- Total exported classes: 9
- Symbols: `BoolExpr`, `Dynamic`, `Expr`, `ListExpr`, `MoneyExpr`, `PathExpr`, `TableEntry`, `TableExpr`, `TextExpr`

## Project and Extension Files

- Total exported classes: 8
- Symbols: `ContentDependency`, `ContentLibrary`, `ContentText`, `ExtensionContent`, `ExtensionProject`, `GeneratedFile`, `TranslationEntry`, `TranslationPage`

## Mission Director

- Total exported classes: 96
- Symbols: `AbortIf`, `ActionNode`, `Actions`, `AppendListElements`, `AppendToList`, `Break`, `CancelAllOrders`, `CancelCue`, `CancelOrder`, `CheckAll`, `CheckAny`, `CheckValue`, `ConditionNode`, `Conditions`, `Continue`, `CreateList`, `Cue`, `CueChildNode`, `CueSignalledCue`, `Cues`, `DebugText`, `Delay`, `DoAll`, `DoElse`, `DoElseIf`, `DoForEach`, `DoIf`, `DoWhile`, `EditOrderParam`, `EnsureCounter`, `EnsureList`, `EnsurePath`, `EnsureTable`, `EventCueSignalled`, `EventGameLoaded`, `EventGameSaved`, `EventObjectAttacked`, `EventObjectChangedSector`, `EventObjectChangedZone`, `EventObjectDestroyed`, `EventObjectOrderReady`, `EventObjectSignalled`, `EventPlayerAssignedHiredActor`, `EventPlayerCreated`, `EventUITriggered`, `FindBuyOffer`, `FindDockingbay`, `FindGate`, `FindObject`, `FindSector`, `FindSellOffer`, `FindShip`, `FindStation`, `GameLoadedCue`, `GetWareReservation`, `Guard`, `InitializeGlobalsCue`, `InputParam`, `Library`, `MDCreateOrder`, `MDNode`, `MDScript`, `Match`, `MatchBuyer`, `MatchDistance`, `MatchDock`, `MatchGateDistance`, `MatchRelationTo`, `MatchSeller`, `OnAbort`, `Param`, `ParamNode`, `Params`, `PlayerCreatedCue`, `RaiseLuaEvent`, `RemoveFromList`, `RemoveValue`, `RequestRegistryLibrary`, `Return`, `ReturnIf`, `RewardPlayer`, `RunActions`, `SetObjectName`, `SetSkill`, `SetValue`, `ShowNotification`, `ShuffleList`, `SignalCue`, `SignalCueAction`, `SignalCueInstantly`, `SignalObjects`, `SignalRouterCue`, `SortList`, `SortTrades`, `SubstituteText`, `WriteToLogbook`

## AI Script

- Total exported classes: 28
- Symbols: `AINode`, `AIScript`, `AddWareReservation`, `Attention`, `ClampTradeAmount`, `ClearOrderFailure`, `CreateOrder`, `CreatePosition`, `CreateTradeOrder`, `GetJumpPath`, `Goto`, `Handler`, `IncludeInterruptActions`, `InterruptNode`, `Interrupts`, `Label`, `Order`, `OrderChildNode`, `RemoveWareReservation`, `Requires`, `Resume`, `RunScript`, `SetCommand`, `SetCommandAction`, `SetOrderFailed`, `SetOrderState`, `SetOrderSyncpointReached`, `Wait`

## Notes

- This matrix reflects exported API surface, not semantic parity with every X4 node variant.
- Use downstream mod needs to prioritize any additional node additions.
