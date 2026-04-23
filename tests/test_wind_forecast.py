from pathlib import Path
import pytest

from fairweather.winds.api import WindForecastResponse
from fairweather.winds.forecast import forecast_response_to_hourly_entries, WindForecast  # type: ignore


def test_forecast_parsing_and_units_from_example():
    p = Path(__file__).with_name("example_response_winds.json")
    data = p.read_text()

    resp = WindForecastResponse.model_validate_json(data)
    entries = forecast_response_to_hourly_entries(resp)

    assert len(entries) == len(resp.hourly.time)

    # example file is already in mph, so first value should match
    assert entries[0].wind_speed_mph == pytest.approx(resp.hourly.wind_speed_10m[0])



def test_windforecast_metrics():
    p = Path(__file__).with_name("example_response_winds.json")
    data = p.read_text()
    resp = WindForecastResponse.model_validate_json(data)
    wf = WindForecast.from_response(resp)

    mean = wf.mean_wind_speed()
    assert mean > 0
    assert wf.max_wind_entry().wind_speed_mph >= wf.min_wind_entry().wind_speed_mph


def test_mean_wind_direction_wraparound():
    from datetime import datetime, timezone
    from fairweather.winds.forecast import HourlyWindForecast, WindForecast

    now = datetime.now(timezone.utc)
    a = HourlyWindForecast(time=now, wind_speed_mph=5.0, wind_direction=359, temperature=50, rain=0)
    b = HourlyWindForecast(time=now, wind_speed_mph=5.0, wind_direction=1, temperature=50, rain=0)
    wf = WindForecast(hourlies=[a, b])

    mean_dir = wf.mean_wind_direction()
    assert mean_dir == pytest.approx(0.0, abs=1e-6)


def test_mean_wind_direction_near_zero_with_offset():
    from datetime import datetime, timezone
    from fairweather.winds.forecast import HourlyWindForecast, WindForecast

    now = datetime.now(timezone.utc)
    a = HourlyWindForecast(time=now, wind_speed_mph=5.0, wind_direction=350, temperature=50, rain=0)
    b = HourlyWindForecast(time=now, wind_speed_mph=5.0, wind_direction=10, temperature=50, rain=0)
    wf = WindForecast(hourlies=[a, b])

    mean_dir = wf.mean_wind_direction()
    # expect approximately 0 (north)
    assert mean_dir == pytest.approx(0.0, abs=1e-6)
