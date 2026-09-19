import streamlit as st
import pandas as pd
from modules.data_loader import load_data

st.title("Tabell")
st.write("Dette er en tabell med LineChartColumn() for hver kolonne i datasettet.")

df = load_data()

first_date = df['date'].min()
first_month_mask = (df['date'].dt.year == first_date.year) & (df['date'].dt.month == first_date.month)
first_month_df = df[first_month_mask]

numeric_cols = df.select_dtypes(include='number').columns.tolist()

table_data = pd.DataFrame({
    "Kolonne": numeric_cols,
    "Trend (første måned)": [first_month_df[col].tolist() for col in numeric_cols]
})

st.dataframe(
    table_data,
    column_config={
        "Trend (første måned)": st.column_config.LineChartColumn(
            "Trend (første måned)",
            width="medium"
        )
    },
    hide_index=True,
    use_container_width=True
)