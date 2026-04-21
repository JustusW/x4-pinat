# Known `x4md` Class-Design Defects Uncovered by Schema Tests

The XSD-driven test layers (`tests/test_xsd_contract.py` and
`tests/test_xsd_conformance.py`) surfaced several places where a Python
class in `x4md` produces XML that the authoritative X4 XSDs
(`.x4-refs/md.xsd`, `.x4-refs/aiscripts.xsd`) reject. The cheap fixes
are already in `x4md` and its tests. The defects below are more invasive
and are tracked here instead of silencing the relevant tests.

Entries are sorted by blast radius (most severe first). Each entry
lists the XSD requirement, the Python class that violates it, how many
XSD errors the defect contributes to `GalaxyProtector`'s output, and the
intended fix.

## 1. `GetJumpPath` uses attributes instead of child elements

**Python:** `x4md.x4ai.nodes.GetJumpPath` emits
`<get_jump_path result="$v" start="a" end="b"/>`.

**XSD (`aiscripts.xsd`):** `<get_jump_path>` requires a `component`
attribute and takes `<start>` / `<end>` as *child elements*, not
attributes. `result` is not a declared attribute at all - the result
is returned into a variable via a different mechanism (typically a
`component`-typed variable binding).

**Impact:** Contributes 5 schema errors to the
`galactic_trade_protector` QRF AI script today. The mod runs anyway
because X4's runtime appears permissive here, but any strict XSD
validator will reject the output.

**Fix:** Rewrite `GetJumpPath` to accept `component=` (required),
`refobject=`, `multiple=`, etc. as attributes, and `start=` / `end=`
as child-element expressions. Update `GalaxyProtector/builders/orders.py`
accordingly; consult a vanilla X4 AI script that uses `<get_jump_path>`
for the idiomatic shape.

## 2. `Goto` emits an element that `aiscripts.xsd` does not declare

**Python:** `x4md.x4ai.nodes.Goto("label")` emits
`<goto label="label"/>`.

**XSD:** `aiscripts.xsd` has no `<goto>` element. `<resume label="..."/>`
exists, but semantically it is "resume at label after an interrupt",
not "unconditionally jump to label inside the main actions block".

**Impact:** Contributes 1 schema error to the QRF AI script.

**Reality check:** Vanilla X4 AI scripts *do* use `<goto>`. This is a
case where the shipped XSD is incomplete rather than the library being
wrong. The correct fix is probably to:

  1. Keep `Goto` as-is.
  2. Add a targeted xfail in `test_xsd_conformance.py` when validating
     scripts that use `<goto>`, with a docstring explaining the XSD gap.
  3. Track the gap so we re-validate against future Egosoft XSD
     releases.

## 3. `OnAbort` is declared as an MD cue child but `md.xsd` has no `<on_abort>`

**Python:** `x4md.md.document.OnAbort` extends `CueChildNode`, so it is
valid to drop inside an MD `<cue>`.

**XSD (`md.xsd`):** No `<on_abort>` element exists anywhere in
`md.xsd`. The tag is only declared in `aiscripts.xsd` as a top-level
sibling of `<aiscript>`'s main `<actions>`.

**Impact:** Any MD script that uses `OnAbort` will be rejected by
`md.xsd`. GP does not use it today, but `tests/test_md_document.py`
does (as a builder-level test, not a schema-level one).

**Fix:** Move `OnAbort` to `x4md.x4ai.nodes`, re-base it on
`OrderChildNode`, and remove the MD-side import. Alternatively, delete
the class entirely if no user ever emitted it into an MD document.

## 4. `Delay` is filed as `ActionNode` but is only valid as a direct `<cue>` child

**Python:** `x4md.md.actions.Delay` extends `ActionNode` and renders
`<delay exact="..."/>` anywhere an action is legal.

**XSD (`md.xsd`):** The `<delay>` element only appears inside `<cue>`
directly (the XSD model is `<cue><delay .../><conditions/>...`).
Inserting `<delay>` inside `<actions>` produces
*Unexpected child with tag 'delay'*.

**Impact:** None in `GalaxyProtector` today; would break any future
caller who tried to use it inside an action block.

**Fix:** Either rename `Delay` to `CueDelay` and re-base it as
`CueChildNode`, or replace action-scope usage with
`Wait(exact="...")` (the AI-script equivalent). MD scripts that want
a delayed action typically split the action into a second cue chained
via `signal_cue_instantly`.

## 5. `Handler` previously accepted loose actions

**Status: FIXED.** `Handler._rewrite_children` now hoists loose
actions into a single `<actions>` child, matching the
``interrupts`` context of `<handler>` in `aiscripts.xsd`.

## Remaining schema errors in `GalaxyProtector` after current fixes

After the cheap fixes in this pass, validating the installed
`galactic_trade_protector` extension against the XSDs yields:

```
galactic_trade_protector_dispatch.xml: 0 errors
order.galactictradeprotector.quickreactionforce.xml: 6 errors
   - missing required attribute 'component'
   - 'result' attribute not allowed for element
   - 'start' attribute not allowed for element
   - 'end' attribute not allowed for element
   - The content of element 'get_jump_path' is not complete. Tag 'start' expected.
   - Unexpected child with tag 'goto' at position 15.
```

The first five are from defect #1 above (`GetJumpPath`). The last is
defect #2 (`Goto`).

## How to rerun the schema checks

```bash
cd PythonToMDTranspiler
./.venv/Scripts/python.exe -m pytest tests/test_xsd_contract.py tests/test_xsd_conformance.py
```

To validate a freshly-built `GalaxyProtector` install:

```bash
cd GalaxyProtector
../PythonToMDTranspiler/.venv/Scripts/python.exe build.py
../PythonToMDTranspiler/.venv/Scripts/python.exe -c "
import sys, os, glob
sys.path.insert(0, r'../PythonToMDTranspiler/src')
sys.path.insert(0, r'../PythonToMDTranspiler/tests')
from xsd_support import md_schema, ai_schema
base = r'E:\\SteamLibrary\\steamapps\\common\\X4 Foundations\\extensions\\galactic_trade_protector'
for schema, folder in [(md_schema(), 'md'), (ai_schema(), 'aiscripts')]:
    for f in glob.glob(os.path.join(base, folder, '*.xml')):
        errs = list(schema.iter_errors(open(f, encoding='utf-8').read()))
        print(os.path.basename(f), len(errs), 'errors')
        for e in errs[:10]: print('  -', e.reason)
"
```
