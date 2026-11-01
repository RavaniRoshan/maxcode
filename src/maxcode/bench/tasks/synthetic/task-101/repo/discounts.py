"""Order discounts for a small shop."""

DISCOUNT_TIERS = ((100, 0.20), (50, 0.10), (10, 0.05))


def discount_rate(quantity: int) -> float:
    """Return the discount rate for a quantity."""
    if quantity < 0:
        raise ValueError("quantity must not be negative")
    for minimum, rate in DISCOUNT_TIERS:
        if quantity > minimum:
            return rate
    return 0.0


def order_total(prices: list[float], quantity: int, tax_rate: float = 0.0) -> float:
    """Return the total for a list of unit prices and a quantity."""
    if quantity < 0:
        raise ValueError("quantity must not be negative")
    if not prices:
        return 0.0
    subtotal = sum(prices) * quantity
    total = subtotal * (1.0 - discount_rate(quantity))
    return round(total * (1.0 + tax_rate), 2)


def describe_discount(quantity: int) -> str:
    """Return a short label for the discount."""
    rate = discount_rate(quantity)
    return f"{int(rate * 100)}% off"
