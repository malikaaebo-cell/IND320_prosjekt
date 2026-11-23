# Data overview: cross-border power flow NO2–DK1 (part 2), read directly from MongoDB (the same
# data that was prepared via Cassandra and Spark in the part 2 notebook).
# Update (part 4): Plotly instead of matplotlib, and a useful message if MongoDB is unavailable.
# Note (part 4 notebook): the time stamps are stored as Norwegian local time labelled as UTC,
# so they are shown here as local time.
import pandas as pd
import plotly.graph_objects as go
import pymongo
import certifi
import streamlit as st

from modules.theme import page_header, show

page_header("Power flow NO2–DK1", "Data overview",
            "Cross-border physical flow between Norway (NO2) and Denmark (DK1) from the ENTSO-E "
            "Transparency Platform, read from MongoDB.")


# Connect to MongoDB. On Streamlit Cloud, the connection details are read from st.secrets
# (set under the app's "Secrets" settings). When running locally, we fall back to the No_sync
# file, so the credentials are never committed to GitHub.
@st.cache_resource
def get_kraftflyt_collection():
    try:
        uri = st.secrets["mongo"]["uri"]
    except (FileNotFoundError, KeyError, st.errors.StreamlitSecretNotFoundError):
        with open('No_sync/MongoDB') as f:
            user, password = f.read().splitlines()
        uri = f"mongodb+srv://{user}:{password}@cluster0.z3mwysd.mongodb.net/?retryWrites=true&w=majority"
    client = pymongo.MongoClient(uri, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=10000)
    return client['ind320']['kraftflyt']


# The data fetch is cached separately, since the connection object cannot be cached with cache_data
@st.cache_data(show_spinner="Reading power flow data from MongoDB ...")
def load_kraftflyt():
    docs = list(get_kraftflyt_collection().find({}, {'_id': 0}))
    df = pd.DataFrame(docs)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


try:
    df_kraft = load_kraftflyt()
except Exception as error:           # missing credentials, network or database problems
    st.error(f"Could not read the power flow data from MongoDB. Check the connection and "
             f"credentials.\n\nDetails: {error}")
    st.stop()
if df_kraft.empty:
    st.warning("The MongoDB collection is empty.")
    st.stop()

left, right = st.columns([1, 1.6])
years = sorted(df_kraft['timestamp'].dt.year.unique())

with left:
    st.subheader("Total flow by year")
    selected_year = st.selectbox("Year", years, index=len(years) - 1)
    df_year = df_kraft[df_kraft['timestamp'].dt.year == selected_year]
    total = df_year.groupby(['from_area', 'to_area'])['quantity_mw'].sum()

    fig = go.Figure(go.Pie(
        labels=['Out of Norway (NO2 → DK1)', 'Into Norway (DK1 → NO2)'],
        values=[total.get(('NO2', 'DK1'), 0), total.get(('DK1', 'NO2'), 0)],
        hole=0.45, marker=dict(colors=['#2A6F97', '#E9A03B']), sort=False,
        hovertemplate='%{label}<br>%{percent}<extra></extra>',
    ))
    fig.update_layout(title=f"Share of the flow in {selected_year}", height=420,
                      legend=dict(orientation='h', y=-0.1, x=0.5, xanchor='center'))
    show(fig)

with right:
    st.subheader("Flow over selected months")
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    selected_months = st.pills("Months", month_names, selection_mode="multi", default=["Jan"])
    numbers = [month_names.index(m) + 1 for m in selected_months or []]
    df_months = df_year[df_year['timestamp'].dt.month.isin(numbers)]

    if df_months.empty:
        st.info("Select at least one month with data to show the line plot.")
    else:
        fig = go.Figure()
        for (src, dst), group in df_months.groupby(['from_area', 'to_area']):
            fig.add_scatter(x=group['timestamp'], y=group['quantity_mw'], mode='lines',
                            name=f'{src} → {dst}', line=dict(width=1))
        fig.update_layout(title=f"Power flow NO2–DK1, {selected_year}", xaxis_title="Time (Norwegian time)",
                          yaxis_title="Flow (MW)", height=420, hovermode='x unified')
        show(fig)

with st.expander("About the data source"):
    st.write("""
        The data comes from the ENTSO-E Transparency Platform API (cross-border physical flow,
        documentType A11) for the connection between Norway (NO2) and Denmark (DK1). The raw data
        was fetched in the part 2 notebook, inserted into Cassandra with Spark, read back and
        inserted into this MongoDB database. This page reads directly from MongoDB.
    """)
