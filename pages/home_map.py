# Front page (part 4): interactive map of the areas from Magasinstatistikk.
#  - GeoJSON outlines of the price areas (EL), water areas (VASS) or Norway (NO)
#  - the areas are coloured transparently by the degree of filling or a weather property
#    for the week chosen with the slider
#  - a click in an area gives it a thick, contrasting outline and stores it as the selected
#    area in st.session_state, together with the chosen week. The other pages use these.
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.theme import page_header, show, HIGHLIGHT
from modules.data_loader import load_data_or_stop
from modules.area_selector import keep
from modules.geo import load_geojson, GEOJSON_FILE
from modules.weather import weather_for_period, DAILY_VARS, DAILY_LABELS, WeatherError

page_header(
    "Norwegian reservoirs, weather and power", "Home",
    "Choose the type of area, what to colour the areas by and the week. Click on an area to "
    "select it; the selected area and week are used on the other pages (see the menu).",
)

df = load_data_or_stop()
if not GEOJSON_FILE.exists():
    st.error("The map file project_data/areas.geojson is missing. Make it with "
             "`python scripts/make_geojson.py` (needs geopandas).")
    st.stop()

# Default selection the first time the app is opened: EL 3 and the latest week
st.session_state.setdefault('area_type', 'EL')
st.session_state.setdefault('area_number', 3)
dates = list(pd.DatetimeIndex(df['date'].unique()).sort_values())
if st.session_state.get('map_date') not in dates:
    st.session_state['map_date'] = dates[-1]

# ---- Selectors
type_labels = {'EL': 'Price areas (EL)', 'VASS': 'Water areas (VASS)', 'NO': 'Norway (NO)'}
col1, col2, col3 = st.columns([1.1, 1.2, 2.2])
area_type = col1.radio("Areas", list(type_labels), format_func=type_labels.get,
                       index=list(type_labels).index(st.session_state['area_type']))
colour_by = col2.radio("Colour by", ["Degree of filling", "Weather property"], horizontal=True)
weather_var = None
if colour_by == "Weather property":
    keep('weather_var', '_map_weather_var', DAILY_VARS[0])
    weather_var = col2.selectbox("Weather property", DAILY_VARS, format_func=DAILY_LABELS.get,
                                 key='_map_weather_var')
    st.session_state['weather_var'] = weather_var

# Time: the weeks in Magasinstatistikk (the date is the Sunday ending the ISO week)
keep('map_date', '_map_date', dates[-1])
if st.session_state['_map_date'] not in dates:
    st.session_state['_map_date'] = dates[-1]
date = col3.select_slider(
    "Week", options=dates, key='_map_date',
    format_func=lambda d: f"{pd.Timestamp(d):%d %b %Y} (week {pd.Timestamp(d).isocalendar().week})",
    help="Also used as the end of the training data on the forecast page.",
)
st.session_state['map_date'] = date
date = pd.Timestamp(date)

# Fixed places for messages and the title above the map. Streamlit identifies elements by
# their position on the page, so a message or spinner that only appears sometimes would move
# the map one place down; Streamlit would then treat it as a new chart and draw it from scratch
# (the map disappeared for half a second). With fixed containers the map keeps its position.
messages = st.container()
title = st.empty()

# ---- Values used to colour the areas
geo = load_geojson(area_type)
areas = [ft['properties']['area'] for ft in geo['features']]
week = df[(df['area_type'] == area_type) & (df['date'] == date)].set_index('area')

if colour_by == "Degree of filling":
    values = 100 * week['fill_ratio'].reindex(areas)
    label, colorscale = "Degree of filling (%)", "Blues"
    period_text = f"week ending {date:%d %b %Y}"
