# Page showing the ENTSO-E cross-border power flow data, read directly from MongoDB
# (the same data that was prepared via Cassandra and Spark in the notebook)
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pymongo
import certifi
import matplotlib.dates as mdates

st.set_page_config(
    page_title="Kraftflyt",
    layout="wide",
)

st.title("Kraftflyt NO2-DK1")
st.write("Cross-border power flow data between Norway (NO2) and Denmark (DK1), read from MongoDB.")


# Connect to MongoDB. On Streamlit Cloud, the connection details are read from
# st.secrets (set under the app's "Secrets" settings on streamlit.io). When running
# locally, we fall back to the No_sync file used elsewhere in this project, so the
# same credentials are never duplicated or committed to GitHub in either case.
@st.cache_resource
def get_kraftflyt_collection():
    # st.secrets raises an error (rather than just being empty) when no secrets.toml
    # file exists at all, which is the case when running locally, so we catch that here.
    try:
        uri = st.secrets["mongo"]["uri"]
    except (FileNotFoundError, KeyError, st.errors.StreamlitSecretNotFoundError):
        with open('No_sync/MongoDB') as f:
            user, password = f.read().splitlines()
        uri = f"mongodb+srv://{user}:{password}@cluster0.z3mwysd.mongodb.net/?retryWrites=true&w=majority"

    client = pymongo.MongoClient(uri, tlsCAFile=certifi.where())
    return client['ind320']['kraftflyt']


# Cache the actual data fetch separately, since a MongoDB connection object itself
# cannot be cached with st.cache_data
@st.cache_data
def load_kraftflyt():
    collection = get_kraftflyt_collection()
    docs = list(collection.find({}, {'_id': 0}))
    df = pd.DataFrame(docs)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


df_kraft = load_kraftflyt()

left, right = st.columns(2)

with left:
    st.subheader("Total flow by year")

    # Only one connection was fetched for this project (NO2-DK1), per the assignment's
    # "a chosen connection" wording, so the radio button has a single option
    connection = st.radio("Select connection", ["NO2 - DK1"])

    years = sorted(df_kraft['timestamp'].dt.year.unique())
    selected_year = st.selectbox("Select year", years, index=years.index(2025) if 2025 in years else 0)

    df_year = df_kraft[df_kraft['timestamp'].dt.year == selected_year]
    sum_per_retning = df_year.groupby(['from_area', 'to_area'])['quantity_mw'].sum()

    ut_av_norge = sum_per_retning.get(('NO2', 'DK1'), 0)
    inn_til_norge = sum_per_retning.get(('DK1', 'NO2'), 0)

    fig_pie, ax_pie = plt.subplots(figsize=(5, 5))
    wedges, _, _ = ax_pie.pie(
        [ut_av_norge, inn_til_norge],
        autopct='%1.1f%%',
        startangle=90,
    )
    # Labels in a legend below the pie instead of next to the slices, so their position
    # does not depend on the slice sizes
    ax_pie.legend(
        wedges,
        ['Ut av Norge (NO2 -> DK1)', 'Inn til Norge (DK1 -> NO2)'],
        loc='upper center',
        bbox_to_anchor=(0.5, 0.02),
        ncol=1,
        frameon=False,
    )
    ax_pie.set_title(f"Kraftflyt NO2-DK1, totalt for {selected_year}")
    ax_pie.axis('equal')
    # bbox_inches=None keeps the full 5x5 figure instead of Streamlit's default 'tight'
    # cropping, so the pie has the same size for every year
    st.pyplot(fig_pie, bbox_inches=None)
    plt.close(fig_pie)

with right:
    st.subheader("Flow over selected months")

    month_names = ["Jan", "Feb", "Mar", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Des"]
    selected_months = st.pills("Select months", month_names, selection_mode="multi", default=["Jan"])
    selected_month_numbers = [month_names.index(m) + 1 for m in selected_months]

    df_months = df_year[df_year['timestamp'].dt.month.isin(selected_month_numbers)]

    fig_line, ax_line = plt.subplots(figsize=(8, 5))
    has_lines = False
    for (fra, til), gruppe in df_months.groupby(['from_area', 'to_area']):
        ax_line.plot(gruppe['timestamp'], gruppe['quantity_mw'], label=f'{fra} -> {til}', linewidth=1)
        has_lines = True

    ax_line.set_xlabel("Tidspunkt")
    ax_line.set_ylabel("Mengde (MW)")
    ax_line.set_title(f"Kraftflyt NO2-DK1, {selected_year}")
    # Short, non-overlapping date labels: the locator picks sensible tick positions and
    # the concise formatter only shows the parts of the date that change (e.g. 'Jan', '08')
    locator = mdates.AutoDateLocator()
    ax_line.xaxis.set_major_locator(locator)
    ax_line.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax_line.grid(alpha=0.3)

    if has_lines:
        ax_line.legend()
        st.pyplot(fig_line)
    else:
        st.info("Velg minst én måned for å vise linjeplottet.")
    plt.close(fig_line)

with st.expander("About the data source"):
    st.write("""
        The data shown on this page comes from the ENTSO-E Transparency Platform API
        (cross-border physical flow, documentType A11), for the connection between
        Norway (NO2) and Denmark (DK1), covering the last two years. The raw data was
        fetched in the project notebook, inserted into a local Cassandra database using
        Spark, read back out of Cassandra with Spark, and then inserted into this
        MongoDB database. This page reads directly from MongoDB, as required.
    """)