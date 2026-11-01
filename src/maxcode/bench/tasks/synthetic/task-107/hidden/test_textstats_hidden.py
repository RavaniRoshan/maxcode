from textstats import average_sentence_length, average_word_length, longest_word


def test_empty_text_has_zero_average() -> None:
    assert average_word_length("") == 0.0


def test_single_word() -> None:
    assert average_word_length("hello") == 5.0


def test_punctuation_does_not_change_longest() -> None:
    assert longest_word("hello, world!") == "hello,"


def test_average_sentence_length() -> None:
    assert average_sentence_length("One two. Three four five.") == 2.5


def test_empty_sentence_average() -> None:
    assert average_sentence_length("") == 0.0
