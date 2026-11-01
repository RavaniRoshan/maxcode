from discounts import order_total


def test_large_order_gets_five_percent_off() -> None:
    assert order_total([10.0, 10.0], 10) == 190.0


def test_small_order_has_no_discount() -> None:
    assert order_total([10.0], 5) == 50.0
