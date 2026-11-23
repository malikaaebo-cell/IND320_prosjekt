# Data overview: the Magasinstatistikk data (part 1-2, merged in part 4).
# The former table page (LineChartColumn) and plot page are joined here as two tabs, since both
# give an overview of the same data. The area type comes from the shared selector in the
# sidebar; both tabs show all area numbers of that type.
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.theme import page_header, show
from modules.data_loader import load_data_or_stop
from modules.area_selector import select_area

page_header("Reservoir data", "Data overview",
            "Weekly reservoir statistics from NVE's Magasinstatistikk API, one line per area "
            "number within the area type selected in the sidebar.")

df = load_data_or_stop()
area_type, _ = select_area(df)
df_type = df[df['area_type'] == area_type].copy()

# Only these columns are real measurements; iso_year, iso_week and area_number are identifiers
measurement_cols = {
    'fill_ratio': 'Degree of filling',
    'capacity_twh': 'Capacity (TWh)',
    'fill_twh': 'Filling (TWh)',
    'fill_ratio_previous_week': 'Degree of filling, previous week',
    'fill_ratio_change': 'Change in degree of filling',
}

# Month labels ('YYYY-MM' sorts correctly as text) for the period selectors
df_type['year_month'] = df_type['date'].dt.strftime('%Y-%m')
months = sorted(df_type['year_month'].unique())

tab_plot, tab_table = st.tabs(["Plot", "Table with small line charts"])

with tab_plot:
    col1, col2 = st.columns([1, 2])
    column = col1.selectbox("Column", list(measurement_cols), format_func=measurement_cols.get)
    # Default: the last three years, which shows the seasonal pattern clearly
    start, end = col2.select_slider("Period (months)", options=months,
                                    value=(months[max(0, len(months) - 36)], months[-1]),
                                    format_func=lambda m: pd.Timestamp(m).strftime('%b %Y'))
    period = df_type[(df_type['year_month'] >= start) & (df_type['year_month'] <= end)]

    fig = go.Figure()
    for number, df_area in period.groupby('area_number'):
        fig.add_scatter(x=df_area['date'], y=df_area[column], mode='lines',
                        name=f'{area_type} {number}', line=dict(width=1.6))
    fig.update_layout(title=f"{measurement_cols[column]}, all {area_type} areas",
                      xaxis_title="Date", yaxis_title=measurement_cols[column], height=480,
                      hovermode='x unified')
    show(fig)

with tab_table:
    st.write("One row per area number. Each small line chart shows the selected months "
             "(the first month by default, as in part 1).")
    # Month picker added in part 3 after peer review, so the charts are not locked to Jan 1995
    first, last = st.select_slider("Months", options=months, value=(months[0], months[0]),
                                   format_func=lambda m: pd.Timestamp(m).strftime('%b %Y'),
                                   key='table_months')
    selected = df_type[(df_type['year_month'] >= first) & (df_type['year_month'] <= last)]

    # Each cell holds the list of values for the selected months, drawn by LineChartColumn
    rows = []
    for number, df_area in selected.groupby('area_number'):
        rows.append({"Area": f"{area_type} {number}",
                     **{col: df_area[col].tolist() for col in measurement_cols}})
    st.dataframe(
        pd.DataFrame(rows),
        column_config={col: st.column_config.LineChartColumn(label, width="medium")
                       for col, label in measurement_cols.items()},
        hide_index=True,
    )
