# Page with a plot of the reservoir data, with selection of area, column and months
import streamlit as st
import matplotlib.pyplot as plt
from modules.data_loader import load_data

# Set the page title and use the full width of the browser
st.set_page_config(
    page_title="Plot",
    layout="wide",
)

st.title("Plot")
st.write("Plot of one column, or all columns together, for a selected area and period.")

# Load the data using the shared, cached function (also used on the table page)
df = load_data()

# Drop-down menu for choosing area, since the data contains nine areas
area = st.selectbox("Select area", sorted(df['area'].unique()))
df_area = df[df['area'] == area].copy()

# Keep only numeric columns, since these are the only ones that can be plotted
numeric_cols = df_area.select_dtypes(include='number').columns.tolist()

# Drop-down menu for choosing one column or all columns together
selected_column = st.selectbox("Select column", ["All columns"] + numeric_cols)

# Make a list of the available months as text (e.g., '1995-01') for the slider
df_area['year_month'] = df_area['date'].dt.to_period('M').astype(str)
months = sorted(df_area['year_month'].unique())

# Selection slider for a range of months. The default is the first month only.
selected_period = st.select_slider(
    "Select months",
    options=months,
    value=(months[0], months[0])
)

# Keep only the rows within the selected months
start, end = selected_period
filtered = df_area[(df_area['year_month'] >= start) & (df_area['year_month'] <= end)]

# Create the figure
fig, ax = plt.subplots(figsize=(10, 5))

# Show markers only for short periods, since they clutter the plot over many years
marker = 'o' if len(filtered) <= 60 else None

if selected_column == "All columns":
    col_min = df_area[numeric_cols].min()
    col_range = df_area[numeric_cols].max() - col_min
    normalised = ((filtered[numeric_cols] - col_min) / col_range).fillna(0)
    for col in numeric_cols:
        ax.plot(filtered['date'], normalised[col], marker=marker, label=col, alpha=0.7, linewidth=1)
    ax.legend(fontsize='small', loc='center left', bbox_to_anchor=(1, 0.5))
    ax.set_ylabel("Normalised value (0-1)")
    ax.set_title(f"All columns, normalised ({area})")
else:
    # Plot the selected column directly, no scaling is needed with only one scale
    ax.plot(filtered['date'], filtered[selected_column], marker=marker)
    ax.set_ylabel(selected_column)
    ax.set_title(f"{selected_column} ({area})")

ax.set_xlabel("Date")
ax.grid(alpha=0.3)

# Show the figure in the app and close it afterwards to free memory between reruns
st.pyplot(fig)
plt.close(fig)