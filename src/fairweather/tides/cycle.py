from datetime import datetime, timedelta, timezone
from datetime import date as _date

from fairweather.tides.api import TurnPrediction


class TideCycle:
    start: TurnPrediction
    end: TurnPrediction

    def __init__(self, start: TurnPrediction, end: TurnPrediction):
        if start.tide_type == end.tide_type:
            raise ValueError(
                "Start and end predictions must be different types (H vs L)"
            )
        if start.timestamp >= end.timestamp:
            raise ValueError("Start prediction must be before end prediction")

        self.start = start
        self.end = end

    def __str__(self):
        cycle_type = "Ebb" if self.is_ebb() else "Flood"
        return f"{cycle_type} cycle from {self.start.local_time().strftime('%Y-%m-%d %H:%M')} to {self.end.local_time().strftime('%Y-%m-%d %H:%M')} with spread {self.spread():.2f} ft from {self.start.height} ft to {self.end.height} ft"

    def spread(self) -> float:
        """Return the height difference between the start and end of the cycle."""
        return abs(self.end.height - self.start.height)

    def is_ebb(self) -> bool:
        """Return True if this is an ebb cycle (high to low), False if flood (low to high)."""
        return self.end.height < self.start.height

    def is_flood(self) -> bool:
        """Return True if this is a flood cycle (low to high), False if ebb (high to low)."""
        return not self.is_ebb()


def find_last_tide_turn(tide_predictions: list[TurnPrediction]) -> TurnPrediction:
    """Find the most recent tide from the list of predictions."""
    now = datetime.now(timezone.utc)
    past_tides = [t for t in tide_predictions if t.timestamp <= now]
    return past_tides[-1] if past_tides else None


def find_next_tide_turns(
    tide_predictions: list[TurnPrediction], count: int = 2
) -> list[TurnPrediction]:
    """Find the next `count` tides from the list of predictions."""
    now = datetime.now(timezone.utc)
    upcoming_tides = [t for t in tide_predictions if t.timestamp > now]
    return upcoming_tides[:count]


def find_optimal_tide_turn(
    tide_predictions: list[TurnPrediction],
    start_hour: int = 6,
    end_hour: int = 15,
    day_offset: int = 1,
    target_date: _date | None = None,
) -> TurnPrediction:
    """Return the first tide prediction for the target day (today + `day_offset`) whose
    local time falls between `start_hour` and `end_hour` (inclusive).

    Uses the prediction's local time (via `TidePrediction.local_time()`) so comparisons
    respect the machine's local timezone. Returns `None` when no suitable tide is found.
    """
    # If an explicit target_date is provided, use it. Otherwise compute
    # the target date as today + day_offset (preserving existing behavior).
    if target_date is None:
        local_now = datetime.now().astimezone()
        target_date = (local_now + timedelta(days=day_offset)).date()

    # Predictions are returned in chronological order.
    for p in tide_predictions:
        lt = p.local_time()
        if lt.date() == target_date and start_hour <= lt.hour <= end_hour:
            return p
    return None


def find_optimal_tide_cycle(
    tide_predictions: list[TurnPrediction], target_date: _date | None = None
) -> TideCycle:
    """Find the tide cycle that starts with the optimal tide turn."""
    optimal_turn = find_optimal_tide_turn(tide_predictions, target_date=target_date)
    if not optimal_turn:
        return None

    # Find the next tide turn after the optimal turn
    for t in tide_predictions:
        if t.timestamp > optimal_turn.timestamp:
            return TideCycle(start=optimal_turn, end=t)
    return None
