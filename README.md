# IND320 – Data to Decision: project work

Streamlit app and Jupyter notebooks for the project work in IND320 (NMBU, autumn 2026).
The app combines Norwegian reservoir statistics, weather data and cross-border power flow data.

- **Streamlit app:** https://malikaaebo-cell-ind320-prosjekt-main-rqsvdg.streamlit.app
- **Author:** Malika Äbo

## Data sources

| Data | Source | Used for |
|---|---|---|
| Reservoir statistics (fill ratio, capacity) | NVE Magasinstatistikk API | Table, plot, STL and spectrogram |
| Hourly weather (ERA5 reanalysis) | open-meteo historical weather API | Outliers (SPC) and anomalies (LOF) |
| Electricity areas and NVE regions (shapefiles) | NVE Atlas | Random locations per area for the weather download |
| Cross-border power flow NO2–DK1 | ENTSO-E Transparency Platform (via Cassandra/Spark → MongoDB) | Power flow page |

## The app

| Page | Content |
|---|---|
| **main** | Overview of the app |
| **tabell** | One row per area with small line charts, with a month picker |
| **plot** | Reservoir data over a chosen period, one line per area |
| **magasinanalyse** | STL decomposition and spectrogram of the reservoir fill ratio |
| **vaeranalyse** | Outliers in precipitation (SPC with DCT) and anomalies in temperature (LOF) |
| **kraftflyt** | Power flow NO2–DK1: pie chart per year and line plot for chosen months |

The area selector in the sidebar is shared by the reservoir and weather pages, and the weather data that is downloaded depends on the selected area.

## Repository structure

```
main.py                 Front page of the Streamlit app
pages/                  The app's pages
modules/
  data_loader.py        Downloads and prepares the Magasinstatistikk data
  area_selector.py      Shared area selector in the sidebar
  weather.py            Downloads ERA5 weather data from open-meteo
  analysis.py           SPC, LOF, STL and spectrogram functions (same as in the notebook)
notebooks/              Project notebooks for part 1–3
project_data/           Shapefiles, random locations and the downloaded NO3 2024 weather data
media/                  Screencasts
requirements.txt        Python packages
```

## Running locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run main.py
```

The power flow page reads from MongoDB. Locally, the credentials are read from `No_sync/MongoDB` (not in the repository); on Streamlit Cloud they are set as secrets.

## Project parts

1. **Part 1:** Streamlit app with table and plot of reservoir data from CSV.
2. **Part 2:** NVE API, ENTSO-E power flow data via Cassandra/Spark to MongoDB, power flow page.
3. **Part 3:** Shapefiles from NVE Atlas, ERA5 weather data from open-meteo, outlier and anomaly detection (SPC, LOF), STL and spectrogram, two new analysis pages in the app.