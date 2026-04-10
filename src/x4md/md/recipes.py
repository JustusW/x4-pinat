"""Higher-level MD recipe classes."""

from __future__ import annotations

from x4md.expressions import PathExpr, TableEntry, TableExpr, TextExpr

from .actions import Actions, DebugText, DoElse, DoIf, Param, Params, Return, SetValue, SignalObjects
from .conditions import Conditions, EventCueSignalled, EventGameLoaded, EventObjectSignalled, EventPlayerCreated
from .document import Cue, Library
from .types import ActionNode


class EnsureTable(DoIf):
    def __init__(self, name: str) -> None:
        super().__init__(f"not {name}?", SetValue(name, exact="table[]"))


class EnsureList(DoIf):
    def __init__(self, name: str) -> None:
        super().__init__(f"not {name}?", SetValue(name, exact="[]"))


class EnsureCounter(DoIf):
    def __init__(self, name: str, initial: object = 0) -> None:
        super().__init__(f"not {name}?", SetValue(name, exact=initial))


class EnsurePath(DoIf):
    def __init__(self, name: str, exact: object) -> None:
        super().__init__(f"not {name}?", SetValue(name, exact=exact))


class ReturnIf(DoIf):
    def __init__(self, condition: object, value: object) -> None:
        super().__init__(condition, Return(value))


class AbortIf(DoIf):
    def __init__(self, condition: object, *actions: ActionNode) -> None:
        super().__init__(condition, *actions, Return(False))


class Guard(DoIf):
    def __init__(self, condition: object, *then: ActionNode, else_: tuple[ActionNode, ...] = ()) -> None:
        children: list[ActionNode] = list(then)
        if else_:
            children.append(DoElse(*else_))
        super().__init__(condition, *children)


class GameLoadedCue(Cue):
    def __init__(self, name: str, *actions: ActionNode, instantiate: bool = True) -> None:
        super().__init__(name, Conditions(EventGameLoaded()), Actions(*actions), instantiate=instantiate)


class PlayerCreatedCue(Cue):
    def __init__(self, name: str, *actions: ActionNode, instantiate: bool = True) -> None:
        super().__init__(name, Conditions(EventPlayerCreated()), Actions(*actions), instantiate=instantiate)


class CueSignalledCue(Cue):
    def __init__(self, name: str, *actions: ActionNode, instantiate: bool = True) -> None:
        super().__init__(name, Conditions(EventCueSignalled()), Actions(*actions), instantiate=instantiate)


class SignalCue(Cue):
    def __init__(
        self,
        name: str,
        *,
        object_expr: object,
        signal_name: object,
        actions: tuple[ActionNode, ...],
        instantiate: bool = True,
    ) -> None:
        super().__init__(
            name,
            Conditions(EventObjectSignalled(object_expr, param=signal_name)),
            Actions(*actions),
            instantiate=instantiate,
        )


class InitializeGlobalsCue(Cue):
    def __init__(self, name: str, *initializers: ActionNode) -> None:
        super().__init__(
            name,
            Conditions(EventGameLoaded()),
            Actions(*initializers),
            instantiate=True,
            version=1,
        )


class SignalRouterCue(Cue):
    def __init__(
        self,
        name: str,
        *,
        listen_object: object,
        listen_param: object,
        emit_object: object,
        emit_param: object,
        payload: object | None = None,
    ) -> None:
        super().__init__(
            name,
            Conditions(EventObjectSignalled(listen_object, param=listen_param)),
            Actions(SignalObjects(emit_object, emit_param, param2=payload)),
            instantiate=True,
        )


class RequestRegistryLibrary(Library):
    def __init__(self, name: str = "RequestRegistryAcquire") -> None:
        super().__init__(
            name,
            Params(
                Param("ship"),
                Param("traceId", default=TextExpr.quote("")),
            ),
            Actions(
                EnsureTable("global.$RequestRegistry"),
                SetValue(
                    "global.$RequestRegistry.{$ship}",
                    exact=TableExpr.of(TableEntry("TraceId", PathExpr.of("traceId"))),
                ),
                DebugText(TextExpr.quote("Request registry acquired")),
                Return(True),
            ),
            purpose="run_actions",
        )
