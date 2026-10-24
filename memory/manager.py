from __future__ import annotations

from .storage import MemoryStorage


class MemorySearch:
    def __init__(self, storage: MemoryStorage | None = None) -> None:
        self.storage = storage or MemoryStorage()

    def query(self, user_id: str, query_text: str, limit: int = 20):
        return self.storage.buscar_texto(user_id, query_text, limit)
