from datetime import datetime, timezone
import math
from typing import List

from pydantic import BaseModel

from fairweather.winds.api import WindForecastResponse


class HourlyWindForecast(BaseModel):
    time: datetime
    wind_speed_mph: float
    wind_direction: int
    temperature: float
    rain: float


    def __str__(self):
        local = self.time.astimezone().strftime("%Y-%m-%d %H:%M")
        return (
            f"At {local}, wind speed: {self.wind_speed_mph:.1f} mph, direction: {self.wind_direction}°; "
            f"temperature: {self.temperature:.1f}°F, rain: {self.rain:.1f} in"
        )


def forecast_response_to_hourly_entries(forecast: WindForecastResponse) -> List[HourlyWindForecast]:
    entries: List[HourlyWindForecast] = []

    for (time_str, speed_mph, d, temp, rain) in zip(
        forecast.hourly.time,
        forecast.hourly.wind_speed_10m,
        forecast.hourly.wind_direction_10m,
        forecast.hourly.temperature_2m,
        forecast.hourly.rain,
    ):
        dt = datetime.fromisoformat(time_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        entry = HourlyWindForecast(
            time=dt,
            wind_speed_mph=speed_mph,
            wind_direction=d,
            temperature=temp,
            rain=rain,
        )
        entries.append(entry)

    return entries


class WindForecast(BaseModel):
    hourlies: List[HourlyWindForecast]

    @classmethod
    def from_response(cls, response: WindForecastResponse) -> "WindForecast":
        hourlies = forecast_response_to_hourly_entries(response)
        return cls(hourlies=hourlies)
    

    def within_time_range(self, start: datetime, end: datetime) -> "WindForecast":
        return WindForecast(hourlies=[h for h in self.hourlies if start <= h.time <= end])

    def max_wind_entry(self) -> HourlyWindForecast:
        return max(self.hourlies, key=lambda e: e.wind_speed_mph)

    def min_wind_entry(self) -> HourlyWindForecast:
        return min(self.hourlies, key=lambda e: e.wind_speed_mph)

    def mean_wind_speed(self) -> float:
        assert len(self.hourlies) > 0
        return sum(e.wind_speed_mph for e in self.hourlies) / len(self.hourlies)

    def mean_wind_direction(self) -> float:
        assert len(self.hourlies) > 0
        # average of unit vectors to handle circular nature of direction
        x = sum(math.cos(math.radians(e.wind_direction)) for e in self.hourlies)
        y = sum(math.sin(math.radians(e.wind_direction)) for e in self.hourlies)
        return int(math.degrees(math.atan2(y, x))) % 360
