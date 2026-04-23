import json

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

    with open("data/locations.json") as f:
        spots_to_predict = json.load(f)["spots_to_predict"]

    for spot in spots_to_predict:
        print(f"Fetching data for {spot['name']}...")

        tide_response = fetch_tides(
            TideRequest()
        )  # get tides at seldovia from yesterday to tomorrow

        optimal_cycle = find_optimal_tide_cycle(tide_response.predictions)

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

        print("\nWave forecast during optimal cycle:")
        print(f"Mean wave height: {waves_during_cycle.mean_wave_height()}")
        print(f"Max wave height entry: {waves_during_cycle.max_wave_height_entry()}")
        print(f"Min wave height entry: {waves_during_cycle.min_wave_height_entry()}")

        print("\nWind forecast during optimal cycle:")
        print(f"Mean wind speed: {winds_during_cycle.mean_wind_speed()}")
        print(f"Mean wind direction: {humanize(winds_during_cycle.mean_wind_direction())}")
        print(f"Max wind speed entry: {winds_during_cycle.max_wind_entry()}")
        print(f"Min wind speed entry: {winds_during_cycle.min_wind_entry()}")



        print("\n" + "=" * 40 + "\n")


if __name__ == "__main__":
    main()
