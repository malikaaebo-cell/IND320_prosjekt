"""
Download the daily weather (2010 until today) for all areas in advance, so the correlation and
forecast pages in the app do not have to wait for open-meteo (part 4).

Each area counts as about 1400 calls in open-meteo's free API (limits: 600 per minute,
5000 per hour, 10 000 per day), so the script waits when a limit is reached and continues.
Areas that are already downloaded (files in project_data/) are skipped.

Run from the project folder:
    .venv/bin/python scripts/download_weather.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.weekly_data import download_daily_weather, weather_file   # noqa: E402
from modules.weather import WeatherError                                # noqa: E402

AREAS = ['EL 1', 'EL 2', 'EL 3', 'EL 4', 'EL 5', 'VASS 1', 'VASS 2', 'VASS 3', 'NO 0']

for area in AREAS:
    while not weather_file(area).exists():
        try:
            print(f"Downloading {area} ...", flush=True)
            download_daily_weather(area)
            print(f"  saved {weather_file(area).name}", flush=True)
        except WeatherError as error:
            print(f"  {error} Waiting 10 minutes ...", flush=True)
            time.sleep(600)
    print(f"{area}: done")
