from __future__ import annotations

import time
from dataclasses import dataclass

from finance.models import TransactionPreview


@dataclass
class PendingEntry:
    preview: TransactionPreview
    user_id: int


class PendingPreviewStore:
    """In-process pending previews (single bot instance)."""

    def __init__(self) -> None:
        self._items: dict[str, PendingEntry] = {}

    def put(self, user_id: int, preview: TransactionPreview) -> None:
        self._purge()
        self._items[preview.preview_id] = PendingEntry(preview=preview, user_id=user_id)

    def get(self, preview_id: str, user_id: int) -> TransactionPreview | None:
        self._purge()
        entry = self._items.get(preview_id)
        if entry is None or entry.user_id != user_id:
            return None
        if entry.preview.expires_at < time.time():
            del self._items[preview_id]
            return None
        return entry.preview

    def invalidate(self, preview_id: str) -> None:
        self._items.pop(preview_id, None)

    def invalidate_user(self, user_id: int) -> None:
        for key in [k for k, v in self._items.items() if v.user_id == user_id]:
            del self._items[key]

    def _purge(self) -> None:
        now = time.time()
        expired = [k for k, v in self._items.items() if v.preview.expires_at < now]
        for key in expired:
            del self._items[key]


pending_store = PendingPreviewStore()
