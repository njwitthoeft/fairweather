from fairweather.tides import (
    TideRequest,
    fetch_tides,
    find_next_tides,
    find_last_tide,
)


def main():
    response = fetch_tides(TideRequest())

    last_tide = find_last_tide(response.predictions)
    next_tides = find_next_tides(response.predictions)

    print("Last tide:")
    print(last_tide.local_time())

    print("Next tides:")
    for tide in next_tides:
        print(tide.local_time())


if __name__ == "__main__":
    main()
