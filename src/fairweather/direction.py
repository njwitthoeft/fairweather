"""Utilities for working with directions, such as converting between compass points and degrees."""


def humanize(degrees: float) -> str:
    """Convert a direction in degrees to a human-readable compass point.

    Accepts degrees in the inclusive range [0, 360]. Values outside this
    range raise `ValueError` to prevent silent wrap-around.
    """
    if not (0 <= degrees <= 360):
        raise ValueError("degrees must be between 0 and 360")

    compass_points = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(degrees / 45) % 8
    return compass_points[index]
