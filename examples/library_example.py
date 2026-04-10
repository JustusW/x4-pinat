from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from x4md import (
    Actions,
    Cue,
    Cues,
    DebugText,
    Library,
    MDScript,
    Param,
    Params,
    PathExpr,
    Return,
    RunActions,
    SetValue,
    TableEntry,
    TableExpr,
    TextExpr,
)


document = MDScript(
    name="GalaxyTraderLibraries",
    cues=Cues(
        Library(
            "GT_RequestStatus_Init",
            Params(
                Param("ship"),
            ),
            Actions(
                SetValue(
                    "global.$GT_RequestStatus",
                    exact=TableExpr.of(TableEntry("LastShip", PathExpr.of("this", "ship"))),
                ),
                Return(True),
            ),
            purpose="run_actions",
        ),
        Cue(
            "UseLibrary",
            Actions(
                RunActions(
                    "md.GT_Libraries.GT_RequestStatus_Init",
                    Param("ship", value=PathExpr.of("player", "ship")),
                    result="$initialized",
                ),
                DebugText(TextExpr.quote("Library invoked")),
            ),
            instantiate=True,
        ),
    ),
)

print(document)
