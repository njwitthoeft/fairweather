from pathlib import Path

import pytest

from fairweather.waves.api import WaveForecastResponse
from fairweather.waves.forecast import (
    forecast_response_to_hourly_entries,
    M_TO_FT,
    WaveForecast,
)


@pytest.fixture
def wf_response():
    p = Path(__file__).with_name("example_response.json")
    data = p.read_text()
    return WaveForecastResponse.model_validate_json(data)


@pytest.fixture
def wf(wf_response):
    return WaveForecast.from_response(wf_response)


def test_hourly_entries_count(wf_response):
    entries = forecast_response_to_hourly_entries(wf_response)
    # len of array of structs should match length of each array in struct of arrays
    assert len(entries) == len(wf_response.hourly.time)


def test_unit_conversion_first_entry(wf_response):
    entries = forecast_response_to_hourly_entries(wf_response)
    first_m = wf_response.hourly.wave_height[0]
    first_entry = entries[0]
    assert first_entry.wave_height == pytest.approx(first_m * M_TO_FT, rel=1e-6)


def test_waveforecast_metrics_and_within_range(wf, wf_response):
    # mean, min, max should be consistent with entries
    mean = wf.mean_wave_height()
    mean_response = (
        sum(wf_response.hourly.wave_height)
        * M_TO_FT
        / len(wf_response.hourly.wave_height)
    )
    assert mean == pytest.approx(mean_response, rel=1e-6)

    max_entry = wf.max_wave_height_entry()
    min_entry = wf.min_wave_height_entry()

    max_response = max(wf_response.hourly.wave_height) * M_TO_FT
    min_response = min(wf_response.hourly.wave_height) * M_TO_FT
    assert max_entry.wave_height == pytest.approx(max_response, rel=1e-6)
    assert min_entry.wave_height == pytest.approx(min_response, rel=1e-6)

    # pick a small time window inside the hourlies and verify the filtered forecast
    start = wf.hourlies[1].time
    end = wf.hourlies[4].time
    during = wf.within_time_range(start, end)
    assert isinstance(during, WaveForecast)
    assert all(start <= e.time <= end for e in during.hourlies)
