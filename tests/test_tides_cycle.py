import pytest
from datetime import datetime, timezone, timedelta
from freezegun import freeze_time

from fairweather.tides.api import TurnPrediction
from fairweather.tides import cycle as tides_cycle


def make_turn(ts: datetime, h: float, typ: str) -> TurnPrediction:
    # TurnPrediction validators expect the NOAA-style aliased input (strings like 'YYYY-MM-DD HH:MM')
    payload = {
        "t": ts.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "v": str(h),
        "type": typ,
    }
    return TurnPrediction.model_validate(payload)


def test_find_last_and_next_two_from_models():
    # freeze time so relative comparisons are deterministic
    with freeze_time("2026-04-22T12:00:00Z"):
        now = datetime.now(timezone.utc)
        preds = [
            make_turn(now - timedelta(hours=2), -1.0, "L"),
            make_turn(now - timedelta(hours=1), -1.0, "L"),
            make_turn(now + timedelta(hours=1), 2.5, "H"),
            make_turn(now + timedelta(hours=4), 0.5, "L"),
            make_turn(now + timedelta(hours=8), 2.5, "H"),
        ]

        last = tides_cycle.find_last_tide_turn(preds)
        assert last is not None
        assert last.timestamp.hour == (now - timedelta(hours=1)).hour

        next_two = tides_cycle.find_next_tide_turns(preds, count=2)
        assert len(next_two) == 2
        assert next_two[0].timestamp.hour == (now + timedelta(hours=1)).hour
        assert next_two[1].timestamp.hour == (now + timedelta(hours=4)).hour


def test_optimal_turn_selection():
    with freeze_time("2026-04-22T12:00:00Z"):
        local_now = datetime.now().astimezone()
        target_date = (local_now + timedelta(days=1)).date()
        local_tz = local_now.tzinfo

        def local_to_utc(d, h, m=0):
            dt_local = datetime(d.year, d.month, d.day, h, m, tzinfo=local_tz)
            return dt_local.astimezone(timezone.utc)

        # create predictions so the optimal turn is 08:30 local next day
        preds = [
            make_turn(datetime.now(timezone.utc) - timedelta(hours=1), 1.0, "H"),
            make_turn(local_to_utc(target_date, 8, 30), 0.5, "L"),
            make_turn(local_to_utc(target_date, 16, 0), 2.5, "H"),
        ]

        optimal = tides_cycle.find_optimal_tide_turn(preds, start_hour=6, end_hour=15, day_offset=1)
        assert optimal is not None
        assert optimal.tide_type == "L"


def test_cycle_properties():
    with freeze_time("2026-04-22T12:00:00Z"):
        # minimal preds for cycle property tests
        now = datetime.now(timezone.utc)
        preds = [
            make_turn(now - timedelta(hours=1), 1.0, "H"),
            make_turn(now + timedelta(hours=2), 0.5, "L"),
        ]

        cycle = tides_cycle.TideCycle(start=preds[0], end=preds[1])
        assert cycle is not None
        assert cycle.spread() == pytest.approx(abs(1.0 - 0.5))
        # start is H to L, so ebb
        assert cycle.is_ebb()


def test_tidecycle_validation_errors():
    a = make_turn(datetime(2026, 4, 22, 8, tzinfo=timezone.utc), 1.0, "H")
    b = make_turn(datetime(2026, 4, 22, 9, tzinfo=timezone.utc), 2.0, "H")
    with pytest.raises(ValueError):
        tides_cycle.TideCycle(start=a, end=b)

    # start after end
    c = make_turn(datetime(2026, 4, 22, 10, tzinfo=timezone.utc), 0.5, "L")
    with pytest.raises(ValueError):
        tides_cycle.TideCycle(start=c, end=a)
