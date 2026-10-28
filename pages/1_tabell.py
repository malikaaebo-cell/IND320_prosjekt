# Page with a table of the imported data, one row per area number (within the chosen
# area type), with a small line chart per column showing the selected months of data.
# Update (part 3): added a month picker after peer review feedback, so the line charts
# are no longer locked to the first month (January 1995).
import streamlit as st
import pandas as pd
from modules.data_loader import load_data
from modules.area_selector import select_area

# Set the page title and use the full width of the browser
st.set_page_config(
    page_title="Table",
    layout="wide",
)

st.title("Table")
st.write(
    "One row per area number within the selected area type. "
    "Each line chart shows the selected months of that area's data "
    "(the first month by default)."
)

# Load the data using the shared, cached function (also used on the plot page)
df = load_data()

# Area type (EL, NO or VASS) from the shared selector in the sidebar (part 3). The table
# shows all area numbers of the chosen type, as required in part 2; the area number in the
# sidebar is used by the analysis pages.
area_type, _ = select_area(df)
df_type = df[df['area_type'] == area_type]

# Month label for each row, e.g. '1995-01'. The 'YYYY-MM' format sorts correctly as text,
# so it can be compared directly when filtering.
month_labels = df_type['date'].dt.strftime('%Y-%m')
months = sorted(month_labels.unique())

# Month picker: a range slider with the first month as default, as the original task asks.
# Choosing a longer range (e.g. a whole year) shows the seasonal pattern, since the data
# is weekly and one month only gives 4-5 points per line chart.
start_month, end_month = st.select_slider(
    "Select months",
    options=months,
    value=(months[0], months[0]),
    format_func=lambda m: pd.Timestamp(m).strftime('%b %Y'),
)

df_selected = df_type[(month_labels >= start_month) & (month_labels <= end_month)]

# Only these columns are real measurements; iso_year, iso_week and area_number are
# identifiers, not something that makes sense as a sparkline
measurement_cols = ['fill_ratio', 'capacity_twh', 'fill_twh', 'fill_ratio_previous_week', 'fill_ratio_change']

# Build one row per area number within the selected type. Each cell holds the list of
# values for the selected months, which LineChartColumn draws as a small line chart.
rows = []
for area_number, df_area in df_selected.groupby('area_number'):
    row = {"Area": f"{area_type} {area_number}"}
    for col in measurement_cols:
        row[col] = df_area[col].tolist()
    rows.append(row)

table_data = pd.DataFrame(rows)

# Show the table with one LineChartColumn per measurement column
st.dataframe(
    table_data,
    column_config={
        col: st.column_config.LineChartColumn(col, width="medium")
        for col in measurement_cols
    },
    hide_index=True
)