else:
    # Weather aggregated over the same ISO week (Monday to Sunday); ERA5 lags about 5 days
    start, end = date - pd.Timedelta(days=6), min(date, pd.Timestamp.today().normalize() - pd.Timedelta(days=6))
    values = pd.Series(index=areas, dtype=float)
    if end >= start:
        try:
            with messages, st.spinner("Getting weather data for the map ..."):
                values = weather_for_period(area_type, f"{start:%Y-%m-%d}", f"{end:%Y-%m-%d}")[weather_var].reindex(areas)
        except WeatherError as error:
            messages.warning(f"No weather data for the map: {error}")
    label = DAILY_LABELS[weather_var]
    colorscale = "RdBu_r" if 'temperature' in weather_var else "YlGnBu"
    period_text = f"{start:%d %b} – {end:%d %b %Y}"
    if values.isna().all():
        messages.info("ERA5 weather data is not published yet for this week (it lags about five days). "
                "Choose an earlier week to colour by weather.")

selected = f"{st.session_state['area_type']} {st.session_state['area_number']}"

# ---- Map: transparent colours, thin outlines, and a thick contrasting outline for the selection
fig = go.Figure(go.Choroplethmap(
    geojson=geo, featureidkey='properties.area', locations=areas, z=values.values,
    colorscale=colorscale, marker_opacity=0.55, marker_line_width=1, marker_line_color='#33414D',
    colorbar=dict(title=label, thickness=14), customdata=areas,
    hovertemplate='<b>%{location}</b><br>' + label + ': %{z:.1f}<extra></extra>',
))
if selected in areas:
    fig.add_trace(go.Choroplethmap(
        geojson=geo, featureidkey='properties.area', locations=[selected], z=[0],
        colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']], showscale=False,
        marker_line_width=4, marker_line_color=HIGHLIGHT, hoverinfo='skip',
    ))
# uirevision keeps the map (zoom and position) between reruns, so Plotly only updates the colours.
# The title is shown above the map in a fixed place instead, so the figure layout stays the same.
fig.update_layout(
    map=dict(style='carto-positron', center=dict(lat=65.0, lon=15.0), zoom=3.5,
             uirevision='map'),
    uirevision='map',
    height=640, margin=dict(l=0, r=0, t=10, b=0),
)
title.markdown(f"**{label}, {period_text}**")

# A click (point selection) reruns the page; the key depends on the area type so that the
# selection is reset when another type of area is shown
event = show(fig, on_select="rerun", selection_mode="points", key=f"map_{area_type}")
try:
    points = event.selection.points
except (AttributeError, KeyError, TypeError):
    points = []
if points:
    point = points[0]
    clicked = point.get('location') or (areas[point['point_index']] if 'point_index' in point else None)
    if clicked and clicked != selected:
        new_type, new_number = clicked.split()
        st.session_state['area_type'] = new_type
        st.session_state['area_number'] = int(new_number)
        st.rerun()

# ---- Summary of the selected area
st.subheader(f"Selected area: {selected}")
sel = df[(df['area'] == selected) & (df['date'] == date)]
if len(sel):
    row = sel.iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Degree of filling", f"{100 * row['fill_ratio']:.1f} %",
              f"{100 * row['fill_ratio_change']:+.1f} pp since last week")
    c2.metric("Filling", f"{row['fill_twh']:.1f} TWh")
    c3.metric("Capacity", f"{row['capacity_twh']:.1f} TWh")
else:
    st.info(f"No Magasinstatistikk data for {selected} in this week.")

with st.expander("Values for all areas in the map"):
    st.dataframe(values.rename(label).round(2).to_frame())

with st.expander("About the app"):
    st.write("""
        The app combines Norwegian reservoir statistics (NVE Magasinstatistikk), ERA5 weather
        data (open-meteo), cross-border power flow (ENTSO-E, stored in MongoDB) and exchange
        rates (Norges Bank). The menu is grouped into data overview, exploratory analyses and
        anomalies, and predictions. The area and week chosen here are stored in the session
        and used as defaults on the other pages; settings that only concern one page are
        chosen on that page.
    """)
