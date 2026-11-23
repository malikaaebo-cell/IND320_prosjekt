# weekly_data.py
# Weekly data set for the correlation and forecast pages (part 4), built as in the part 4
# notebook: the weekly degree of filling from Magasinstatistikk, joined on ISO year and week
# with daily ERA5 weather (requested in Norwegian time, summed or averaged per week) and,
# optionally, the EUR and USD exchange rates (weekly means of the business days).
#
# The daily weather download covers many years, so it counts as many calls in open-meteo's
# free API (one call per location and two weeks). The download is therefore done year by year
# with a pause before the limit of 600 calls per minute, a progress bar shows how far it has
# come (bonus: waiting time), and the result is saved in project_data/ and cached, so it is only
# downloaded once per area.
import time

import pandas as pd
import streamlit as st

from modules.data_loader import load_data_or_stop
from modules.weather import DATA_DIR, DAILY_VARS, SUM_VARS, grid_cells, request_archive
from modules.currency import exchange_rates_or_none

START_YEAR = 2010     # first year of weather data (as in the notebook)
N_CELLS = 3           # grid cells per area (as in the notebook)


def weather_file(area, start_year=START_YEAR, n_cells=N_CELLS):
    """File name used by both the notebook and the app for the daily weather of an area."""
    return DATA_DIR / f"weather_daily_{area.replace(' ', '')}_{start_year}_{n_cells}cells.csv"


@st.cache_data(show_spinner=False)
def download_daily_weather(area, start_year=START_YEAR, n_cells=N_CELLS, _progress=None):
    """
    Daily ERA5 weather for an area (e.g. 'EL 3'), averaged over n_cells grid cells, from
    start_year until about a week ago. Saved to project_data/ and read from there next time.
    _progress : optional st.progress element updated during the download (not part of the cache key)
    """
    file = weather_file(area, start_year, n_cells)
    if file.exists():
        return pd.read_csv(file, index_col='time', parse_dates=True)

    cells = grid_cells(area, n_cells)
    end = pd.Timestamp.today().normalize() - pd.Timedelta(days=7)   # ERA5 lags about 5 days
    years = list(range(start_year, end.year + 1))
    frames, used = [], 0
    for i, year in enumerate(years):
        # One year for n cells counts as about n * 27 calls; pause before passing 600 per minute
        weight = len(cells) * 27
        if used + weight > 550:
            if _progress is not None:
                _progress.progress(i / len(years), text=f"{area}: waiting one minute for open-meteo's "
                                                        f"rate limit ({year - start_year} of {len(years)} years done) ...")
            time.sleep(61)
            used = 0
        if _progress is not None:
            _progress.progress(i / len(years), text=f"{area}: downloading weather for {year} ...")
        params = {'latitude': ','.join(cells['lat'].astype(str)),
                  'longitude': ','.join(cells['lon'].astype(str)),
                  'start_date': f'{year}-01-01',
                  'end_date': min(pd.Timestamp(f'{year}-12-31'), end).strftime('%Y-%m-%d'),
                  'daily': ','.join(DAILY_VARS), 'models': 'era5', 'timezone': 'Europe/Oslo'}
        result = request_archive(params)
        used += weight
        for n, loc in zip(cells['n'], result):
            frames.append(pd.DataFrame(loc['daily']).assign(n=n))

    # Weighted average over the grid cells
    data = pd.concat(frames)
    data['time'] = pd.to_datetime(data['time'])
    weather = (data[DAILY_VARS].multiply(data['n'], axis=0).groupby(data['time']).sum()
               .div(data.groupby('time')['n'].sum(), axis=0))
    try:
        weather.to_csv(file)          # saved for later runs (may fail on a read-only server)
    except OSError:
        pass
    return weather


def to_iso_weeks(daily, sum_cols=()):
    """Aggregate a daily DataFrame to ISO year and week: sums for sum_cols, means otherwise."""
    iso = daily.index.isocalendar()
    keys = [iso['year'].astype(int).rename('iso_year'), iso['week'].astype(int).rename('iso_week')]
    agg = {c: ('sum' if c in sum_cols else 'mean') for c in daily.columns}
    return daily.groupby(keys).agg(agg)


def weekly_data(area, with_weather=True, with_currency=False):
    """
    Weekly data set for an area, with the NVE date (Sunday ending the ISO week) as index:
    'fill' and 'fill_change' (degree of filling and its weekly change, in %), plus the daily
    weather variables and/or 'EUR' and 'USD' aggregated to the same weeks.
    Shows a progress bar while weather data is downloaded for the first time.
    """
    df = load_data_or_stop()
    fill = df[(df['area'] == area) & (df['date'].dt.year >= START_YEAR)]
    data = fill.set_index(['iso_year', 'iso_week'])[['date', 'fill_ratio', 'fill_ratio_change']].copy()
    data['fill'] = 100 * data.pop('fill_ratio')              # per cent works better with SGD
    data['fill_change'] = 100 * data.pop('fill_ratio_change')

    if with_weather:
        bar = None if weather_file(area).exists() else st.progress(0.0, text="Preparing weather download ...")
        weather = download_daily_weather(area, _progress=bar)
        if bar is not None:
            bar.empty()
        data = data.join(to_iso_weeks(weather, SUM_VARS))
    if with_currency:
        fx = exchange_rates_or_none(f'{START_YEAR}-01-01', pd.Timestamp.today().strftime('%Y-%m-%d'))
        if fx is not None:
            data = data.join(to_iso_weeks(fx))

    # Short gaps in the inputs (e.g. the latest week before ERA5 is published) are filled forward
    data = data.reset_index().set_index('date').sort_index().ffill()
    return data
