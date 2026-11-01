from inventory import Item, reorder_list, reorder_needed


def test_threshold_is_not_a_reorder() -> None:
    assert reorder_needed(5, 5) is False


def test_below_threshold_is_a_reorder() -> None:
    assert reorder_needed(4, 5) is True


def test_reorder_list_skips_threshold_items() -> None:
    items = [Item("A", 5, 5), Item("B", 4, 5)]
    assert reorder_list(items) == ["B"]
