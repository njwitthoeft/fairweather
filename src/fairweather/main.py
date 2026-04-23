import argparse
import json
import os
from datetime import datetime, date as _date

from fairweather.tides.api import TideRequest, fetch_tides
from fairweather.tides.cycle import (
    find_optimal_tide_cycle,
)
from fairweather.waves.api import WaveRequest, fetch_wave_forecast
from fairweather.waves.forecast import WaveForecast
from fairweather.winds.api import WindRequest, fetch_wind_forecast
from fairweather.winds.forecast import WindForecast
from fairweather.formatters import render_detailed_report


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

        # Create formatted text output (detailed report)
        detailed = render_detailed_report(
            spot["name"], optimal_cycle, waves_during_cycle, winds_during_cycle
        )

        out_dir = os.environ.get("FAIRWEATHER_OUT", "out")
        os.makedirs(out_dir, exist_ok=True)
        safe_name = (
            "".join(c for c in spot["name"] if c.isalnum() or c in ("-", "_", " "))
            .strip()
            .replace(" ", "_")
        )
        date_tag = optimal_cycle.start.timestamp.date().isoformat()
        report_path = os.path.join(out_dir, f"{safe_name}-report-{date_tag}.txt")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(detailed)

        print(f"Wrote detailed report: {report_path}")

        print("\n" + "=" * 40 + "\n")


if __name__ == "__main__":
    main()
