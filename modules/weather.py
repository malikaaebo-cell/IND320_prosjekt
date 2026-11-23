# weather.py
# Download of ERA5 weather data from open-meteo for the Streamlit app.
#
# get_weather()        (part 3) hourly data for one area and one year, used by the weather
#                      analysis page (SATV and LOF). Same method as download_weather() in the
#                      part 3 notebook: the area's random locations are rounded to the ERA5 0.25°
#                      grid, and the average is weighted by the number of locations per grid cell.
#                      To fit in one request, the app uses a random sample of 10 grid cells
#                      (the complete notebook download is used if it exists in project_data/).
# weather_for_period() (part 4) daily data for ALL areas of one type over a short period
#                      (one week), aggregated per area, used to colour the map.
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
HOURLY_VARS = ['temperature_2m', 'precipitation', 'rain', 'snowfall',
               'relative_humidity_2m', 'wind_speed_10m', 'cloud_cover', 'shortwave_radiation']

# Readable labels with units for the selectors and axes
HOURLY_LABELS = {
    'temperature_2m': 'Temperature (°C)',
    'precipitation': 'Precipitation (mm)',
    'rain': 'Rain (mm)',
    'snowfall': 'Snowfall (cm)',
    'relative_humidity_2m': 'Relative humidity (%)',
    'wind_speed_10m': 'Wind speed (km/h)',
    'cloud_cover': 'Cloud cover (%)',
    'shortwave_radiation': 'Shortwave radiation (W/m²)',
}

# Daily variables (same as in the part 4 notebook); the sums are summed per week,
# the others averaged
DAILY_VARS = ['temperature_2m_mean', 'precipitation_sum', 'rain_sum', 'snowfall_sum',
              'wind_speed_10m_mean', 'shortwave_radiation_sum']
SUM_VARS = ['precipitation_sum', 'rain_sum', 'snowfall_sum', 'shortwave_radiation_sum']
DAILY_LABELS = {
    'temperature_2m_mean': 'Mean temperature (°C)',
    'precipitation_sum': 'Precipitation (mm)',
    'rain_sum': 'Rain (mm)',
    'snowfall_sum': 'Snowfall (cm)',
    'wind_speed_10m_mean': 'Mean wind speed (km/h)',
    'shortwave_radiation_sum': 'Shortwave radiation (MJ/m²)',
}

# project_data/ in the repository (one level above the modules folder)
DATA_DIR = Path(__file__).resolve().parent.parent / 'project_data'


class WeatherError(RuntimeError):
    """Raised with a readable message when open-meteo cannot deliver the data."""


@st.cache_data
def load_locations():
    """Read the 1000 random locations per region, made in the notebook from the NVE shapefiles."""
    return pd.read_csv(DATA_DIR / 'locations.csv')


def grid_cells(area, n_cells, seed=320):
    """
    The area's random locations rounded to the ERA5 0.25° grid, with the number of locations
    in each cell as weight, and a random sample of n_cells cells (same seed as the notebook).
    """
    locations = load_locations()
    pts = locations[locations['area'] == area]
    cells = (pts.assign(lat=(pts['lat'] * 4).round() / 4, lon=(pts['lon'] * 4).round() / 4)
                .groupby(['lat', 'lon']).size().rename('n').reset_index())
    return cells.sample(min(n_cells, len(cells)), random_state=seed)


def request_archive(params):
    """Call open-meteo's archive API and turn the usual problems into readable errors."""
    try:
        r = requests.get(ARCHIVE_URL, params=params, timeout=120)
    except requests.RequestException as error:
        raise WeatherError(f"Could not reach open-meteo: {error}") from error
    if r.status_code == 429:
        raise WeatherError("open-meteo's API limit is reached. Wait a minute and try again.")
    if r.status_code != 200:
        reason = r.json().get('reason', r.text[:200]) if r.headers.get('content-type', '').startswith('application/json') else r.text[:200]
        raise WeatherError(f"open-meteo returned an error ({r.status_code}): {reason}")
    data = r.json()
    return [data] if isinstance(data, dict) else data      # one location gives a dict


# Cached, so each area and year is only downloaded once
@st.cache_data(show_spinner="Downloading hourly weather data from open-meteo ...")
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

    cells = grid_cells(area, n_cells)
    params = {'latitude': ','.join(cells['lat'].astype(str)),
              'longitude': ','.join(cells['lon'].astype(str)),
              'start_date': start, 'end_date': end,
              'hourly': ','.join(HOURLY_VARS), 'models': 'era5', 'timezone': 'GMT'}
    data = request_archive(params)

    # One DataFrame per grid cell, with the number of locations in the cell as weight
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


@st.cache_data(show_spinner="Downloading weather data for the map ...")
def weather_for_period(area_type, start, end, n_cells=3):
    """
    Daily ERA5 data for all areas of one type ('EL', 'VASS' or 'NO') between start and end
    ('YYYY-MM-DD'), aggregated over the period: sums for precipitation, rain, snowfall and
    radiation, means for the others. Each area is represented by n_cells grid cells.
    Returns a DataFrame with one row per area.
    """
    # The grid cells of every area of this type, in one request
    areas = sorted(a for a in load_locations()['area'].unique() if a.split()[0] == area_type)
    cells = pd.concat([grid_cells(a, n_cells).assign(area=a) for a in areas], ignore_index=True)
    params = {'latitude': ','.join(cells['lat'].astype(str)),
              'longitude': ','.join(cells['lon'].astype(str)),
              'start_date': start, 'end_date': end,
              'daily': ','.join(DAILY_VARS), 'models': 'era5', 'timezone': 'Europe/Oslo'}
    data = request_archive(params)

    # Aggregate each cell over the period, then a weighted average over the cells of each area
    rows = []
    for (_, cell), loc in zip(cells.iterrows(), data):
        daily = pd.DataFrame(loc['daily']).drop(columns='time').astype(float)
        agg = {v: (daily[v].sum(min_count=1) if v in SUM_VARS else daily[v].mean()) for v in DAILY_VARS}
        rows.append({'area': cell['area'], 'n': cell['n'], **agg})
    per_cell = pd.DataFrame(rows)
    weighted = per_cell[DAILY_VARS].multiply(per_cell['n'], axis=0)
    return weighted.groupby(per_cell['area']).sum(min_count=1).div(per_cell.groupby('area')['n'].sum(), axis=0)
