# Page with outlier and anomaly analyses of the weather data (part 3):
# SPC on the precipitation in the first tab and LOF on the temperature in the second tab.
# The weather data is downloaded from open-meteo for the area selected in the sidebar,
# i.e. the same selector as for the Magasinstatistikk data.
import streamlit as st
import matplotlib.pyplot as plt
from modules.data_loader import load_data
from modules.area_selector import select_area
from modules.weather import get_weather
from modules.analysis import spc_outliers, lof_anomalies

st.set_page_config(
    page_title="Væranalyse",
    layout="wide",
)

st.title("Weather analysis")
st.write("Outliers in precipitation and anomalies in temperature, from hourly ERA5 "
         "reanalysis data (open-meteo) for the area selected in the sidebar.")

# The area comes from the shared selector in the sidebar (the same as for the reservoir data)
df = load_data()
area_type, area_number = select_area(df)
area = f"{area_type} {area_number}"

# The year is only used on this page, so it is a local selector
year = st.sidebar.selectbox("Weather year", list(range(2025, 1999, -1)), index=1)

# Download (or read the cached) weather data; the download is hidden behind a spinner
try:
    weather, source = get_weather(area, year)
except Exception as error:
    st.error(f"Could not download the weather data: {error}")
    st.stop()

st.caption(f"Area: **{area}**, year **{year}**, {len(weather)} hours. "
           f"Average over {source}.")

tab_spc, tab_lof = st.tabs(["Outliers in precipitation (SPC)", "Anomalies in temperature (LOF)"])

with tab_spc:
    st.write("The precipitation is high-pass filtered with the Discrete Cosine Transform. "
             "Robust statistics (median and MAD) of the filtered values give the SPC limits, "
             "and values outside the limits are marked in red.")

    # Parameters: DCT frequency cut-off and number of robust standard deviations
    col1, col2 = st.columns(2)
    cutoff = col1.slider("DCT frequency cut-off", min_value=5, max_value=200, value=25, step=5,
                         help="Number of the lowest frequencies removed (25 ≈ variations slower than a month)")
    n_std = col2.slider("Number of standard deviations", min_value=1.0, max_value=6.0, value=3.0, step=0.5)

    fig, summary, outliers = spc_outliers(weather['precipitation'], cutoff=cutoff, n_std=n_std)
    st.pyplot(fig)
    plt.close(fig)

    # Summary as metrics, and the largest outliers as a table
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Outliers", summary['number of outliers'])
    col2.metric("Share of hours", f"{summary['share of outliers (%)']} %")
    col3.metric("Above upper limit", summary['above upper limit'])
    col4.metric("Below lower limit", summary['below lower limit'])
    st.write("The 10 largest outliers (mm per hour):")
    st.dataframe(outliers.sort_values(ascending=False).head(10))

with tab_lof:
    st.write("Local Outlier Factor compares each hour with the hours close in time. "
             "Hours where the temperature differs from its neighbours are marked in red.")

    # Parameters: proportion of anomalies (default 1 %) and number of neighbours
    col1, col2 = st.columns(2)
    proportion = col1.slider("Proportion of anomalies (%)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    n_neighbors = col2.slider("Number of neighbours", min_value=5, max_value=100, value=20, step=5)

    fig, summary, anomalies = lof_anomalies(weather['temperature_2m'],
                                            contamination=proportion / 100, n_neighbors=n_neighbors)
    st.pyplot(fig)
    plt.close(fig)

    # Summary as metrics, and the number of anomalies per month as a bar chart
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Anomalies", summary['number of anomalies'])
    col2.metric("Share of hours", f"{summary['share of anomalies (%)']} %")
    col3.metric("Lowest anomaly", f"{summary['lowest anomaly']} °C")
    col4.metric("Highest anomaly", f"{summary['highest anomaly']} °C")
    st.write("Number of anomalies per month:")
    # Count anomalies per month, including months with none, labelled e.g. '01 Jan'
    # (the number first keeps the months in the right order in the chart)
    per_month = anomalies.groupby(anomalies.index.month).size().reindex(range(1, 13), fill_value=0)
    per_month.index = [f"{m:02d} {name}" for m, name in zip(range(1, 13),
                       ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])]
    st.bar_chart(per_month.rename('anomalies'))

with st.expander("About the weather data"):
    st.write("""
        The weather data is hourly ERA5 reanalysis data from open-meteo's historical
        weather API. In the notebook, 1000 random locations were sampled inside each area
        from NVE's shapefiles, and the data was averaged over all of them (rounded to the
        ERA5 0.25° grid). Downloading all of them takes about an hour because of
        open-meteo's free API limits, so the app uses a random sample of 10 grid cells per
        area and year. For NO3 (EL 3) in 2024, the complete download from the notebook is
        used. Each area and year is only downloaded once while the app is running.
    """)
