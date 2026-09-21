# Page with a table of the imported data, one row per column, with a small line chart of the first month
import streamlit as st
import pandas as pd
from modules.data_loader import load_data

# Set the page title and use the full width of the browser
st.set_page_config(
    page_title="Table",
    layout="wide",
)

st.title("Table")
st.write("One row per column in the data set. The line chart shows the first month of the series.")

# Load the data using the shared, cached function (also used on the plot page)
df = load_data()

# Drop-down menu for choosing which area to show, since the data contains nine areas
area = st.selectbox("Select area", sorted(df['area'].unique()))
df_area = df[df['area'] == area]

# Find the first month in the data set and keep only the rows from that month
first_date = df_area['date'].min()
first_month_mask = (df_area['date'].dt.year == first_date.year) & (df_area['date'].dt.month == first_date.month)
first_month_df = df_area[first_month_mask]

# Use the original columns of the CSV file, i.e., leave out the 'area' label added by the loader
columns = [col for col in df.columns if col != 'area']

# Build the table with one row per column. Each row holds the list of values from the first month.
# Text and date columns cannot be drawn as a line, so they get None (an empty cell).
table_data = pd.DataFrame({
    "Column": columns,
    "First month": [
        first_month_df[col].tolist() if pd.api.types.is_numeric_dtype(df[col]) else None
        for col in columns
    ]
})

# Show the table. LineChartColumn is a column configuration that draws a small line chart
# from the list of values in each cell. Each row is scaled to its own minimum and maximum.
st.dataframe(
    table_data,
    column_config={
        "First month": st.column_config.LineChartColumn(
            "First month (weekly values)",
            width="medium"
        )
    },
    hide_index=True
)