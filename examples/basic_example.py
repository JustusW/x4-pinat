from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from x4md import (
    Actions,
    CheckAny,
    Conditions,
    Cue,
    Cues,
    DebugText,
    EventGameLoaded,
    EventPlayerCreated,
    MDScript,
    Param,
    PathExpr,
    RunActions,
    SetValue,
    SignalCueInstantly,
    TableEntry,
    TableExpr,
    TextExpr,
)


document = MDScript(
    name="GalaxyTraderBootstrap",
    cues=Cues(
        Cue(
            "SystemInit",
            Conditions(
                CheckAny(
                    EventGameLoaded(),
                    EventPlayerCreated(),
                )
            ),
            Actions(
                SetValue(
                    "global.$GT_State",
                    exact=TableExpr.of(
                        TableEntry("Ready", True),
                        TableEntry("LastUpdate", PathExpr.of("player", "age")),
                    ),
                ),
                RunActions(
                    "md.GT_Libraries_General.GT_RequestStatus_Init",
                ),
                DebugText(TextExpr.quote("Python-generated MD initialized"), chance=100),
                SignalCueInstantly("BootstrapComplete", param=PathExpr.of("player", "age")),
            ),
            instantiate=True,
            version=1,
        ),
        Cue(
            "BootstrapComplete",
            Actions(
                DebugText(TextExpr.quote("Bootstrap complete")),
                RunActions(
                    "md.GT_Libraries_General.GT_RequestRegistry_Acquire",
                    Param("ship", value=PathExpr.of("player", "ship")),
                    Param("traceId", value=TextExpr.quote("demo")),
                    result="$acquired",
                ),
            ),
        )
    ),
)

print(document)
