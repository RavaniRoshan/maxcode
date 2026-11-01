"""Small text statistics helpers."""

import string


def average_word_length(text: str) -> float:
    """Return the average length of the words in the text."""
    words = text.split()
    return sum(len(word) for word in words) / len(words)


def longest_word(text: str) -> str:
    """Return the longest word, or an empty string for empty text."""
    words = text.split()
    if not words:
        return ""
    return max(words, key=len)


def word_count(text: str) -> int:
    """Return the number of words in the text."""
    return len(text.split())


def strip_punctuation(text: str) -> str:
    """Remove common punctuation from both ends of each word."""
    return " ".join(word.strip(string.punctuation) for word in text.split())


def average_sentence_length(text: str) -> float:
    """Return the average number of words per sentence."""
    sentences = [part for part in text.split(".") if part.strip()]
    if not sentences:
        return 0.0
    return sum(word_count(part) for part in sentences) / len(sentences)
