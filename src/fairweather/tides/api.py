from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    PlainSerializer,
    Field,
    field_validator,
)
import httpx

StrInt = Annotated[int, PlainSerializer(lambda x: str(x), return_type=str)]

NOAA_TIDES_ENDPOINT = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"


def yesterday_date_str():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    return yesterday.strftime("%Y%m%d")


class TideRequest(BaseModel):
    product: str = "predictions"
    datum: str = "MLLW"
    interval: str = "hilo"
    units: str = "english"
    time_zone: Literal["gmt"] = "gmt"
    format: str = "json"

    begin_date: str = Field(default_factory=yesterday_date_str)
    range: StrInt = 72  # from yesterday to today to the next day (24 x 3)

    station: StrInt = 9455500


class TurnPrediction(BaseModel):
    timestamp: datetime = Field(alias="t")
    tide_type: Literal["H", "L"] = Field(alias="type")
    height: float = Field(alias="v")

    class ConfigDict:
        populate_by_name = True

    def __str__(self):
        return f"{self.tide_type} tide at {self.local_time().strftime('%Y-%m-%d %H:%M')} with height {self.height} ft"

    @field_validator("timestamp", mode="before")
    def _parse_timestamp_to_utc(cls, v):
        # NOAA returns times like 'YYYY-MM-DD HH:MM' when asked for GMT.
        # Accept strings with or without timezone info and ensure result is
        # timezone-aware in UTC for reliable comparisons.
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def local_time(self) -> datetime:
        local_tz = datetime.now().astimezone().tzinfo
        return self.timestamp.astimezone(local_tz)


class TurnPredictionResponse(BaseModel):
    predictions: list[TurnPrediction]


def fetch_tides(request: TideRequest) -> TurnPredictionResponse:
    """Fetch tide predictions from NOAA API."""

    # hit NOAA api with httpx
    with httpx.Client(http2=True) as client:
        response = client.get(
            NOAA_TIDES_ENDPOINT, params=request.model_dump(), timeout=10
        )

    response.raise_for_status()

    return TurnPredictionResponse.model_validate_json(response.text)
