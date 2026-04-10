from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from x4md import (
    AIScript,
    Actions,
    Conditions,
    CreateOrder,
    EventObjectSignalled,
    Handler,
    Interrupts,
    Order,
    Param,
    PathExpr,
    Resume,
    TextExpr,
    Wait,
)


script = AIScript(
    "order.trade.demo",
    Order(
        "DemoOrder",
        Interrupts(
            Handler(
                Conditions(
                    EventObjectSignalled(
                        PathExpr.of("this", "ship"),
                        param=TextExpr.quote("GT_Go"),
                    )
                ),
                Actions(
                    CreateOrder(
                        PathExpr.of("this", "ship"),
                        TextExpr.quote("DockAndWait"),
                        Param("destination", value=PathExpr.of("this", "sector")),
                        immediate=True,
                    ),
                    Resume("main_loop"),
                ),
            )
        ),
        Wait(max="5s"),
        name=TextExpr.quote("Demo Order"),
        category="trade",
        infinite=True,
    ),
    version=3,
)

print(script)
