# Page with a table of the imported data, one row per area number (within the chosen
# area type), with a small line chart per column showing the first month of data
import streamlit as st
import pandas as pd
from modules.data_loader import load_data

# Set the page title and use the full width of the browser
st.set_page_config(
    page_title="Table",
    layout="wide",
)

st.title("Table")
st.write("One row per area number within the selected area type. Each line chart shows the first month of that area's data.")

# Load the data using the shared, cached function (also used on the plot page)
df = load_data()

# Radio buttons for choosing area type (EL, NO or VASS), per the part 2 requirements:
# "such that plots and LineChartColumn() show the corresponding graphics for each
# of the associated area numbers"
area_type = st.radio("Select area type", sorted(df['area_type'].unique()), horizontal=True)
df_type = df[df['area_type'] == area_type]

# Only these columns are real measurements; iso_year, iso_week and area_number are
# identifiers, not something that makes sense as a sparkline
measurement_cols = ['fill_ratio', 'capacity_twh', 'fill_twh', 'fill_ratio_previous_week', 'fill_ratio_change']

# Build one row per area number within the selected type. Each cell holds the list of
# values for that area's first month, which LineChartColumn draws as a small line chart.
rows = []
for area_number, df_area in df_type.groupby('area_number'):
    first_date = df_area['date'].min()
    first_month_mask = (df_area['date'].dt.year == first_date.year) & (df_area['date'].dt.month == first_date.month)
    first_month_df = df_area[first_month_mask]

    row = {"Area": f"{area_type} {area_number}"}
    for col in measurement_cols:
        row[col] = first_month_df[col].tolist()
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