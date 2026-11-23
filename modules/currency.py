# currency.py
# Daily EUR and USD exchange rates (NOK per unit) from Norges Bank's open SDMX API (part 4).
# Same function as download_exchange_rates() in the part 4 notebook, with caching and
# readable errors for the app.
import pandas as pd
import requests
import streamlit as st

NB_URL = "https://data.norges-bank.no/api/data/EXR/B.{currencies}.NOK.SP"


# Cached for 6 hours: the rates are published once per business day
@st.cache_data(ttl=6 * 3600, show_spinner="Downloading exchange rates from Norges Bank ...")
def download_exchange_rates(start, end, currencies=('EUR', 'USD')):
    """
    Download daily exchange rates (NOK per unit of foreign currency) from Norges Bank.

    start, end : first and last date, 'YYYY-MM-DD'
    currencies : base currencies, e.g. ('EUR', 'USD')
    Returns a DataFrame with one column per currency and the date as index.
    The series key B.EUR+USD.NOK.SP means business days, EUR and USD against NOK, spot rates.
    """
    url = NB_URL.format(currencies='+'.join(currencies))
    params = {'format': 'sdmx-json', 'startPeriod': start, 'endPeriod': end, 'locale': 'en'}
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()['data']

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

    rates = pd.DataFrame(columns).sort_index()
    rates.index.name = 'date'
    return rates


def exchange_rates_or_none(start, end):
    """Exchange rates, or None with a warning in the app if Norges Bank's API is unavailable."""
    try:
        return download_exchange_rates(start, end)
    except (requests.RequestException, KeyError, ValueError) as error:
        st.warning(f"Could not download exchange rates from Norges Bank ({error}).")
        return None
