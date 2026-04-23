import pytest

from fairweather.direction import humanize


@pytest.mark.parametrize(
    "deg,expected",
    [
        (359, "N"),
        (1, "N"),
        (45, "NE"),
        (90, "E"),
        (225, "SW"),
    ],
)
def test_humanize_expected(deg, expected):
    assert humanize(deg) == expected


def test_humanize_out_of_range_raises():
    with pytest.raises(ValueError):
        humanize(-1)

    with pytest.raises(ValueError):
        humanize(361)


@pytest.mark.parametrize(
    "deg,expected",
    [
        (22.5, "N"),
        (67.5, "E"),
        (112.5, "E"),
        (157.5, "S"),
        (202.5, "S"),
        (247.5, "W"),
        (292.5, "W"),
        (337.5, "N"),
    ],
)
def test_humanize_quadrant_boundaries(deg, expected):
    # Verify exact quadrant-edge behavior (ties handled by Python's round-to-even)
    assert humanize(deg) == expected
