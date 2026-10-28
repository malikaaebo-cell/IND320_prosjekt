# weather.py
# Download of hourly ERA5 weather data from open-meteo for the Streamlit app (part 3).
# Same method as download_weather() in the notebook: the region's random locations are
# rounded to the ERA5 0.25° grid, and the regional average is weighted by the number of
# locations in each grid cell.
#
# Difference from the notebook: downloading all grid cells for one region and one year
# takes about an hour because of open-meteo's free API limits (600 calls/minute,
# 5000/hour, 10 000/day). The app therefore uses a random sample of the grid cells
# (default 10), which fits in a single request. If the complete download from the
# notebook exists in project_data/, that file is used instead.
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
HOURLY_VARS = ['temperature_2m', 'precipitation', 'rain', 'snowfall',
               'relative_humidity_2m', 'wind_speed_10m', 'cloud_cover', 'shortwave_radiation']

# project_data/ in the repository (one level above the modules folder)
DATA_DIR = Path(__file__).resolve().parent.parent / 'project_data'


@st.cache_data
def load_locations():
    """Read the 1000 random locations per region, made in the notebook from the NVE shapefiles."""
    return pd.read_csv(DATA_DIR / 'locations.csv')


# Cached, so each area and year is only downloaded once
@st.cache_data(show_spinner="Downloading weather data from open-meteo ...")
def get_weather(area, year, n_cells=10):
    """
    Get hourly ERA5 data for an area (e.g. 'EL 3') and a year, averaged over the area.
    Returns the data and a short text describing which locations were used.
    """
    start, end = f'{year}-01-01', f'{year}-12-31'

    # Use the complete download from the notebook (all 1000 locations) if it exists
    file = DATA_DIR / f"weather_{area.replace(' ', '')}_{start}_{end}.csv"
    if file.exists():
        weather = pd.read_csv(file, index_col='time', parse_dates=True)
        return weather, "all 1000 locations (downloaded in the notebook)"

    # Round the area's locations to the ERA5 grid and count the locations per grid cell
    locations = load_locations()
    pts = locations[locations['area'] == area]
    cells = (pts.assign(lat=(pts['lat'] * 4).round() / 4, lon=(pts['lon'] * 4).round() / 4)
                .groupby(['lat', 'lon']).size().rename('n').reset_index())

    # Random sample of the grid cells, so the download fits in one request
    cells = cells.sample(min(n_cells, len(cells)), random_state=320)

    params = {'latitude': ','.join(cells['lat'].astype(str)),
              'longitude': ','.join(cells['lon'].astype(str)),
              'start_date': start, 'end_date': end,
              'hourly': ','.join(HOURLY_VARS), 'models': 'era5', 'timezone': 'GMT'}
    r = requests.get(ARCHIVE_URL, params=params, timeout=120)

    # Stop with a clear message if the API limit is reached (the error is not cached)
    if r.status_code == 429:
        raise RuntimeError("open-meteo's API limit is reached. Wait a minute and try again.")
    r.raise_for_status()

    # One DataFrame per grid cell, with the number of locations in the cell as weight
    data = r.json()
    if isinstance(data, dict):                        # one location gives a dict, several give a list
        data = [data]
    frames = []
    for n, loc in zip(cells['n'], data):
        df = pd.DataFrame(loc['hourly'])
        df['n'] = n
        frames.append(df)

    # Weighted average over the grid cells
    data = pd.concat(frames)
    data['time'] = pd.to_datetime(data['time'])
    weather = (data[HOURLY_VARS].multiply(data['n'], axis=0).groupby(data['time']).sum()
               .div(data.groupby('time')['n'].sum(), axis=0))
    return weather, f"{len(cells)} ERA5 grid cells sampled from the 1000 locations"
