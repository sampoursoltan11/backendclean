from typing import Any, Callable, Dict, Iterator, ItemsView, KeysView


class HybridAsyncDict:
    """
    A small helper that behaves like both:
    - an awaitable (await -> Dict[str, Any])
    - a dict-like object for synchronous access (result["key"], result.get(...))

    Useful to expose service methods that can be used in both sync unit tests
    and async application code without duplicating APIs.
    """

    def __init__(self, sync_fn: Callable[[], Dict[str, Any]], async_fn: Callable[[], Any]):
        self._sync_fn = sync_fn
        self._async_fn = async_fn
        self._data: Dict[str, Any] | None = None

    # Awaitable protocol
    def __await__(self):  # type: ignore[override]
        async def _runner():
            result = await self._async_fn()
            if isinstance(result, dict):
                self._data = result
            return result

        return _runner().__await__()

    # Dict-like behavior for synchronous access
    def _ensure_sync(self) -> Dict[str, Any]:
        if self._data is None:
            self._data = self._sync_fn()
        return self._data

    def __getitem__(self, key: str) -> Any:
        return self._ensure_sync()[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._ensure_sync().get(key, default)

    def __contains__(self, key: object) -> bool:
        return key in self._ensure_sync()

    def keys(self) -> KeysView[str]:
        return self._ensure_sync().keys()

    def items(self) -> ItemsView[str, Any]:
        return self._ensure_sync().items()

    def __iter__(self) -> Iterator[str]:
        return iter(self._ensure_sync())

    def __len__(self) -> int:
        return len(self._ensure_sync())

    def __repr__(self) -> str:
        return f"HybridAsyncDict({self._ensure_sync()!r})"
