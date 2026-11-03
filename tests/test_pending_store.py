import time
from decimal import Decimal

from finance.models import TransactionPreview
from services.pending_store import PendingPreviewStore


def _preview(pid: str = "p1", expires_in: float = 60) -> TransactionPreview:
    return TransactionPreview(
        preview_id=pid,
        idempotency_key=pid,
        preview_hash="h",
        type="expense",
        amount=Decimal("10"),
        category_id="c",
        category_name="Food",
        date_iso="2026-11-03",
        description=None,
        expires_at=time.time() + expires_in,
    )


def test_get_requires_matching_user() -> None:
    store = PendingPreviewStore()
    store.put(1, _preview())
    assert store.get("p1", 1) is not None
    assert store.get("p1", 2) is None


def test_expired_returns_none() -> None:
    store = PendingPreviewStore()
    store.put(1, _preview(expires_in=-1))
    assert store.get("p1", 1) is None
