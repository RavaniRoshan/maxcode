"""Meeting overlap checks for a small calendar."""

from dataclasses import dataclass


@dataclass
class Meeting:
    """One meeting with a start and end hour."""

    name: str
    start: int
    end: int


def overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    """Return True when two half-open intervals overlap."""
    if a_start > a_end or b_start > b_end:
        raise ValueError("start must not be after end")
    return a_start <= b_end and b_start <= a_end


def conflicting_meetings(meetings: list[Meeting]) -> list[tuple[str, str]]:
    """Return pairs of meeting names that overlap."""
    conflicts: list[tuple[str, str]] = []
    for index, first in enumerate(meetings):
        for second in meetings[index + 1 :]:
            if overlaps(first.start, first.end, second.start, second.end):
                conflicts.append((first.name, second.name))
    return conflicts


def free_between(meetings: list[Meeting], start: int, end: int) -> bool:
    """Return True when the interval is free of meetings."""
    return not any(overlaps(start, end, meeting.start, meeting.end) for meeting in meetings)
