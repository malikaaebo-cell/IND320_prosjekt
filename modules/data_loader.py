# data_loader.py
# Load and prepare the Magasinstatistikk data for the Streamlit pages.
# Update (part 2): data now comes directly from the NVE Magasinstatistikk API
# instead of the CSV file used in part 1.
import streamlit as st
import pandas as pd
import requests

API_URL = "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOffentligData"

# Cache the result so the API is only called once and not on every Streamlit rerun.
# Note: the API does not support filtering by date in the request itself (confirmed via
# its Swagger specification), so we always fetch the full data set here. Any "download
# interval" selection in the app (see the plot page) filters this already-downloaded data.
@st.cache_data
def load_data():
    response = requests.get(API_URL)
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

    # Convert the date column from text to datetime
    df['date'] = pd.to_datetime(df['date'])

    # Combine area type and number into one label, e.g., 'EL 1', 'VASS 2' and 'NO 0'
    df['area'] = df['area_type'] + ' ' + df['area_number'].astype(str)

    # Sort by area and date so that each area forms one continuous time series
    df = df.sort_values(['area_type', 'area_number', 'date']).reset_index(drop=True)
    return df