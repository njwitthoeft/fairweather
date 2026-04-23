import argparse
import json
from datetime import datetime, date as _date

from fairweather.direction import humanize
from fairweather.tides.api import TideRequest, fetch_tides
from fairweather.tides.cycle import (
    find_optimal_tide_cycle,
)
from fairweather.waves.api import WaveRequest, fetch_wave_forecast
from fairweather.waves.forecast import WaveForecast
from fairweather.winds.api import WindRequest, fetch_wind_forecast
from fairweather.winds.forecast import WindForecast


def main():
    """Run a tide selection and forecast for the next optimal cycle, printing results for local development."""
    parser = argparse.ArgumentParser(
        description="Fetch tide and marine forecasts for spots"
    )
    parser.add_argument(
        "--date", help="Target date (YYYY-MM-DD) to search for tide turns"
    )
    args = parser.parse_args()

    with open("data/locations.json") as f:
        spots_to_predict = json.load(f)["spots_to_predict"]

    target_date: _date | None = None
    if args.date:
        target_date = datetime.fromisoformat(args.date).date()

    for spot in spots_to_predict:
        print(f"Fetching data for {spot['name']}...")

        # Set the begin_date on the TideRequest when a target date was provided so
        # NOAA returns predictions covering that day.
        if target_date:
            tide_req = TideRequest(begin_date=target_date.strftime("%Y%m%d"))
        else:
            tide_req = TideRequest()

        tide_response = fetch_tides(tide_req)

        optimal_cycle = find_optimal_tide_cycle(
            tide_response.predictions, target_date=target_date
        )

        if optimal_cycle is None:
            print("No optimal tide cycle found in the next 24 hours.")
            return

        # get a wave forecast for the duration of the optimal cycle
        wave_request = WaveRequest(
            latitude=spot["latitude"],
            longitude=spot["longitude"],
            start_date=optimal_cycle.start.timestamp.date().isoformat(),
            end_date=optimal_cycle.end.timestamp.date().isoformat(),
        )
        wave_forecast = WaveForecast.from_response(fetch_wave_forecast(wave_request))

        # get a wind forecast for the duration of the optimal cycle
        wind_request = WindRequest(
            latitude=spot["latitude"],
            longitude=spot["longitude"],
            start_date=optimal_cycle.start.timestamp.date().isoformat(),
            end_date=optimal_cycle.end.timestamp.date().isoformat(),
        )
        wind_forecast = WindForecast.from_response(fetch_wind_forecast(wind_request))

        waves_during_cycle = wave_forecast.within_time_range(
            optimal_cycle.start.timestamp, optimal_cycle.end.timestamp
        )
        winds_during_cycle = wind_forecast.within_time_range(
            optimal_cycle.start.timestamp, optimal_cycle.end.timestamp
        )

        print("Optimal tide cycle:")
        print(optimal_cycle)

        # Waves
        mean_wh = waves_during_cycle.mean_wave_height()
        max_wh_entry = waves_during_cycle.max_wave_height_entry()
        min_wh_entry = waves_during_cycle.min_wave_height_entry()

        print("\nWave forecast during optimal cycle:")
        print(f"- Mean wave height: {mean_wh:.2f} ft")
        print(
            "- Max wave:",
            f"{max_wh_entry.time.astimezone().strftime('%Y-%m-%d %H:%M')} — {max_wh_entry.wave_height:.2f} ft, period {max_wh_entry.wave_period}s, dir {humanize(max_wh_entry.wave_direction)};",
            f"wind-wave {max_wh_entry.wind_wave_height:.2f} ft, period {max_wh_entry.wind_wave_period}s, dir {humanize(max_wh_entry.wind_wave_direction)}",
        )
        print(
            "- Min wave:",
            f"{min_wh_entry.time.astimezone().strftime('%Y-%m-%d %H:%M')} — {min_wh_entry.wave_height:.2f} ft, period {min_wh_entry.wave_period}s, dir {humanize(min_wh_entry.wave_direction)};",
            f"wind-wave {min_wh_entry.wind_wave_height:.2f} ft, period {min_wh_entry.wind_wave_period}s, dir {humanize(min_wh_entry.wind_wave_direction)}",
        )

        # Winds
        mean_ws = winds_during_cycle.mean_wind_speed()
        mean_wd = winds_during_cycle.mean_wind_direction()
        max_w_entry = winds_during_cycle.max_wind_entry()
        min_w_entry = winds_during_cycle.min_wind_entry()

        print("\nWind forecast during optimal cycle:")
        print(f"- Mean wind speed: {mean_ws:.1f} mph")
        print(f"- Mean wind direction: {humanize(mean_wd)}")
        print(
            "- Max wind:",
            f"{max_w_entry.time.strftime('%Y-%m-%d %H:%M')} — {max_w_entry.wind_speed_mph:.1f} mph, {humanize(max_w_entry.wind_direction)}; temp {max_w_entry.temperature:.1f}°F; rain {max_w_entry.rain:.1f} in",
        )
        print(
            "- Min wind:",
            f"{min_w_entry.time.strftime('%Y-%m-%d %H:%M')} — {min_w_entry.wind_speed_mph:.1f} mph, {humanize(min_w_entry.wind_direction)}; temp {min_w_entry.temperature:.1f}°F; rain {min_w_entry.rain:.1f} in",
        )

        print("\n" + "=" * 40 + "\n")


if __name__ == "__main__":
    main()
