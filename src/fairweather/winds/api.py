from typing import List, Literal

from pydantic import BaseModel, Field
import httpx

OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"


class WindRequest(BaseModel):
    latitude: float
    longitude: float
    timezone: Literal["GMT"] = "GMT"
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD

    hourly: List[str] = Field(
        default_factory=lambda: [
            "wind_speed_10m",
            "wind_direction_10m",
            "temperature_2m",
            "rain",
        ]
    )


class HourlyWindDataSOA(BaseModel):
    time: List[str]
    wind_speed_10m: List[float]
    wind_direction_10m: List[int]
    temperature_2m: List[float]
    rain: List[float]


class HourlyWindUnits(BaseModel):
    time: str
    wind_speed_10m: str
    wind_direction_10m: Literal["°"]
    temperature_2m: str
    rain: str


class WindForecastResponse(BaseModel):
    hourly: HourlyWindDataSOA
    latitude: float
    longitude: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float
    hourly_units: HourlyWindUnits


def fetch_wind_forecast(wind_request: WindRequest) -> WindForecastResponse:
    with httpx.Client(http2=True) as client:
        resp = client.get(
            OPEN_METEO_FORECAST, params=wind_request.model_dump(), timeout=10
        )

    if hasattr(resp, "status_code"):
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Open-Meteo API error {resp.status_code}: {getattr(resp, 'text', '')}"
            )
    else:
        try:
            resp.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Open-Meteo API error: {getattr(resp, 'text', str(e))}")

    return WindForecastResponse.model_validate_json(resp.text)
