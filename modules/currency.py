# currency.py
# Daily EUR and USD exchange rates (NOK per unit) from Norges Bank's open SDMX API (part 4).
# Same function as download_exchange_rates() in the part 4 notebook: the period is downloaded
# one year at a time, each request is retried if the server does not answer (Norges Bank has
# returned "522 Connection timed out"), and the rates are saved to project_data/ and used from
# there if the API is unavailable. The app adds caching and readable error messages.
import time

import pandas as pd
import requests
import streamlit as st

from modules.weather import DATA_DIR

NB_URL = "https://data.norges-bank.no/api/data/EXR/B.{currencies}.NOK.SP"
RATES_FILE = DATA_DIR / 'exchange_rates.csv'     # local copy, used if Norges Bank is unavailable


def _parse_sdmx_json(data):
    """Turn Norges Bank's sdmx-json response into a DataFrame with one column per currency."""
    # The dates are listed once, in the observation dimension
    dates = [v['id'] for v in data['structure']['dimensions']['observation'][0]['values']]

    # The series dimensions (FREQ, BASE_CUR, QUOTE_CUR, TENOR); find BASE_CUR by name
    series_dims = data['structure']['dimensions']['series']
    base_pos = [d['id'] for d in series_dims].index('BASE_CUR')
    base_values = [v['id'] for v in series_dims[base_pos]['values']]

    # Each series has a key like '0:1:0:0' pointing into the dimension lists, and its
    # observations are stored as {date position: [value, ...]}
    columns = {}
    for key, series in data['dataSets'][0]['series'].items():
        currency = base_values[int(key.split(':')[base_pos])]
        columns[currency] = pd.Series(
            {pd.Timestamp(dates[int(i)]): float(obs[0]) for i, obs in series['observations'].items()})
    return pd.DataFrame(columns)


def _get_period(url, start, end, retries=3):
    """One request for a period, tried up to 'retries' times if the server does not answer."""
    params = {'format': 'sdmx-json', 'startPeriod': start, 'endPeriod': end, 'locale': 'en'}
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return _parse_sdmx_json(r.json()['data'])
        except (requests.RequestException, KeyError, ValueError):
            if attempt == retries:
                raise
            time.sleep(5 * attempt)           # wait a little longer before each new attempt


# Cached for 6 hours: the rates are published once per business day
@st.cache_data(ttl=6 * 3600, show_spinner="Downloading exchange rates from Norges Bank ...")
def download_exchange_rates(start, end, currencies=('EUR', 'USD')):
    """
    Download daily exchange rates (NOK per unit of foreign currency) from Norges Bank.

    start, end : first and last date, 'YYYY-MM-DD'
    currencies : base currencies, e.g. ('EUR', 'USD')
    Returns a DataFrame with one column per currency and the date as index.
    The period is downloaded one year at a time (small, fast requests), each request is
    retried if the server does not answer, and the result is saved to project_data/. If
    Norges Bank is unavailable, the saved rates are used instead.
    """
    url = NB_URL.format(currencies='+'.join(currencies))
    try:
        years = range(pd.Timestamp(start).year, pd.Timestamp(end).year + 1)
        parts = [_get_period(url, max(start, f'{y}-01-01'), min(end, f'{y}-12-31')) for y in years]
        rates = pd.concat(parts).sort_index()
        rates.index.name = 'date'
        # Merge with the saved rates (if any), so the file keeps the longest period downloaded
        saved = pd.read_csv(RATES_FILE, index_col='date', parse_dates=True) if RATES_FILE.exists() else None
        try:
            (rates.combine_first(saved) if saved is not None else rates).to_csv(RATES_FILE)
        except OSError:
            pass                                  # e.g. a read-only file system on the server
    except (requests.RequestException, KeyError, ValueError) as error:
        if not RATES_FILE.exists():
            raise
        rates = pd.read_csv(RATES_FILE, index_col='date', parse_dates=True)
    return rates.loc[start:end, list(currencies)]


def exchange_rates_or_none(start, end):
    """Exchange rates, or None with a warning in the app if neither Norges Bank nor the saved file has them."""
    try:
        return download_exchange_rates(start, end)
    except (requests.RequestException, KeyError, ValueError, OSError) as error:
        st.warning(f"Could not download exchange rates from Norges Bank ({error}). Try again later.")
        return None
