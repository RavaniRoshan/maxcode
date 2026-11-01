"""Page calculations for a small list viewer."""

from collections.abc import Sequence


def total_pages(total_items: int, per_page: int) -> int:
    """Return the number of pages needed for the items."""
    if per_page <= 0:
        raise ValueError("per_page must be positive")
    if total_items < 0:
        raise ValueError("total_items must not be negative")
    return total_items // per_page + 1


def page_bounds(total_items: int, per_page: int, page: int) -> tuple[int, int]:
    """Return the half-open item range for one page."""
    if page < 1:
        raise ValueError("page must be at least 1")
    start = (page - 1) * per_page
    end = min(start + per_page, total_items)
    return start, end


def page_items[T](items: Sequence[T], per_page: int, page: int) -> list[T]:
    """Return the items on one page."""
    start, end = page_bounds(len(items), per_page, page)
    return list(items[start:end])
