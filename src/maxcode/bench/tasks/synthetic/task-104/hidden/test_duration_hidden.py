import pytest
from duration import format_duration, parse_duration


def test_none_is_zero() -> None:
    assert parse_duration(None) == 0


def test_units() -> None:
    assert parse_duration("45s") == 45
    assert parse_duration("2m") == 120
    assert parse_duration("1h30m") == 5400


def test_whitespace_is_zero() -> None:
    assert parse_duration("   ") == 0


def test_invalid_text() -> None:
    with pytest.raises(ValueError):
        parse_duration("soon")


def test_format_duration() -> None:
    assert format_duration(5400) == "1h30m"
    assert format_duration(0) == "0s"
