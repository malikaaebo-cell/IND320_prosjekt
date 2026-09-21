# data_loader.py
# Load and prepare the reservoir data (reservoirs.csv) for the Streamlit pages
import streamlit as st
import pandas as pd

# Cache the result so the CSV is only read once and not on every Streamlit rerun
@st.cache_data
def load_data(path="project_data/reservoirs.csv"):
    # Read the CSV file
    df = pd.read_csv(path)

    # Rename the Norwegian headers to English (same names as in the notebook)
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