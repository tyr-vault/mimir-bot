from finance.category_resolver import CategoryRef, resolve_category
from finance.date_resolver import resolve_date_hint


def test_exact_category() -> None:
    cats = [CategoryRef(id="1", name="Alimentação"), CategoryRef(id="2", name="Food")]
    r = resolve_category("alimentacao", cats)  # accent-folded
    assert r.category_id == "1"


def test_unknown_category() -> None:
    r = resolve_category("Pets", [CategoryRef(id="1", name="Food")])
    assert r.unknown


def test_hoje() -> None:
    iso, hint, amb = resolve_date_hint("gastei 10 hoje")
    assert iso is not None
    assert hint == "hoje"
    assert not amb


def test_explicit_date() -> None:
    iso, hint, amb = resolve_date_hint("paguei 10 em 02/11/2026")
    assert iso == "2026-11-02"
    assert not amb
