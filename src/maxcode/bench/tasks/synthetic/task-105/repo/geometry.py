"""Point scaling helpers for a small drawing tool."""

Point = tuple[float, float]


def scale_point(x: float, y: float, scale_x: float, scale_y: float) -> Point:
    """Scale one point around the origin."""
    return x * scale_x, y * scale_y


def scale_shape(points: list[Point], scale_x: float, scale_y: float) -> list[Point]:
    """Scale every point in a shape."""
    return [scale_point(y, x, scale_x, scale_y) for x, y in points]


def bounding_box(points: list[Point]) -> tuple[float, float, float, float]:
    """Return the min x, min y, max x, max y of the points."""
    if not points:
        raise ValueError("points must not be empty")
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    return min(xs), min(ys), max(xs), max(ys)


def translate_shape(points: list[Point], dx: float, dy: float) -> list[Point]:
    """Move every point by the given offset."""
    return [(x + dx, y + dy) for x, y in points]
