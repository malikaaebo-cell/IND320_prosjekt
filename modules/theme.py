# theme.py
# Common look of the app (part 4):
#  - one colour per menu group, used in the page header and the active menu item
#  - a Plotly template with the same colours and font as the Streamlit theme
#    (.streamlit/config.toml), set as default for all plots
#  - helpers for the page header and for showing Plotly figures with this template
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

PRIMARY = "#2A6F97"       # blue: main colour, same as primaryColor in config.toml
TEXT = "#1F2A33"
GRID = "#E3E8EC"
MUTED = "#8A949C"         # history and other background lines
HIGHLIGHT = "#FF5A1F"     # selected area on the map, anomalies/outliers

# One colour per group in the menu (same as in the sketch in the notebook)
GROUPS = {
    "Home": "#2A6F97",
    "Data overview": "#2A9D8F",
    "Exploratory & anomalies": "#E9A03B",
    "Predictive": "#C8553D",
}

COLORWAY = ["#2A6F97", "#E9A03B", "#2A9D8F", "#C8553D", "#6C5B7B",
            "#8AB17D", "#B56576", "#4D908E", "#F4A261"]

# Plotly template matching the app theme; 'plotly_white' is used as the base
pio.templates["ind320"] = go.layout.Template(layout=dict(
    font=dict(family="Source Sans Pro, Arial, sans-serif", color=TEXT, size=13),
    colorway=COLORWAY,
    paper_bgcolor="white",
    plot_bgcolor="white",
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor="#B8C2CA"),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor="#B8C2CA"),
    title=dict(font=dict(size=16), x=0, xanchor="left"),
    legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
    margin=dict(l=60, r=20, t=80, b=40),
    hoverlabel=dict(font_size=12),
))
pio.templates.default = "plotly_white+ind320"


def page_header(title, group, intro=None):
    """Title of a page, with a badge and highlighted menu item in the colour of its group."""
    color = GROUPS[group]
    st.markdown(
        f"<span style='background:{color}; color:white; padding:3px 12px; border-radius:12px; "
        f"font-size:0.8rem; font-weight:600'>{group}</span>"
        # Colour the active page in the sidebar menu with the group colour
        f"<style>[data-testid='stSidebarNav'] a[aria-current='page'] {{background-color:{color}26;}}"
        f"[data-testid='stSidebarNav'] a[aria-current='page'] span {{color:{color}; font-weight:600;}}</style>",
        unsafe_allow_html=True,
    )
    st.title(title)
    if intro:
        st.write(intro)
    return color


def show(fig, **kwargs):
    """Show a Plotly figure with our own template (theme=None) instead of Streamlit's."""
    return st.plotly_chart(fig, theme=None, **kwargs)
