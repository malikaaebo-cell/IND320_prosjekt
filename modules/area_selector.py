# area_selector.py
# Shared area selector in the sidebar, used by the reservoir and weather pages (part 3).
# The choice is stored in st.session_state, so the same area stays selected when the
# user moves between pages. The weather data that is downloaded depends on this choice.
import streamlit as st


def select_area(df):
    """
    Show radio buttons for area type and a dropdown for area number in the sidebar.
    The options come from the Magasinstatistikk data (df).
    Returns the selected area type (e.g. 'EL') and area number (e.g. 3).
    """
    # Default selection the first time the app is opened: NO3 (EL 3), as in the notebook
    if 'area_type' not in st.session_state:
        st.session_state['area_type'] = 'EL'
        st.session_state['area_number'] = 3

    st.sidebar.header("Area")

    # Area type: EL, NO or VASS, with the saved choice as the selected option
    area_types = sorted(df['area_type'].unique())
    area_type = st.sidebar.radio(
        "Area type", area_types,
        index=area_types.index(st.session_state['area_type']),
        horizontal=True,
    )

    # Area number: only the numbers that exist for the chosen area type
    numbers = sorted(df.loc[df['area_type'] == area_type, 'area_number'].unique())
    saved_number = st.session_state['area_number']
    area_number = st.sidebar.selectbox(
        "Area number", numbers,
        index=numbers.index(saved_number) if saved_number in numbers else 0,
    )

    # Save the choice so the other pages start with the same area
    st.session_state['area_type'] = area_type
    st.session_state['area_number'] = area_number
    return area_type, area_number
