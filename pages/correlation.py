# Exploratory: sliding window correlation between a weather property and the reservoir data
# (part 4), the Streamlit equivalent of the Sliding Window Correlation in the course material.
# Both series are weekly (ISO weeks). The weather series can be shifted by a lag, so that, e.g.,
# the precipitation some weeks earlier is compared with this week's change in filling, and the
# correlation is computed in a window that slides over the period.
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from modules.theme import page_header, show, PRIMARY, GROUPS
from modules.data_loader import load_data_or_stop
from modules.area_selector import select_area
from modules.weather import DAILY_VARS, DAILY_LABELS, WeatherError
from modules.weekly_data import weekly_data

page_header("Weather vs. reservoir filling", "Exploratory & anomalies",
            "Sliding window correlation between a weekly weather property and the reservoir data "
            "for the area selected in the sidebar or on the map. A positive lag compares the "
            "weather that many weeks earlier with the reservoir data.")

df = load_data_or_stop()
area_type, area_number = select_area(df)
area = f"{area_type} {area_number}"

try:
    data = weekly_data(area, with_weather=True)
except WeatherError as error:
    st.error(f"Could not download the weather data. {error}")
    st.stop()

# ---- Controls
reservoir_vars = {'fill_change': 'Weekly change in degree of filling (pp)',
                  'fill': 'Degree of filling (%)'}
col1, col2 = st.columns(2)
weather_var = col1.selectbox("Weather property", DAILY_VARS, format_func=DAILY_LABELS.get,
                             index=DAILY_VARS.index('precipitation_sum'))
reservoir_var = col2.selectbox("Magasinstatistikk variable", list(reservoir_vars),
                               format_func=reservoir_vars.get,
                               help="The weekly change reacts directly to inflow; the level mostly "
                                    "shows the seasonal cycle.")
col3, col4, col5 = st.columns(3)
lag = col3.slider("Lag (weeks)", min_value=-12, max_value=26, value=0,
                  help="Positive: the weather this many weeks earlier is compared with the reservoir data.")
window = col4.slider("Window length (weeks)", min_value=8, max_value=156, value=52, step=4)
years = sorted(data.index.year.unique())
first, last = col5.select_slider("Period (years)", options=years, value=(max(years[0], years[-1] - 9), years[-1]))

# ---- Correlation: the weather series shifted by the lag, then a rolling (centred) correlation
period = data[(data.index.year >= first) & (data.index.year <= last)]
reservoir = period[reservoir_var]
weather = period[weather_var].shift(lag)          # positive lag: earlier weather
valid = reservoir.notna() & weather.notna()
if valid.sum() < window:
    st.warning("Too few weeks with data for this window length and period.")
    st.stop()
rolling = reservoir.rolling(window, center=True, min_periods=window // 2).corr(weather)
overall = reservoir[valid].corr(weather[valid])

c1, c2, c3 = st.columns(3)
c1.metric("Correlation over the whole period", f"{overall:.2f}")
c2.metric("Highest window correlation", f"{rolling.max():.2f}")
c3.metric("Lowest window correlation", f"{rolling.min():.2f}")

fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                    subplot_titles=[reservoir_vars[reservoir_var],
                                    f"{DAILY_LABELS[weather_var]}, shifted {lag} weeks",
                                    f"Correlation in a {window}-week sliding window"])
fig.add_scatter(x=reservoir.index, y=reservoir, row=1, col=1, mode='lines', showlegend=False,
                line=dict(color=PRIMARY, width=1.2))
fig.add_scatter(x=weather.index, y=weather, row=2, col=1, mode='lines', showlegend=False,
                line=dict(color='#2A9D8F', width=1.2))
fig.add_scatter(x=rolling.index, y=rolling, row=3, col=1, mode='lines', showlegend=False,
                line=dict(color=GROUPS['Exploratory & anomalies'], width=2),
                fill='tozeroy', fillcolor='rgba(233,160,59,0.15)')
fig.add_hline(y=0, row=3, col=1, line=dict(color='#555555', width=1))
fig.update_yaxes(range=[-1, 1], row=3, col=1, title_text="r")
fig.update_layout(height=720, hovermode='x unified', margin=dict(t=60))
show(fig)

# ---- Correlation as a function of the lag (whole period), to help choose the lag
lags = np.arange(-12, 27)
by_lag = [reservoir.corr(period[weather_var].shift(k)) for k in lags]
bar = go.Figure(go.Bar(x=lags, y=by_lag, marker_color=[GROUPS['Predictive'] if k == lag else '#B8C2CA' for k in lags],
                       hovertemplate='Lag %{x} weeks: r = %{y:.2f}<extra></extra>'))
bar.update_layout(title="Correlation over the whole period for each lag (selected lag highlighted)",
                  xaxis_title="Lag (weeks)", yaxis_title="r", height=320, yaxis_range=[-1, 1])
show(bar)

with st.expander("How to read the plots"):
    st.write("""
        The top panels show the two weekly series; the weather series is shifted by the lag.
        The bottom panel shows the Pearson correlation inside a window that slides over the
        period (centred on each week). Long windows give stable values that mostly reflect the
        seasonal cycle; short windows show how the relation changes between seasons and years.
        Weeks where the correlation changes sign or strength can indicate when a weather
        property is useful as an input to the forecast.
    """)
