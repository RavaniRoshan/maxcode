"""Stock checks for a small warehouse."""

from dataclasses import dataclass


@dataclass
class Item:
    """One stocked item."""

    sku: str
    stock: int
    threshold: int


def reorder_needed(stock: int, threshold: int) -> bool:
    """Return True when stock has fallen to the reorder level."""
    return stock <= threshold


def reorder_list(items: list[Item]) -> list[str]:
    """Return the SKUs that need a reorder."""
    return [item.sku for item in items if reorder_needed(item.stock, item.threshold)]


def total_stock(items: list[Item]) -> int:
    """Return the total units across all items."""
    return sum(item.stock for item in items)


def out_of_stock(items: list[Item]) -> list[str]:
    """Return the SKUs with no stock left."""
    return [item.sku for item in items if item.stock == 0]
