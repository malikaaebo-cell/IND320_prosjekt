# data_loader.py
# Load and prepare the Magasinstatistikk data for the Streamlit pages.
# Update (part 2): data now comes directly from the NVE Magasinstatistikk API
# instead of the CSV file used in part 1.
# Update (part 4): errors from the API are caught, and load_data_or_stop() shows a useful
# message in the app instead of a crash (bonus: error handling).
import pandas as pd
import requests
import streamlit as st

API_URL = "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOffentligData"


# Cache the result so the API is only called once and not on every Streamlit rerun.
# The data is published once a week, so the cache is refreshed every 6 hours (ttl).
# Note: the API does not support filtering by date in the request itself, so we always
# fetch the full data set here and filter it in the app.
@st.cache_data(ttl=6 * 3600, show_spinner="Downloading Magasinstatistikk from NVE ...")
def load_data():
    response = requests.get(API_URL, timeout=60)
    response.raise_for_status()
    df = pd.DataFrame(response.json())

    # Rename the Norwegian headers to English (same names as in the notebook and the old CSV)
    df = df.rename(columns={
        'dato_Id': 'date',
        'omrType': 'area_type',
        'omrnr': 'area_number',
        'iso_aar': 'iso_year',
        'iso_uke': 'iso_week',
        'fyllingsgrad': 'fill_ratio',
        'kapasitet_TWh': 'capacity_twh',
        'fylling_TWh': 'fill_twh',
        'neste_Publiseringsdato': 'next_publication_date',
        'fyllingsgrad_forrige_uke': 'fill_ratio_previous_week',
        'endring_fyllingsgrad': 'fill_ratio_change'
    })

    # Convert the date column from text to datetime (the date is the Sunday ending the ISO week)
    df['date'] = pd.to_datetime(df['date'])

    # Combine area type and number into one label, e.g., 'EL 1', 'VASS 2' and 'NO 0'
    df['area'] = df['area_type'] + ' ' + df['area_number'].astype(str)

    # Sort by area and date so that each area forms one continuous time series
    df = df.sort_values(['area_type', 'area_number', 'date']).reset_index(drop=True)
    return df


def load_data_or_stop():
    """Load the data, or show an error message and stop the page if NVE's API is unavailable."""
    try:
        return load_data()
    except requests.RequestException as error:
        st.error("Could not download Magasinstatistikk from NVE's API. The service may be "
                 f"temporarily unavailable; please try again later.\n\nDetails: {error}")
        st.stop()
