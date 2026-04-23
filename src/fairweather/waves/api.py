from typing import List, Literal

from pydantic import BaseModel, Field
import httpx

OPEN_METEO_MARINE = "https://marine-api.open-meteo.com/v1/marine"
M_TO_FT = 3.28084


class WaveRequest(BaseModel):
    latitude: float
    longitude: float
    timezone: Literal["GMT"] = "GMT"
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD

    # fields we want hourly data on
    hourly: List[str] = Field(
        default_factory=lambda: [
            "wave_height",
            "wave_period",
            "wind_wave_period",
            "wind_wave_direction",
            "wave_direction",
            "wind_wave_height",
        ]
    )


class HourlyDataSOA(BaseModel):
    time: List[str]
    wave_height: List[float]
    wave_period: List[float]
    wave_direction: List[int]

    wind_wave_height: List[float]
    wind_wave_period: List[float]
    wind_wave_direction: List[int]


class HourlySOAUnits(BaseModel):
    time: str
    wave_height: Literal["m"]
    wave_period: Literal["s"]
    wave_direction: Literal["°"]

    wind_wave_height: Literal["m"]
    wind_wave_period: Literal["s"]
    wind_wave_direction: Literal["°"]


class WaveForecastResponse(BaseModel):
    hourly: HourlyDataSOA
    latitude: float
    longitude: float
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    elevation: float
    hourly_units: HourlySOAUnits


def fetch_wave_forecast(wave_request: WaveRequest) -> WaveForecastResponse:
    with httpx.Client(http2=True) as client:
        resp = client.get(
            OPEN_METEO_MARINE, params=wave_request.model_dump(), timeout=10
        )

    # Provide the API response body on error to aid debugging of 400 responses.
    # Some tests use fake responses that implement `raise_for_status()` but
    # not `status_code`, so handle both.
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

    return WaveForecastResponse.model_validate_json(resp.text)
