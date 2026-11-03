"""Lightweight invariant checks for confirm/cancel/idempotency store."""

from __future__ import annotations

from decimal import Decimal

from finance.engine import build_preview
from finance.models import TransactionCandidate
from services.pending_store import PendingPreviewStore


def test_preview_hash_changes_when_amount_edits() -> None:
    base = TransactionCandidate(
        raw_text="x",
        intent_create=True,
        type="expense",
        amounts=[Decimal("10")],
        category_id="c1",
        category_name="Food",
        date_iso="2026-11-03",
    )
    p1 = build_preview(base, ttl_seconds=60)
    base.amounts = [Decimal("20")]
    p2 = build_preview(base, ttl_seconds=60)
    assert p1.preview_hash != p2.preview_hash


def test_other_user_cannot_load_preview() -> None:
    store = PendingPreviewStore()
    cand = TransactionCandidate(
        raw_text="x",
        intent_create=True,
        type="expense",
        amounts=[Decimal("10")],
        category_id="c1",
        category_name="Food",
        date_iso="2026-11-03",
    )
    preview = build_preview(cand, ttl_seconds=60)
    store.put(42, preview)
    assert store.get(preview.preview_id, 99) is None
    assert store.get(preview.preview_id, 42) is not None


def test_expired_preview_not_confirmable() -> None:
    store = PendingPreviewStore()
    cand = TransactionCandidate(
        raw_text="x",
        intent_create=True,
        type="income",
        amounts=[Decimal("5")],
        category_id="c1",
        category_name="Income",
        date_iso="2026-11-03",
    )
    preview = build_preview(cand, ttl_seconds=-1)
    store.put(1, preview)
    assert store.get(preview.preview_id, 1) is None
