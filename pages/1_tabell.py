import streamlit as st
import pandas as pd
from modules.data_loader import load_data

st.title("Tabell")
st.write("Dette er en tabell med LineChartColumn() for hver kolonne i datasettet.")

# Last inn dataene via den delte, cachede funksjonen (samme som brukes på plot-siden)
df = load_data()

# Finn datasettets første måned, siden tabellen kun skal vise trend for denne perioden
first_date = df['date'].min()
first_month_mask = (df['date'].dt.year == first_date.year) & (df['date'].dt.month == first_date.month)
first_month_df = df[first_month_mask]

# Velg kun numeriske kolonner, siden tekstkolonner ikke kan vises som trendlinje
numeric_cols = df.select_dtypes(include='number').columns.tolist()

# Bygg tabellen: én rad per numerisk kolonne, med en liste av verdier fra første måned
# (listen brukes av LineChartColumn under til å tegne en minigraf per rad)
table_data = pd.DataFrame({
    "Kolonne": numeric_cols,
    "Trend (første måned)": [first_month_df[col].tolist() for col in numeric_cols]
})

# Vis tabellen, med "Trend"-kolonnen endret igjen som en linjegraf i stedet for rå tall
# LineChartColumn er en Streamlit-widget
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