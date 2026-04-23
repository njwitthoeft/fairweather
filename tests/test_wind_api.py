from pathlib import Path

from fairweather.winds.api import WindForecastResponse


def test_example_wind_response_parsing():
    p = Path(__file__).with_name("example_response_winds.json")
    data = p.read_text()

    resp = WindForecastResponse.model_validate_json(data)

    # basic shape checks
    assert len(resp.hourly.time) == len(resp.hourly.wind_speed_10m)
    assert len(resp.hourly.time) == len(resp.hourly.wind_direction_10m)

    # spot-check first values from the example file
    assert resp.hourly.wind_speed_10m[0] == 14.5
    assert resp.hourly.wind_direction_10m[0] == 218
