def main():
    print("Hello from fairweather!")

    from src.fairweather.tides import (
        TideRequest,
        fetch_tides,
        find_next_tides,
        find_last_tide,
    )

    response = fetch_tides(TideRequest())

    for tide in response.predictions:
        print(tide.local_time())

    last_tide = find_last_tide(response.predictions)
    print("Last tide:")
    print(last_tide)

    next_tides = find_next_tides(response.predictions)
    print("Next tides:")
    for tide in next_tides:
        print(tide)


if __name__ == "__main__":
    main()
