import streamlit as st
from lib import get_s3_status
def show_table_with_links(df):
    # Convert DataFrame to HTML, replacing text URL with an HTML link
    df['Download Link'] = df['Download Link'].apply(lambda x: f'<a href="{x}" target="_blank">Download</a>' if x is not None else "")
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

st.set_page_config(page_title="Traffic Tracker - Processed Videos", layout="wide")

st.header("TraffMind AI Traffic Tracker")

st.markdown("""
Experience our Traffic Tracker's capabilities firsthand. This feature automatically identifies and tracks vehicles with bounding boxes, enhancing traffic video analysis. Follow the steps below to view and download your processed videos:
""")
st.markdown("""
**1. Refresh Data**: Click the button below to refresh the list of processed videos.
""")
refresh = st.button('Refresh Data', key='refresh')
st.markdown("""
**2. Download Video**: After refreshing, use the main panel to download your processed videos.
""")

# Manage initial load and refresh with session state
if 'first_load' not in st.session_state:
    st.session_state['first_load'] = True

# Auto-refresh on the initial load or when the refresh button is pressed
if 'first_load' not in st.session_state or refresh:
    data_df = get_s3_status()
    # Display data
    show_table_with_links(data_df)
    st.session_state['first_load'] = False
