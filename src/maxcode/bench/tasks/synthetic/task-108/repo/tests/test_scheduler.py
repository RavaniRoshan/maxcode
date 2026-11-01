from scheduler import Meeting, conflicting_meetings, overlaps


def test_touching_intervals_do_not_overlap() -> None:
    assert overlaps(9, 10, 10, 11) is False


def test_touching_meetings_do_not_conflict() -> None:
    meetings = [Meeting("A", 9, 10), Meeting("B", 10, 11)]
    assert conflicting_meetings(meetings) == []
