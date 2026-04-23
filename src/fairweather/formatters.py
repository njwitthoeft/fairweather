from fairweather.direction import humanize


def render_detailed_report(
    spot_name: str,
    cycle,
    waves_forecast,
    winds_forecast,
) -> str:

    lines = []
    lines.append(f"{spot_name}")

    # Tide summary
    start_local = cycle.start.local_time()
    end_local = cycle.end.local_time()
    cycle_type = "Ebb" if cycle.is_ebb() else "Flood"
    spread = cycle.spread()
    start_h = cycle.start.height
    end_h = cycle.end.height
    start_lbl = "H" if cycle.start.tide_type == "H" else "L"
    end_lbl = "H" if cycle.end.tide_type == "H" else "L"

    lines.append("")
    lines.append(f"Optimal tide for {start_local.month}/{start_local.day}:")
    lines.append(f"- {cycle_type} tide starting at {start_local.strftime('%H:%M')}")
    lines.append(f"- {start_lbl} {start_local.strftime('%H:%M')} {start_h:.1f}ft")
    lines.append(f"- {end_lbl} {end_local.strftime('%H:%M')} {end_h:.1f}ft")
    lines.append(f"- Spread {spread:.1f} ft")
    lines.append("")

    # Waves
    lines.append("Wave Forecast:")
    lines.append(f"- Mean wave height: {waves_forecast.mean_wave_height():.1f} ft")
    max_e = waves_forecast.max_wave_height_entry()
    min_e = waves_forecast.min_wave_height_entry()
    lines.append(
        f"- Max: {max_e.time.astimezone().strftime('%H:%M')} — {max_e.wave_height:.1f} ft, period {max_e.wave_period:.2f}s, dir {humanize(max_e.wave_direction)}"
    )
    lines.append(
        f"- Min: {min_e.time.astimezone().strftime('%H:%M')} — {min_e.wave_height:.1f} ft, period {min_e.wave_period:.2f}s, dir {humanize(min_e.wave_direction)}"
    )

    lines.append("")

    # Winds
    lines.append("Wind Forecast:")
    lines.append(f"- Mean wind speed: {winds_forecast.mean_wind_speed():.1f} mph")
    lines.append(
        f"- Mean wind direction: {humanize(winds_forecast.mean_wind_direction())}"
    )
    max_w = winds_forecast.max_wind_entry()
    min_w = winds_forecast.min_wind_entry()
    lines.append(
        f"- Max: {max_w.time.astimezone().strftime('%H:%M')} — {max_w.wind_speed_mph:.1f} mph, dir {humanize(max_w.wind_direction)}"
    )
    lines.append(
        f"- Min: {min_w.time.astimezone().strftime('%H:%M')} — {min_w.wind_speed_mph:.1f} mph, dir {humanize(min_w.wind_direction)}"
    )

    lines.append("")

    # Temperatures: report the highest and lowest temperatures from winds hourlies
    lines.append("Temperatures:")
    temps_seq = winds_forecast.hourlies
    min_e = min(temps_seq, key=lambda h: h.temperature)
    max_e = max(temps_seq, key=lambda h: h.temperature)
    lines.append(
        f"- Low:  {min_e.temperature:.1f}°F at {min_e.time.astimezone().strftime('%H:%M')}"
    )
    lines.append(
        f"- High: {max_e.temperature:.1f}°F at {max_e.time.astimezone().strftime('%H:%M')}"
    )

    # Rain: sum hourly rain in winds forecast
    lines.append("")
    lines.append("Rain:")
    total_rain = sum(h.rain for h in winds_forecast.hourlies)
    lines.append(f"- {total_rain:.1f} inches over tide")

    return "\n".join(lines)
