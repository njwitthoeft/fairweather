import json
from datetime import timezone

from freezegun import freeze_time

from fairweather.tides.api import TideRequest, TurnPrediction
from fairweather.tides import api as tides_api


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
    preds = []
    for t, v, typ in pred_times:
        preds.append({"t": t, "v": str(v), "type": typ})
    return json.dumps({"predictions": preds})


def test_fetch_tides_parses_predictions(monkeypatch):
    with freeze_time("2026-04-22T12:00:00Z"):
        pred_times = [
            ("2026-04-22 11:00", -1.0, "L"),
            ("2026-04-22 13:00", 2.5, "H"),
        ]
        resp_text = make_response_text(pred_times)

        monkeypatch.setattr(
            tides_api,
            "httpx",
            type("X", (), {"Client": lambda *a, **k: FakeClient(_resp_text=resp_text)}),
        )

        req = TideRequest()
        resp = tides_api.fetch_tides(req)

        assert len(resp.predictions) == 2
        first = resp.predictions[0]
        assert isinstance(first.timestamp.tzinfo, type(timezone.utc))
        assert first.height == -1.0
        assert first.tide_type == "L"


def test_turnprediction_timestamp_is_utc():
    payload = {"t": "2026-04-22 11:00", "v": "1.0", "type": "H"}
    t = TurnPrediction.model_validate(payload)
    assert t.timestamp.tzinfo is not None
    assert t.timestamp.utcoffset().total_seconds() == 0
