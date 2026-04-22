import json
from datetime import datetime, timezone

from fairweather import tides


class DummyResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
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


def make_response_text(pred_times):
    # pred_times: list of tuples (t_str, v, type)
    preds = []
    for t, v, typ in pred_times:
        preds.append({"t": t, "v": str(v), "type": typ})
    return json.dumps({"predictions": preds})


def test_find_last_and_next_two(monkeypatch):
    # fixed now = 2026-04-22 12:00 UTC
    fixed_now = datetime(2026, 4, 22, 12, 0, tzinfo=timezone.utc)

    # Patch tides.datetime so its now() returns fixed_now but parsing still works
    RealDT = tides.datetime

    class FixedDT:
        @classmethod
        def now(cls, tz=None):
            return fixed_now

        @staticmethod
        def fromisoformat(s):
            return RealDT.fromisoformat(s)

        @staticmethod
        def strptime(s, fmt):
            return RealDT.strptime(s, fmt)

    monkeypatch.setattr(tides, "datetime", FixedDT)

    # Prepare predictions: one past (11:00), two future (13:00, 16:00)
    pred_times = [
        ("2026-04-22 11:00", -1.0, "L"),
        ("2026-04-22 13:00", 2.5, "H"),
        ("2026-04-22 16:00", 0.5, "L"),
    ]
    resp_text = make_response_text(pred_times)

    # Monkeypatch httpx.Client to return our fake response
    def fake_client_constructor(*args, **kwargs):
        return FakeClient(_resp_text=resp_text)

    monkeypatch.setattr(tides.httpx, "Client", fake_client_constructor)

    req = tides.TideRequest()
    resp = tides.fetch_tides(req)

    # validate parsing produced timezone-aware datetimes
    assert all(p.timestamp.tzinfo is not None for p in resp.predictions)

    last = tides.find_last_tide(resp.predictions)
    assert last is not None
    assert last.timestamp.hour == 11

    next_two = tides.find_next_tides(resp.predictions, count=2)
    assert len(next_two) == 2
    assert next_two[0].timestamp.hour == 13
    assert next_two[1].timestamp.hour == 16
