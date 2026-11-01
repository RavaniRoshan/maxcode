import pytest
from scheduler import Meeting, free_between, overlaps


def test_identical_intervals_overlap() -> None:
    assert overlaps(9, 10, 9, 10) is True


def test_nested_intervals_overlap() -> None:
    assert overlaps(9, 12, 10, 11) is True


def test_touching_is_not_overlap() -> None:
    assert overlaps(9, 10, 10, 11) is False


def test_reversed_interval_rejected() -> None:
    with pytest.raises(ValueError):
        overlaps(10, 9, 1, 2)


def test_free_between() -> None:
    assert free_between([], 9, 10) is True
    assert free_between([Meeting("A", 9, 10)], 9, 10) is False
