import streamlit as st

# Set the page title and use the full width of the browser
st.set_page_config(
    page_title="IND320 Project",
    layout="wide",
)

st.title("IND320 - Project work, part 1")
st.write("Welcome to my dashboard for the weekly reservoir data in reservoirs.csv.")
st.write("Use the menu in the sidebar to open the table page and the plot page.")

# Show a hint in the sidebar, below the automatic page navigation
st.sidebar.success("Select a page above")