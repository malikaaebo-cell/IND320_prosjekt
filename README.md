# IND320 – Data to Decision: project work

Streamlit app and Jupyter notebooks for the project work in IND320 (NMBU, autumn 2026).
The app combines Norwegian reservoir statistics, weather data, cross-border power flow data and
exchange rates, with exploratory analyses and forecasts of the reservoir filling.

- **Streamlit app:** https://malikaaebo-cell-ind320-prosjekt-main-rqsvdg.streamlit.app
- **Author:** Malika Äbo

## Data sources

| Data | Source | Used for |
|---|---|---|
| Reservoir statistics (fill ratio, capacity) | NVE Magasinstatistikk API | Map, reservoir data, STL, spectrogram, correlation and forecast |
| Weather (ERA5 reanalysis, hourly and daily) | open-meteo historical weather API | Map, outliers (SPC) and anomalies (LOF), correlation and exogenous variables in the forecast |
| Exchange rates EUR and USD | Norges Bank open data API (SDMX) | Exchange rates page, optional exogenous variables in the forecast |
| Cross-border power flow NO2–DK1 | ENTSO-E Transparency Platform (via Cassandra/Spark → MongoDB) | Power flow page |
| Electricity areas and NVE regions (shapefiles) | NVE Atlas | GeoJSON for the map, random locations per area for the weather download |

## The app

The menu is grouped with `st.navigation`, and each group has its own colour.

| Group | Page | Content |
|---|---|---|
| **Home** | Map and area selection | GeoJSON map of the EL, VASS or NO areas, coloured by degree of filling or a weather property for the chosen week. A click selects the area for all pages |
| **Data overview** | Reservoir data | Plot of the reservoir data and the table with small line charts (LineChartColumn) |
| | Power flow NO2–DK1 | Pie chart per year and line plot for chosen months, read from MongoDB |
| | Exchange rates | EUR and USD against NOK from Norges Bank |
| **Exploratory & anomalies** | Reservoir analysis | STL decomposition and spectrogram of the degree of filling |
| | Weather analysis | Outliers (SPC on DCT-filtered values, SATV) and anomalies (LOF) for a chosen weather property |
| | Weather vs. filling | Sliding window correlation between a weather property and the reservoir data, with lag and window length |
| **Predictive** | Forecast of filling | SARIMAX (River's SNARIMAX) with selectable parameters, training period, horizon and exogenous variables, 90 % interval from quantile models and Plotly animation |

The area and the week are shared between the pages through `st.session_state`. Downloads and
analyses are cached, time-consuming calls show a spinner or progress bar, and missing connections
to the APIs or the database give a readable message instead of an error.

## Repository structure

```
main.py                 Entry point: grouped menu with st.navigation
pages/                  The app's pages
modules/
  theme.py              Colours, Plotly template and page header
  data_loader.py        Downloads and prepares the Magasinstatistikk data
  area_selector.py      Shared area selector and session state helpers
  weather.py            ERA5 weather data from open-meteo (hourly, and per week for the map)
  weekly_data.py        Weekly data set (filling, daily weather, exchange rates) on ISO weeks
  currency.py           Exchange rates from Norges Bank
  forecast.py           SARIMAX forecast with River (same function as in the notebook)
  analysis.py           SPC, LOF, STL and spectrogram functions
  geo.py                Reads the GeoJSON of the areas
scripts/
  make_geojson.py       Converts the NVE shapefiles to project_data/areas.geojson
  download_weather.py   Downloads the daily weather for all areas in advance
notebooks/              Project notebooks for part 1–4
project_data/           Shapefiles, GeoJSON, random locations and downloaded weather data
media/                  Screencasts and the app sketch
requirements.txt        Python packages
```

## Running locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run main.py
```

The power flow page reads from MongoDB. Locally, the credentials are read from `No_sync/MongoDB`
(not in the repository); on Streamlit Cloud they are set as secrets.

## Project parts

1. **Part 1:** Streamlit app with table and plot of reservoir data from CSV.
2. **Part 2:** NVE API, ENTSO-E power flow data via Cassandra/Spark to MongoDB, power flow page.
3. **Part 3:** Shapefiles from NVE Atlas, ERA5 weather data from open-meteo, outlier and anomaly detection (SPC, LOF), STL and spectrogram, two new analysis pages in the app.
4. **Part 4:** Exchange rates from Norges Bank, time zones in the four sources, SARIMAX forecasts with River, new app structure with grouped menu and Plotly, interactive map with GeoJSON, sliding window correlation and forecast page.
