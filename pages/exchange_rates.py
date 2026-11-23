# Data overview: EUR and USD exchange rates from Norges Bank's API (part 4). The same rates
# can be used as exogenous variables on the forecast page.
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.theme import page_header, show
from modules.currency import exchange_rates_or_none

page_header("Exchange rates", "Data overview",
            "Daily exchange rates from Norges Bank (NOK per unit of foreign currency). "
            "Rates are only published on Norwegian business days.")

today = pd.Timestamp.today().normalize()
col1, col2 = st.columns([1, 2])
period = col1.date_input("Period", value=(today - pd.DateOffset(years=3), today),
                         min_value=pd.Timestamp('2000-01-01'), max_value=today)
resolution = col2.radio("Resolution", ["Daily", "Weekly mean", "Monthly mean"], horizontal=True)

# The date input returns one date while the user is still choosing the end of the period
if not isinstance(period, tuple) or len(period) != 2:
    st.info("Choose both a start and an end date.")
    st.stop()

rates = exchange_rates_or_none(f"{period[0]:%Y-%m-%d}", f"{period[1]:%Y-%m-%d}")
if rates is None or rates.empty:
    st.stop()
if resolution != "Daily":
    rates = rates.resample('W-SUN' if resolution == "Weekly mean" else 'MS').mean()

# Latest values with the change over the period
c1, c2 = st.columns(2)
for col, currency in zip([c1, c2], ['EUR', 'USD']):
    if currency in rates:
        s = rates[currency].dropna()
        col.metric(f"{currency}/NOK, {s.index[-1]:%d %b %Y}", f"{s.iloc[-1]:.3f}",
                   f"{s.iloc[-1] - s.iloc[0]:+.3f} over the period")

fig = go.Figure()
for currency, color in [('EUR', '#2A9D8F'), ('USD', '#2A6F97')]:
    if currency in rates:
        fig.add_scatter(x=rates.index, y=rates[currency], mode='lines', name=currency,
                        line=dict(color=color, width=1.5))
fig.update_layout(title=f"Exchange rates ({resolution.lower()})", yaxis_title="NOK per unit",
                  height=460, hovermode='x unified')
show(fig)

with st.expander("Data table"):
    st.dataframe(rates.round(4))
