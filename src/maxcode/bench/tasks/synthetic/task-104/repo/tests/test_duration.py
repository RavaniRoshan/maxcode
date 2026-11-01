from duration import parse_duration


def test_none_is_zero() -> None:
    assert parse_duration(None) == 0


def test_empty_is_zero() -> None:
    assert parse_duration("") == 0
