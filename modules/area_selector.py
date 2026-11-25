# area_selector.py
# Shared area selector in the sidebar, used by the reservoir and weather pages (part 3).
# The choice is stored in st.session_state, so the same area stays selected when the
# user moves between pages. The weather data that is downloaded depends on this choice.
# Update (part 4): the area can also be chosen by clicking on the map on the front page,
# which writes to the same session state keys. The week chosen on the map is stored as
# 'map_date' and used as default time on the other pages.
import streamlit as st


def keep(state_key, widget_key, default):
    """
    Give a widget (with key widget_key) its start value from a value that is kept across pages
    (state_key). Streamlit deletes a widget's own key when the user leaves the page, so the
    shared value is stored under a separate key. The widget gets no index/value argument, which
    would make Streamlit treat it as a new widget (and reset it) every time the value changes.
    """
    st.session_state.setdefault(state_key, default)
    if widget_key not in st.session_state:
        st.session_state[widget_key] = st.session_state[state_key]


def select_area(df):
    """
    Show radio buttons for area type and a dropdown for area number in the sidebar.
    The options come from the Magasinstatistikk data (df).
    Returns the selected area type (e.g. 'EL') and area number (e.g. 3).
    """
    st.sidebar.header("Area")
    st.sidebar.caption("Also selected by clicking on the map on the front page.")

    # Area type: EL, NO or VASS. Default the first time: NO3 (EL 3), as in the notebook
    area_types = sorted(df['area_type'].unique())
    keep('area_type', '_area_type', 'EL')
    area_type = st.sidebar.radio("Area type", area_types, horizontal=True, key='_area_type')

    # Area number: only the numbers that exist for the chosen area type
    numbers = sorted(int(n) for n in df.loc[df['area_type'] == area_type, 'area_number'].unique())
    keep('area_number', '_area_number', 3)
    if st.session_state['_area_number'] not in numbers:      # e.g. after changing the area type
        st.session_state['_area_number'] = numbers[0]
    area_number = st.sidebar.selectbox("Area number", numbers, key='_area_number')

    # Save the choice so the other pages (and the map) start with the same area
    st.session_state['area_type'] = area_type
    st.session_state['area_number'] = area_number
    return area_type, area_number


def selected_date(df):
    """The week chosen on the map (default: the latest week in Magasinstatistikk)."""
    return st.session_state.get('map_date', df['date'].max())
