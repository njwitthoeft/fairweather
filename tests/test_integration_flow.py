import json
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time

from fairweather.tides.api import TideRequest
from fairweather.tides import api as tides_api
from fairweather.tides import cycle as tides_cycle
from fairweather.waves.api import WaveRequest
from fairweather.waves.api import fetch_wave_forecast
from fairweather.waves.forecast import WaveForecast
import fairweather.winds.api as wind_api
from fairweather.winds.forecast import WindForecast
from fairweather.winds.api import WindRequest, fetch_wind_forecast


class DummyResponse:
    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")
        return None


class FakeClient:
    def __init__(self, _http2=True, *, _resp_text=None):
        self._resp_text = _resp_text

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, *args, **kwargs):
        return DummyResponse(self._resp_text)


def make_tide_text(pred_times):
    preds = []
    for t, v, typ in pred_times:
        preds.append({"t": t, "v": str(v), "type": typ})
    return json.dumps({"predictions": preds})


def test_end_to_end_with_mocks(monkeypatch):
    # Freeze time used by tide selection and run the full mocked flow
    with freeze_time("2026-04-22T12:00:00Z"):
        # NOAA tide predictions: construct times so the 'optimal' turn is at 08:30 local next day
        local_now = datetime.now().astimezone()
        target_date = (local_now + timedelta(days=1)).date()
        local_tz = local_now.tzinfo

        def local_to_utc_str(d, h, m=0):
            dt_local = datetime(d.year, d.month, d.day, h, m, tzinfo=local_tz)
            dt_utc = dt_local.astimezone(timezone.utc)
            return dt_utc.strftime("%Y-%m-%d %H:%M")

        pred_times = [
            # a past tide before fixed_now
            (
                (datetime.now() - timedelta(hours=1))
                .astimezone(timezone.utc)
                .strftime("%Y-%m-%d %H:%M"),
                1.0,
                "H",
            ),
            # optimal turn at 08:30 local next day
            (local_to_utc_str(target_date, 8, 30), 0.5, "L"),
            # following tide later that day
            (local_to_utc_str(target_date, 16, 0), 2.5, "H"),
        ]
        tide_text = make_tide_text(pred_times)
        monkeypatch.setattr(
            tides_api,
            "httpx",
            type("X", (), {"Client": lambda *a, **k: FakeClient(_resp_text=tide_text)}),
        )

        tides_resp = tides_api.fetch_tides(TideRequest())
        cycle = tides_cycle.find_optimal_tide_cycle(tides_resp.predictions)
        assert cycle is not None

        # Use the bundled example Open-Meteo response
        with open("tests/example_response_waves.json") as f:
            wave_text = f.read()

        import fairweather.waves.api as waves_api

        monkeypatch.setattr(
            waves_api,
            "httpx",
            type("X", (), {"Client": lambda *a, **k: FakeClient(_resp_text=wave_text)}),
        )

        wr = WaveRequest(
            latitude=59.708336,
            longitude=-151.875,
            start_date="2026-04-22",
            end_date="2026-04-23",
        )
        wf_resp = fetch_wave_forecast(wr)
        wf = WaveForecast.from_response(wf_resp)
        wave_during = wf.within_time_range(cycle.start.timestamp, cycle.end.timestamp)

        # `during` is a WaveForecast instance (may be empty depending on dates)
        assert isinstance(wave_during, WaveForecast)
        assert all(
            cycle.start.timestamp <= h.time <= cycle.end.timestamp
            for h in wave_during.hourlies
        )

        # Also fetch wind data for the cycle and ensure we have wind samples
        with open("tests/example_response_winds.json") as f:
            wind_text = f.read()

        monkeypatch.setattr(
            wind_api,
            "httpx",
            type("X", (), {"Client": lambda *a, **k: FakeClient(_resp_text=wind_text)}),
        )

        wr = WindRequest(
            latitude=59.708336,
            longitude=-151.875,
            start_date="2026-04-22",
            end_date="2026-04-23",
        )
        wind_resp = fetch_wind_forecast(wr)
        wind_forecast = WindForecast.from_response(wind_resp)
        wind_during = wind_forecast.within_time_range(
            cycle.start.timestamp, cycle.end.timestamp
        )

        assert isinstance(wind_during, WindForecast)
        assert all(
            cycle.start.timestamp <= h.time <= cycle.end.timestamp
            for h in wind_during.hourlies
        )

        assert len(wind_during.hourlies) == len(
            wave_during.hourlies
        )  # in our test data, wind and wave forecasts have same timestamps
