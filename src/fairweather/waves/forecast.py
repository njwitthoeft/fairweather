from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel

from fairweather.waves.api import WaveForecastResponse

OPEN_METEO_MARINE = "https://marine-api.open-meteo.com/v1/marine"
M_TO_FT = 3.28084


class HourlyForecast(BaseModel):
    time: datetime
    wave_height: float
    wave_period: float
    wave_direction: int

    wind_wave_height: float
    wind_wave_period: float
    wind_wave_direction: int

    def __str__(self):
        local = self.time.astimezone().strftime("%Y-%m-%d %H:%M")
        return (
            f"At {local}, wave height: {self.wave_height:.1f} ft, period: {self.wave_period:.0f} s, direction: {self.wave_direction}°; "
            f"wind wave height: {self.wind_wave_height:.1f} ft, period: {self.wind_wave_period:.0f} s, direction: {self.wind_wave_direction}°"
        )


def forecast_response_to_hourly_entries(
    forecast: WaveForecastResponse,
) -> List[HourlyForecast]:
    entries = []

    for (
        time,
        wave_height,
        wave_period,
        wave_direction,
        wind_wave_height,
        wind_wave_period,
        wind_wave_direction,
    ) in zip(
        forecast.hourly.time,
        forecast.hourly.wave_height,
        forecast.hourly.wave_period,
        forecast.hourly.wave_direction,
        forecast.hourly.wind_wave_height,
        forecast.hourly.wind_wave_period,
        forecast.hourly.wind_wave_direction,
    ):
        entry = HourlyForecast(
            time=datetime.fromisoformat(time).astimezone(timezone.utc),
            wave_height=wave_height * M_TO_FT,
            wave_period=wave_period,
            wave_direction=wave_direction,
            wind_wave_height=wind_wave_height * M_TO_FT,
            wind_wave_period=wind_wave_period,
            wind_wave_direction=wind_wave_direction,
        )
        entries.append(entry)

    return entries


class WaveForecast(BaseModel):
    hourlies: List[HourlyForecast]

    @classmethod
    def from_response(cls, response: WaveForecastResponse) -> "WaveForecast":
        hourlies = forecast_response_to_hourly_entries(response)
        return cls(hourlies=hourlies)

    def within_time_range(
        self, cycle_start: datetime, cycle_end: datetime
    ) -> List[HourlyForecast]:
        return WaveForecast(
            hourlies=[
                entry
                for entry in self.hourlies
                if cycle_start <= entry.time <= cycle_end
            ]
        )

    def max_wave_height_entry(self) -> float:
        max_entry = max(self.hourlies, key=lambda e: e.wave_height)
        return max_entry

    def min_wave_height_entry(self) -> float:
        min_entry = min(self.hourlies, key=lambda e: e.wave_height)
        return min_entry

    def mean_wave_height(self) -> float:
        assert len(self.hourlies) > 0
        total_height = sum(entry.wave_height for entry in self.hourlies)
        return total_height / len(self.hourlies)
