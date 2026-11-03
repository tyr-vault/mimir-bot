from __future__ import annotations

from dataclasses import dataclass

from finance.normalize import normalize_for_match


@dataclass(frozen=True)
class CategoryRef:
    id: str
    name: str


@dataclass(frozen=True)
class CategoryResolveResult:
    category_id: str | None
    category_name: str | None
    unknown: bool = False
    ambiguous: bool = False
    matches: tuple[CategoryRef, ...] = ()


def resolve_category(
    hint: str | None,
    categories: list[CategoryRef],
) -> CategoryResolveResult:
    if not hint or not hint.strip():
        return CategoryResolveResult(category_id=None, category_name=None)

    needle = normalize_for_match(hint)
    exact = [c for c in categories if normalize_for_match(c.name) == needle]
    if len(exact) == 1:
        return CategoryResolveResult(
            category_id=exact[0].id,
            category_name=exact[0].name,
            matches=(exact[0],),
        )
    if len(exact) > 1:
        return CategoryResolveResult(
            category_id=None,
            category_name=None,
            ambiguous=True,
            matches=tuple(exact),
        )
    return CategoryResolveResult(
        category_id=None,
        category_name=None,
        unknown=True,
        matches=(),
    )
