import streamlit as st

# Set the page title and use the full width of the browser
st.set_page_config(
    page_title="IND320 Project",
    page_icon="⚡",
    layout="wide",
)

st.title("IND320 - Project work, part 3")
st.write(
    "A dashboard for Norwegian reservoir statistics, weather data and cross-border power "
    "flow data. Reservoir statistics are read directly from the NVE API, weather data from "
    "the open-meteo API, and cross-border power flow data from MongoDB. The area selector "
    "in the sidebar is shared by the reservoir and weather pages."
)

st.divider()

# Overview of the pages, grouped as in the sidebar: reservoir data, weather data, power flow
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    with st.container(border=True):
        st.subheader("📊 Table")
        st.write(
            "Reservoir fill ratio, capacity and more, one row per area, "
            "for a chosen area type (EL, NO or VASS)."
        )

with col2:
    with st.container(border=True):
        st.subheader("📈 Plot")
        st.write(
            "Reservoir data plotted over a chosen period, with one line "
            "per area number within the selected area type."
        )

with col3:
    with st.container(border=True):
        st.subheader("🔍 Magasinanalyse")
        st.write(
            "STL decomposition and spectrogram of the reservoir "
            "degree of filling for the selected area."
        )

with col4:
    with st.container(border=True):
        st.subheader("🌦️ Væranalyse")
        st.write(
            "Outliers in precipitation (SPC) and anomalies in temperature "
            "(LOF) for the selected area and year."
        )

with col5:
    with st.container(border=True):
        st.subheader("🔌 Kraftflyt")
        st.write(
            "Cross-border power flow between Norway (NO2) and Denmark (DK1): "
            "a pie chart per year and a line plot for chosen months."
        )

st.divider()

st.write(" <- Use the menu in the sidebar to open a page.")
st.write("[GitHub repository](https://github.com/malikaaebo-cell/IND320_prosjekt)")

# Show a hint in the sidebar, below the automatic page navigation
st.sidebar.success("Select a page above")