# main.py
# Entry point of the Streamlit app. Run with:  streamlit run main.py
#
# Update (part 4): the pages are grouped in the menu with st.navigation, following the sketch
# in the part 4 notebook:
#   Home                     - map of the areas, where the area and week are selected
#   Data overview            - the data from the four sources, with little processing
#   Exploratory & anomalies  - analyses of the reservoir and weather data
#   Predictive               - forecast of the reservoir filling
# Each group has its own colour (see modules/theme.py). Selections that are shared between the
# pages (area, week) are stored in st.session_state; the others are made locally on each page.
import streamlit as st

st.set_page_config(
    page_title="IND320 – Reservoirs, weather and power",
    page_icon="⚡",
    layout="wide",
)

pages = {
    "Home": [
        st.Page("pages/home_map.py", title="Map and area selection", icon=":material/map:", default=True),
    ],
    "Data overview": [
        st.Page("pages/reservoir_data.py", title="Reservoir data", icon=":material/table_chart:"),
        st.Page("pages/power_flow.py", title="Power flow NO2–DK1", icon=":material/bolt:"),
        st.Page("pages/exchange_rates.py", title="Exchange rates", icon=":material/currency_exchange:"),
    ],
    "Exploratory & anomalies": [
        st.Page("pages/reservoir_analysis.py", title="Reservoir analysis", icon=":material/water:"),
        st.Page("pages/weather_analysis.py", title="Weather analysis", icon=":material/thermostat:"),
        st.Page("pages/correlation.py", title="Weather vs. filling", icon=":material/query_stats:"),
    ],
    "Predictive": [
        st.Page("pages/forecast.py", title="Forecast of filling", icon=":material/trending_up:"),
    ],
}

# The menu shows one header per group
navigation = st.navigation(pages)

st.sidebar.caption("IND320 project work · Malika Äbo · "
                   "[GitHub](https://github.com/malikaaebo-cell/IND320_prosjekt)")

navigation.run()
