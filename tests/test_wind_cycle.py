from datetime import datetime, timezone

from freezegun import freeze_time

from fairweather.winds.api import WindRequest, fetch_wind_forecast
from fairweather.winds.forecast import WindForecast


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


def test_fetch_wind_for_cycle(monkeypatch):
    with open("tests/example_response_winds.json") as f:
        wind_text = f.read()

    # freeze time to make the cycle deterministic
    with freeze_time("2026-04-22T12:00:00Z"):
        # choose a cycle that lies on 2026-04-22
        start = datetime(2026, 4, 22, 8, 0, tzinfo=timezone.utc)
        end = datetime(2026, 4, 22, 16, 0, tzinfo=timezone.utc)

        monkeypatch.setattr(
            "fairweather.winds.api.httpx",
            type("X", (), {"Client": lambda *a, **k: FakeClient(_resp_text=wind_text)}),
        )

        req = WindRequest(
            latitude=59.75,
            longitude=-151.75,
            start_date=start.date().isoformat(),
            end_date=end.date().isoformat(),
        )
        resp = fetch_wind_forecast(req)
        wf = WindForecast.from_response(resp).within_time_range(start, end)
        assert wf is not None
        assert len(wf.hourlies) > 0
        # all returned hourlies should lie within the requested cycle window
        assert all(start <= h.time <= end for h in wf.hourlies)
        # mean_wind_direction should be an int in [0,360)
        md = wf.mean_wind_direction()
        assert isinstance(md, int)
        assert 0 <= md < 360
