from collections.abc import Callable
from typing import Any, Generic, TypeVar

T = TypeVar("T")
END: str


class CompiledGraph:
    def invoke(self, input: Any, config: Any | None = None, **kwargs: Any) -> dict[str, Any]: ...


class StateGraph(Generic[T]):
    def __init__(self, state_schema: type[T]) -> None: ...
    def add_node(self, node: str, action: Callable[[Any], Any], *args: Any, **kwargs: Any) -> None: ...
    def set_entry_point(self, key: str) -> None: ...
    def add_edge(self, start_key: str, end_key: str) -> None: ...
    def add_conditional_edges(
        self,
        source: str,
        path: Callable[[Any], str],
        path_map: dict[str, str],
        *args: Any,
        **kwargs: Any,
    ) -> None: ...
    def compile(self, *args: Any, **kwargs: Any) -> CompiledGraph: ...
