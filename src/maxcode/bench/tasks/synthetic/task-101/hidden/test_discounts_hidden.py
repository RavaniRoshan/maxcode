import pytest
from discounts import describe_discount, discount_rate, order_total


def test_tier_boundaries() -> None:
    assert discount_rate(9) == 0.0
    assert discount_rate(10) == 0.05
    assert discount_rate(50) == 0.10
    assert discount_rate(100) == 0.20


def test_tax_is_applied_after_discount() -> None:
    assert order_total([10.0], 10, tax_rate=0.1) == 104.5


def test_empty_prices() -> None:
    assert order_total([], 10) == 0.0


def test_negative_quantity() -> None:
    with pytest.raises(ValueError):
        discount_rate(-1)


def test_description_uses_the_tier() -> None:
    assert describe_discount(10) == "5% off"
