from pagination import total_pages


def test_exact_multiple_has_no_extra_page() -> None:
    assert total_pages(20, 10) == 2


def test_empty_list_has_no_pages() -> None:
    assert total_pages(0, 10) == 0
