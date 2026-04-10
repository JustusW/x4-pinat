# X4 MD Transpiler

This project starts a Python library for building X4 Mission Director (MD) XML as a tree of Python objects.

The initial focus is:

- represent XML elements as Python instances
- stringify that object tree into valid XML
- provide a small MD-specific layer for common X4 MD nodes
- expose typed constructors that work well with IDE autocompletion
- cover both Mission Director XML and AI-script XML with clean object-oriented classes

## Implemented components

The library now includes typed builders for the main structures identified from GalaxyTrader:

- core XML: `XmlElement`
- typed expression classes: `Expr`, `TextExpr`, `PathExpr`, `TableExpr`, `ListExpr`, `MoneyExpr`, `BoolExpr`, `TableEntry`, `Dynamic`
- MD document and flow nodes: `MDScript`, `Cues`, `Cue`, `Library`, `Params`, `Param`, `Conditions`, `Actions`, `RunActions`, `SetValue`, `Return`, `DoIf`, `DoElse`, `DoElseIf`, `DoAll`
- MD event and signal nodes: `CheckAny`, `CheckValue`, `EventGameLoaded`, `EventPlayerCreated`, `EventCueSignalled`, `EventObjectSignalled`, `SignalCueInstantly`, `SignalObjects`, `DebugText`
- MD recipe classes: `EnsureTable`, `EnsureList`, `EnsureCounter`, `EnsurePath`, `ReturnIf`, `AbortIf`, `Guard`, `GameLoadedCue`, `PlayerCreatedCue`, `CueSignalledCue`, `SignalCue`, `InitializeGlobalsCue`, `SignalRouterCue`, `RequestRegistryLibrary`
- AI-script classes: `AIScript`, `Order`, `Interrupts`, `Handler`, `Wait`, `Resume`, `CreateOrder`, `Requires`, `Label`, `Goto`

## Package layout

The package is now split by responsibility:

- `x4md/core`
  Core XML primitives
- `x4md/expressions.py`
  Typed expression objects for X4 value strings
- `x4md/md`
  Mission Director nodes, typed node categories, and reusable recipe classes
- `x4md/x4ai`
  AI-script document and order-flow nodes

## Design notes

- `docs/galaxytrader-component-candidates.md`
  Analysis of `GoAhead-at/galaxy_trader_v9`, using the Mk4 routine to identify reusable framework components and to separate MD concerns from AI-script concerns.

## Background research

Egosoft's Mission Director guide describes the core MD document shape for X4:

- the root node is `mdscript`
- `mdscript` contains a single `cues` node
- `cues` contains `cue` and `library` nodes
- a cue may contain `conditions`, `actions`, and nested `cues`

Source:

- https://wiki.egosoft.com/X%20Rebirth%20Wiki/Modding%20support/Mission%20Director%20Guide/

## Quick start

Run the example with:

```powershell
py -3.11 examples\basic_example.py
```

It prints a Mission Director document built from typed classes.

There is also a library-focused example:

```powershell
py -3.11 examples\library_example.py
```

And an AI-script example:

```powershell
py -3.11 examples\ai_script_example.py
```
