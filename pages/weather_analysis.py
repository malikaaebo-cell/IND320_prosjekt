# Anomalies: outlier and anomaly analyses of the hourly weather data (part 3).
# Update (part 4): Plotly figures, and both methods work for any weather property, selected on
# the page (temperature by default). SPC is done on the seasonally adjusted (DCT high-pass
# filtered) values, SATV. The area comes from the shared selector (or the map), and the default
# year is the year of the week chosen on the map.
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.theme import page_header, show
from modules.data_loader import load_data_or_stop
from modules.area_selector import select_area, selected_date
from modules.weather import get_weather, HOURLY_VARS, HOURLY_LABELS, WeatherError
from modules.analysis import spc_outliers, lof_anomalies

page_header("Weather analysis", "Exploratory & anomalies",
            "Outliers (SPC on seasonally adjusted values) and anomalies (LOF) in hourly ERA5 "
            "reanalysis data from open-meteo for the area selected in the sidebar or on the map.")

df = load_data_or_stop()
area_type, area_number = select_area(df)
area = f"{area_type} {area_number}"

# The year is only used on this page, so it is a local selector (default: the map's year).
# The last complete year is the latest available, since the year is downloaded as a whole.
last_year = pd.Timestamp.today().year - 1
years = list(range(last_year, 1999, -1))
default_year = min(selected_date(df).year, last_year)
year = st.sidebar.selectbox("Weather year", years, index=years.index(default_year))

try:
    weather, source = get_weather(area, year)
except WeatherError as error:
    st.error(f"Could not download the weather data. {error}")
    st.stop()

missing = int(weather.isna().sum().sum())
st.caption(f"Area: **{area}**, year **{year}**, {len(weather)} hours, average over {source}."
           + (f" {missing} missing values are left out of the analyses." if missing else ""))

tab_spc, tab_lof = st.tabs(["Outliers: SPC on seasonally adjusted values (SATV)",
                            "Anomalies: Local Outlier Factor (LOF)"])

with tab_spc:
    st.write("The series is high-pass filtered with the Discrete Cosine Transform, which removes "
             "the slow seasonal variation (SATV). Robust statistics (median and MAD) of the "
             "filtered values give the SPC limits, and values outside the limits are marked.")
    col1, col2, col3 = st.columns(3)
    spc_var = col1.selectbox("Weather property", HOURLY_VARS, format_func=HOURLY_LABELS.get,
                             index=HOURLY_VARS.index('temperature_2m'), key='spc_var')
    cutoff = col2.slider("DCT frequency cut-off", min_value=5, max_value=200, value=25, step=5,
                         help="Number of the lowest frequencies removed (25 ≈ variations slower than a month)")
    n_std = col3.slider("Number of standard deviations", min_value=1.0, max_value=6.0, value=3.0, step=0.5)

    fig, summary, outliers = spc_outliers(weather[spc_var], cutoff=cutoff, n_std=n_std,
                                          label=HOURLY_LABELS[spc_var])
    show(fig)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Outliers", summary['number of outliers'])
    c2.metric("Share of hours", f"{summary['share of outliers (%)']} %")
    c3.metric("Above upper limit", summary['above upper limit'])
    c4.metric("Below lower limit", summary['below lower limit'])
    with st.expander("The 10 largest deviations"):
        st.dataframe(outliers.sort_values(key=abs, ascending=False).head(10).rename(HOURLY_LABELS[spc_var]))

with tab_lof:
    st.write("Local Outlier Factor compares each hour with the hours close in time. "
             "Hours where the value differs from its neighbours are marked.")
    col1, col2, col3 = st.columns(3)
    lof_var = col1.selectbox("Weather property", HOURLY_VARS, format_func=HOURLY_LABELS.get,
                             index=HOURLY_VARS.index('temperature_2m'), key='lof_var')
    proportion = col2.slider("Proportion of anomalies (%)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    n_neighbors = col3.slider("Number of neighbours", min_value=5, max_value=100, value=20, step=5)

    with st.spinner("Fitting LOF ..."):
        fig, summary, anomalies = lof_anomalies(weather[lof_var], contamination=proportion / 100,
                                                n_neighbors=n_neighbors, label=HOURLY_LABELS[lof_var])
    show(fig)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Anomalies", summary['number of anomalies'])
    c2.metric("Share of hours", f"{summary['share of anomalies (%)']} %")
    c3.metric("Lowest anomaly", summary['lowest anomaly'])
    c4.metric("Highest anomaly", summary['highest anomaly'])

    # Number of anomalies per month, including months with none
    per_month = anomalies.groupby(anomalies.index.month).size().reindex(range(1, 13), fill_value=0)
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    bar = go.Figure(go.Bar(x=month_names, y=per_month.values, marker_color='#E9A03B'))
    bar.update_layout(title="Number of anomalies per month", height=300, yaxis_title="Anomalies")
    show(bar)

with st.expander("About the weather data"):
    st.write("""
        Hourly ERA5 reanalysis data from open-meteo's historical weather API. In the part 3
        notebook, 1000 random locations were sampled inside each area from NVE's shapefiles and
        rounded to the ERA5 0.25° grid. Downloading all of them takes about an hour because of
        open-meteo's free API limits, so the app uses a random sample of 10 grid cells per area
        and year (for NO3 in 2024 the complete notebook download is used). Each area and year is
        only downloaded once while the app is running (cached).
    """)
