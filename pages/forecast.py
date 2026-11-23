# Predictive: forecast of the reservoir degree of filling with SARIMAX in River (part 4).
# All model parameters, the training period, the horizon and the exogenous variables can be
# chosen. The defaults are the best settings from the tests in the part 4 notebook. The end of
# the training data is synced with the week chosen on the map (session state 'map_date').
# The forecast is dynamic (each step builds on the earlier forecasts) and is shown with a
# Plotly animation, with a 90 % interval from quantile models (bonus).
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.theme import page_header, show, MUTED, TEXT, GROUPS
from modules.data_loader import load_data_or_stop
from modules.area_selector import select_area
from modules.weather import DAILY_VARS, DAILY_LABELS, WeatherError
from modules.weekly_data import weekly_data
from modules.forecast import forecast_filling, DEFAULTS

COLOR = GROUPS['Predictive']

page_header("Forecast of reservoir filling", "Predictive",
            "Dynamic forecast of the weekly degree of filling with SARIMAX (River's SNARIMAX) for "
            "the area selected in the sidebar or on the map. The defaults are the best settings "
            "from the tests in the notebook.")

df = load_data_or_stop()
area_type, area_number = select_area(df)
area = f"{area_type} {area_number}"

try:
    with st.spinner("Preparing weekly data ..."):
        data = weekly_data(area, with_weather=True, with_currency=True)
except WeatherError as error:
    st.error(f"Could not download the weather data for the exogenous variables. {error}")
    st.stop()

# ---- Training period and horizon (the end is synced with the map)
dates = list(data.index)
map_date = pd.Timestamp(st.session_state.get('map_date', dates[-1]))
end_default = max(d for d in dates if d <= map_date) if map_date >= dates[0] else dates[-1]

st.subheader("Training data and horizon")
col1, col2, col3 = st.columns([2, 1, 1])
train_end = col1.select_slider(
    "Last week of training data", options=dates, value=end_default,
    format_func=lambda d: f"{d:%d %b %Y}",
    help="Synced with the week on the map. Choose a week in the past to compare the forecast "
         "with what actually happened.")
st.session_state['map_date'] = train_end
history_years = col2.slider("Years of training data", 3, 15, DEFAULTS['history_years'])
horizon = col3.slider("Horizon (weeks)", 4, 52, DEFAULTS['horizon'])

# ---- Model parameters and exogenous variables, in a form so the model only runs on request
exog_options = [c for c in DAILY_VARS + ['EUR', 'USD'] if c in data.columns]
labels = {**DAILY_LABELS, 'EUR': 'EUR/NOK', 'USD': 'USD/NOK'}
with st.form("model"):
    st.subheader("Model")
    c = st.columns(7)
    p = c[0].number_input("p (AR)", 0, 8, DEFAULTS['p'])
    d = c[1].number_input("d", 0, 2, DEFAULTS['d'])
    q = c[2].number_input("q (MA)", 0, 8, DEFAULTS['q'])
    sp = c[3].number_input("sp (seasonal AR)", 0, 3, DEFAULTS['sp'])
    sd = c[4].number_input("sd (seasonal diff.)", 0, 1, DEFAULTS['sd'])
    sq = c[5].number_input("sq (seasonal MA)", 0, 3, DEFAULTS['sq'])
    lr = c[6].select_slider("Learning rate", [0.001, 0.002, 0.005, 0.01, 0.02, 0.05], DEFAULTS['lr'])

    col1, col2, col3 = st.columns([2, 1.2, 1])
    exog = col1.multiselect("Exogenous variables", exog_options, default=list(DEFAULTS['exog']),
                            format_func=labels.get)
    future_exog = col2.radio(
        "Future values of the exogenous variables",
        ['climatology', 'actual'],
        format_func={'climatology': 'Mean of the same week (realistic)',
                     'actual': 'Measured values (only past periods)'}.get,
    )
    interval = col3.checkbox("90 % interval (quantile loss)", value=DEFAULTS['interval'])
    st.caption("Season length 52 weeks. Seasonal differencing (sd = 1) was essential in the tests.")
    submitted = st.form_submit_button("Run forecast", type="primary")

# Run the first time the page is opened and whenever the form is submitted
settings = dict(p=p, d=d, q=q, sp=sp, sd=sd, sq=sq, lr=lr, history_years=history_years,
                horizon=horizon, exog=tuple(exog), future_exog=future_exog,
                quantiles=(0.05, 0.95) if interval else None,
                forecast_start=train_end + pd.Timedelta(days=1))


