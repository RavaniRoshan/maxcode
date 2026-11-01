from textstats import average_word_length


def test_empty_text_has_zero_average() -> None:
    assert average_word_length("") == 0.0


def test_whitespace_text_has_zero_average() -> None:
    assert average_word_length("   ") == 0.0


def test_average_of_words() -> None:
    assert average_word_length("one three") == 4.0
