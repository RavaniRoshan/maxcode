import pytest
from pagination import page_bounds, page_items, total_pages


def test_partial_page_rounds_up() -> None:
    assert total_pages(11, 10) == 2


def test_single_item() -> None:
    assert total_pages(1, 10) == 1


def test_exact_multiple() -> None:
    assert total_pages(100, 10) == 10


def test_bounds_are_clamped() -> None:
    assert page_bounds(11, 10, 2) == (10, 11)


def test_page_items() -> None:
    assert page_items(list(range(11)), 10, 2) == [10]


def test_invalid_per_page() -> None:
    with pytest.raises(ValueError):
        total_pages(10, 0)
