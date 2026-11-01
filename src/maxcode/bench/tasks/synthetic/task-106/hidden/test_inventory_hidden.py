from inventory import Item, out_of_stock, reorder_list, total_stock


def test_threshold_is_not_a_reorder() -> None:
    assert reorder_list([Item("A", 5, 5)]) == []


def test_zero_stock_is_a_reorder() -> None:
    assert reorder_list([Item("A", 0, 5)]) == ["A"]


def test_above_threshold_is_not_a_reorder() -> None:
    assert reorder_list([Item("A", 6, 5)]) == []


def test_out_of_stock() -> None:
    assert out_of_stock([Item("A", 0, 5), Item("B", 1, 5)]) == ["A"]


def test_total_stock() -> None:
    assert total_stock([Item("A", 2, 5), Item("B", 3, 5)]) == 5
