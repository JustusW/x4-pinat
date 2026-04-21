# `x4md` XSD Defect Ledger

The XSD-driven test layers (`tests/test_xsd_contract.py` and
`tests/test_xsd_conformance.py`) and the render-time validator
(`src/x4md/_xsd_validation.py`) catch every place where a Python class
in `x4md` produces XML the authoritative X4 XSDs
(`.x4-refs/md.xsd`, `.x4-refs/aiscripts.xsd`) reject. This document is
the running ledger.

## Currently tracked gaps

### Shipped-XSD gap: `<goto>` (permanent)

- **Python:** `x4md.x4ai.nodes.Goto("label")` emits
  `<goto label="label"/>`.
- **XSD:** `aiscripts.xsd` has no `<goto>` element, yet vanilla X4 AI
  scripts use it everywhere to loop back to `<label>` markers inside
  the main `<actions>` block.
- **Verdict:** Incomplete upstream XSD, not a library bug. The tag is
  registered in `x4md._xsd_validation.KNOWN_XSD_GAPS`, so
  `validate_document` / `to_document(validate=True)` accept `<goto>`.
  `validate_document_raw` still reports it so a future Egosoft schema
  release that fixes the gap flips a regression test in
  `tests/test_render_time_validation.py` and prompts removal from the
  allow-list.

Nothing else is currently deferred. All four previously-tracked class-
design defects have been fixed; see the history section below for a
record of the changes that went in.

## Fixed defects (history)

### 1. `GetJumpPath` attributes vs. child elements — FIXED

Previous behaviour emitted
`<get_jump_path result="$v" start="a" end="b"/>`, which violated
`common.xsd` on five counts (missing required `component`, three
`result`/`start`/`end` attributes that the schema does not allow, and a
missing `<start>` child).

The class now takes the XSD shape: a required `component=` attribute,
and either raw expression `start=`/`end=` values (auto-wrapped into
`<start object="..."/>` / `<end object="..."/>` children) or explicit
`Start` / `End` nodes for finer-grained control.

Added classes: `x4md.x4ai.Start`, `x4md.x4ai.End`. All three
participate in the XSD contract registry. A short-lived `result=`
alias (with `DeprecationWarning`) existed during the GalaxyProtector
migration; it has since been removed.

### 2. `Goto` — RECLASSIFIED AS PERMANENT XSD GAP

No code change: `Goto` keeps emitting `<goto label="..."/>` because
vanilla X4 does. The entry is tracked in `KNOWN_XSD_GAPS` (see above).

### 3. `OnAbort` misfiled under MD — FIXED

Moved from `x4md.md.document.OnAbort` (`CueChildNode`, no corresponding
element in `md.xsd`) to `x4md.x4ai.nodes.OnAbort` (`OrderChildNode`).
The AI document writer already hoists `<on_abort>` to the correct
sibling position under `<aiscript>` via
`AIScript._rewrite_children`, so passing `OnAbort(...)` inside an
`Order(...)` now produces schema-valid output.

Breaking change: `from x4md import OnAbort` still works, but
`from x4md.md import OnAbort` does not. `x4md.md.OnAbort` callers that
intended an MD cue cleanup should rewrite their cue logic via a
secondary cue (`SignalCueInstantly` into a cleanup cue) since there is
no MD equivalent to `<on_abort>`.

### 4. `Delay` base class — NOT AN ACTUAL DEFECT

The earlier entry was stale. `md.xsd` *does* declare `<delay>` as a
direct `<cue>` child, and `x4md.md.document.Delay` has always been a
`CueChildNode`, not an `ActionNode`. The class is correct as-is; the
entry has been removed.

### 5. `Handler` loose actions — FIXED (in an earlier pass)

`Handler._rewrite_children` wraps loose action nodes into a single
`<actions>` child, matching the `interrupts`-context handler content
model in `aiscripts.xsd`.

## Render-time validation

`MDScript.to_document(validate=True)` and
`AIScript.to_document(validate=True)` now run the rendered document
through the right XSD and raise `x4md.XsdValidationError` if anything
outside `KNOWN_XSD_GAPS` remains. `MDScript.validate()` /
`AIScript.validate()` return a list of `XsdValidationIssue`s for
callers that prefer structured reporting over exceptions. See
`x4md/_xsd_validation.py` for the implementation and
`tests/test_render_time_validation.py` for the contract.

The default `validate` flag is ``False`` so existing callers do not
break in-place; extension build scripts should flip it on (and treat a
raised `XsdValidationError` as a build failure).

## How to rerun the schema checks

```bash
cd PythonToMDTranspiler
./.venv/Scripts/python.exe -m pytest tests/test_xsd_contract.py tests/test_xsd_conformance.py tests/test_render_time_validation.py
```

To validate a freshly-built `GalaxyProtector` install:

```bash
cd GalaxyProtector
../PythonToMDTranspiler/.venv/Scripts/python.exe build.py
../PythonToMDTranspiler/.venv/Scripts/python.exe -c "
from pathlib import Path
from x4md import validate_document

install = Path(r'E:\\SteamLibrary\\steamapps\\common\\X4 Foundations\\extensions\\galactic_trade_protector')
for folder in ('md', 'aiscripts'):
    for f in sorted((install / folder).glob('*.xml')):
        issues = validate_document(f.read_text(encoding='utf-8'))
        print(f'{f.name}: {len(issues)} issue(s)')
        for issue in issues[:10]:
            print(f'  - {issue}')
"
```
