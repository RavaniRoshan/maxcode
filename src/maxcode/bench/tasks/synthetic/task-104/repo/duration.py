"""Parse short duration strings such as 1h30m or 45s."""

import re

PATTERN = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$")


def parse_duration(text: str | None) -> int:
    """Return the duration in seconds. None or empty text is zero."""
    text = text.strip().lower()
    if not text:
        return 0
    match = PATTERN.fullmatch(text)
    if match is None:
        raise ValueError(f"invalid duration: {text!r}")
    hours, minutes, seconds = (int(value or 0) for value in match.groups())
    if hours < 0 or minutes < 0 or seconds < 0:
        raise ValueError("duration must not be negative")
    return hours * 3600 + minutes * 60 + seconds


def format_duration(total_seconds: int) -> str:
    """Return a compact h/m/s representation."""
    if total_seconds < 0:
        raise ValueError("duration must not be negative")
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    return "".join(parts)