@st.cache_data(show_spinner=False)
def run(area, data, **settings):
    """Cached, so the same forecast is not recomputed when the page is redrawn."""
    return forecast_filling(data, **settings)


try:
    with st.spinner("Training the models and forecasting ..."):
        result, train, mae, runtime = run(area, data, **settings)
except ValueError as error:
    st.error(f"The forecast could not be made: {error}")
    st.stop()

# ---- Results
st.subheader(f"Forecast for {area}")
c1, c2, c3 = st.columns(3)
c1.metric("Training data", f"{train.index[0]:%b %Y} – {train.index[-1]:%b %Y}", f"{len(train)} weeks",
          delta_color="off")
c2.metric("Mean absolute error", f"{mae:.1f} pp" if mae is not None else "–",
          "compared with the measured filling" if mae is not None else "future period", delta_color="off")
c3.metric("Run time", f"{runtime:.1f} s")


def animated_forecast(result, history):
    """Plotly animation: the forecast and its interval grow one week at a time."""
    fig = go.Figure()
    fig.add_scatter(x=history.index, y=history, name='History', mode='lines', line=dict(color=MUTED))
    if 'actual' in result:
        fig.add_scatter(x=result.index, y=result['actual'], name='Measured', mode='lines',
                        line=dict(color=TEXT, width=2))
    q_cols = [c for c in result.columns if c.startswith('q')]

    def traces(k):
        """The animated traces with the first k forecast steps."""
        r = result.iloc[:k]
        out = []
        if len(q_cols) == 2:
            out.append(go.Scatter(x=r.index, y=r[q_cols[0]], mode='lines', line=dict(width=0),
                                  showlegend=False, hoverinfo='skip'))
            out.append(go.Scatter(x=r.index, y=r[q_cols[1]], mode='lines', line=dict(width=0),
                                  fill='tonexty', fillcolor='rgba(200,85,61,0.18)', name='90 % interval'))
        out.append(go.Scatter(x=r.index, y=r['forecast'], mode='lines+markers', name='Forecast',
                              line=dict(color=COLOR, width=3), marker=dict(size=5)))
        return out

    n_static = len(fig.data)
    for trace in traces(len(result)):           # start by showing the whole forecast
        fig.add_trace(trace)
    animated = list(range(n_static, len(fig.data)))
    fig.frames = [go.Frame(data=traces(k), traces=animated, name=str(k)) for k in range(1, len(result) + 1)]

    play = dict(frame=dict(duration=150, redraw=True), transition=dict(duration=0), fromcurrent=False)
    fig.update_layout(
        height=520, hovermode='x unified', yaxis_title="Degree of filling (%)",
        xaxis_range=[history.index[0], result.index[-1] + pd.Timedelta(weeks=2)], yaxis_range=[0, 100],
        updatemenus=[dict(type='buttons', showactive=False, x=0, y=-0.12, xanchor='left', yanchor='top',
                          buttons=[dict(label='▶ Play', method='animate', args=[None, play]),
                                   dict(label='⏸ Pause', method='animate',
                                        args=[[None], dict(frame=dict(duration=0, redraw=False), mode='immediate')])])],
        sliders=[dict(active=len(result) - 1, x=0.12, len=0.88, y=-0.08, yanchor='top',
                      currentvalue=dict(prefix='Weeks forecast: '),
                      steps=[dict(method='animate', label=str(k),
                                  args=[[str(k)], dict(mode='immediate', frame=dict(duration=0, redraw=True))])
                             for k in range(1, len(result) + 1)])],
        margin=dict(b=120),
    )
    return fig


history = train['fill'].iloc[-156:]               # the last three years of the training data
show(animated_forecast(result, history))
st.caption("Press ▶ Play to see the dynamic forecast build up week by week.")

with st.expander("Forecast values"):
    st.dataframe(result.round(2))
with st.expander("About the model"):
    st.write("""
        River's SNARIMAX learns one week at a time. The AR and MA terms (lags of the filling and
        of the errors) and the exogenous variables are fed to a standardised linear regression
        trained with stochastic gradient descent. The forecast is dynamic: each step builds on
        the model's own earlier forecasts. Future weather is not known in a real forecast, so by
        default the mean of the same week in the training years is used. The 90 % interval comes
        from two extra models trained with the quantile loss (alpha 0.05 and 0.95).
    """)
