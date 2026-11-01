from geometry import scale_shape


def test_non_square_scale_keeps_axes() -> None:
    assert scale_shape([(2.0, 3.0)], 10.0, 100.0) == [(20.0, 300.0)]


def test_origin_stays_at_origin() -> None:
    assert scale_shape([(0.0, 0.0)], 10.0, 100.0) == [(0.0, 0.0)]
