# Page with analyses of the reservoir degree of filling (part 3):
# STL decomposition in the first tab and a spectrogram in the second tab.
# The area is chosen with the shared area selector in the sidebar.
import streamlit as st
import matplotlib.pyplot as plt
from modules.data_loader import load_data
from modules.area_selector import select_area
from modules.analysis import stl_decomposition, spectrogram

st.set_page_config(
    page_title="Magasinanalyse",
    layout="wide",
)

st.title("Reservoir analysis")
st.write("Analyses of the weekly degree of filling (fill ratio) from Magasinstatistikk "
         "for the area selected in the sidebar.")

# Reservoir data (cached) and the area chosen in the sidebar
df = load_data()
area_type, area_number = select_area(df)
area = f"{area_type} {area_number}"

# Weekly degree of filling for the selected area, with the date as index
series = df[df['area'] == area].set_index('date')['fill_ratio']
st.caption(f"Area: **{area}**, {len(series)} weeks from {series.index.min():%Y-%m-%d} "
           f"to {series.index.max():%Y-%m-%d}")

tab_stl, tab_spectrogram = st.tabs(["STL decomposition", "Spectrogram"])

with tab_stl:
    st.write("Seasonal-Trend decomposition using LOESS splits the series into a trend, "
             "a yearly seasonal component and a residual. The period is 52 weeks.")

    # Parameters for the STL; the smoothers must be odd numbers, and the trend smoother
    # must be longer than the period (52), so the sliders use odd steps from an odd start
    col1, col2, col3 = st.columns(3)
    seasonal = col1.slider("Seasonal smoother", min_value=7, max_value=51, value=13, step=2,
                           help="Higher value = the seasonal pattern changes less from year to year")
    trend = col2.slider("Trend smoother", min_value=53, max_value=261, value=105, step=2,
                        help="Higher value = smoother trend")
    robust = col3.checkbox("Robust", value=False,
                           help="Gives less weight to outliers when fitting")

    fig = stl_decomposition(series, seasonal=seasonal, trend=trend, robust=robust)
    st.pyplot(fig)
    plt.close(fig)

with tab_spectrogram:
    st.write("The spectrogram shows how the frequency content of the degree of filling "
             "changes over time. The band at 1 cycle per year is the yearly cycle.")

    # Parameters for the spectrogram; the overlap must be smaller than the window length
    col1, col2 = st.columns(2)
    window_length = col1.slider("Window length (weeks)", min_value=26, max_value=260, value=104, step=2)
    overlap = col2.slider("Window overlap (weeks)", min_value=0, max_value=window_length - 2,
                          value=min(78, window_length - 2), step=2)

    fig = spectrogram(series, window_length=window_length, overlap=overlap)
    st.pyplot(fig)
    plt.close(fig)
