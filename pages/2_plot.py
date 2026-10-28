# Page with a plot of the reservoir data, with selection of area type, column and
# download interval
import streamlit as st
import matplotlib.pyplot as plt
from modules.data_loader import load_data
from modules.area_selector import select_area

# Set the page title and use the full width of the browser
st.set_page_config(
    page_title="Plot",
    layout="wide",
)

st.title("Plot")
st.write("Plot of one column, with a separate line for each area number within the selected area type.")

# Load the data using the shared, cached function (also used on the table page)
df = load_data()

# Area type (EL, NO or VASS) from the shared selector in the sidebar (part 3). The plot
# shows all area numbers of the chosen type, as required in part 2.
area_type, _ = select_area(df)
df_type = df[df['area_type'] == area_type].copy()

# Only these columns are real measurements; iso_year, iso_week and area_number are
# identifiers and are left out of the dropdown
measurement_cols = ['fill_ratio', 'capacity_twh', 'fill_twh', 'fill_ratio_previous_week', 'fill_ratio_change']
selected_column = st.selectbox("Select column", measurement_cols)

# Make a list of the available months as text (e.g., '1995-01') for the slider
df_type['year_month'] = df_type['date'].dt.to_period('M').astype(str)
months = sorted(df_type['year_month'].unique())

# Update (part 2): this slider now controls the download interval, i.e., which of the
# data already fetched from the API (see modules/data_loader.py) is actually used here.
# The NVE API itself does not support filtering by date in the request, so "download
# interval" means which part of the downloaded data set the app works with, not a
# narrower API call.
selected_period = st.select_slider(
    "Select download interval (months)",
    options=months,
    value=(months[0], months[0])
)

# Keep only the rows within the selected download interval
start, end = selected_period
filtered = df_type[(df_type['year_month'] >= start) & (df_type['year_month'] <= end)]

# Create the figure, with one line per area number within the selected area type
fig, ax = plt.subplots(figsize=(10, 5))

# Show markers only for short periods, since they clutter the plot over many months
marker = 'o' if len(filtered) <= 60 else None

for area_number, df_area in filtered.groupby('area_number'):
    ax.plot(df_area['date'], df_area[selected_column], marker=marker, label=f'{area_type} {area_number}', linewidth=1)

ax.legend(fontsize='small', loc='center left', bbox_to_anchor=(1, 0.5))
ax.set_ylabel(selected_column)
ax.set_xlabel("Date")
ax.set_title(f"{selected_column}, all {area_type} areas")
ax.grid(alpha=0.3)

# Show the figure in the app and close it afterwards to free memory between reruns
st.pyplot(fig)
plt.close(fig)