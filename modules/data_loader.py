import streamlit as st
import pandas as pd

@st.cache_data # Cacher resultatet slik at CSV-filen kun leses én gang, ikke ved hver Streamlit-rerun
def load_data(path="project_data/reservoirs.csv"):
    """Leser magasindata fra CSV, omdøper kolonner til engelsk,
    og sorterer kronologisk. Cachet for at det skal gå raskere."""
    df = pd.read_csv(path)

# Samme oversettelse av kolonnenavn som i notebooken (se rename-cellen der)

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

# Konverter til faktisk datotype (ikke tekst) og sorter kronologisk
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df