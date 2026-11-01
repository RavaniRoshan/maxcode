from geometry import bounding_box, scale_shape, translate_shape


def test_multiple_points() -> None:
    assert scale_shape([(1.0, 2.0), (3.0, 4.0)], 2.0, 3.0) == [
        (2.0, 6.0),
        (6.0, 12.0),
    ]


def test_negative_scale() -> None:
    assert scale_shape([(2.0, 3.0)], -1.0, 2.0) == [(-2.0, 6.0)]


def test_translate_shape() -> None:
    assert translate_shape([(1.0, 2.0)], 3.0, -1.0) == [(4.0, 1.0)]


def test_bounding_box() -> None:
    assert bounding_box([(1.0, 2.0), (3.0, 0.0)]) == (1.0, 0.0, 3.0, 2.0)
