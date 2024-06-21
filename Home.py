import streamlit as st
from PIL import Image
header = st.container()
header.title("Development Version")
header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

### Custom CSS for the sticky header
st.markdown(
    """
<style>
    div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
        position: sticky;
        top: 2.875rem;
        background-color: red;
        z-index: 999;
    }
    .fixed-header {
        border-bottom: 1px solid black;
    }
</style>
    """,
    unsafe_allow_html=True
)


col1, col2 = st.columns(2)

with col1:
    st.header("Welcome to the TraffMind AI JAMAR Portal")
    st.write("""
    This portal is designed to allow JAMAR to get a hands-on experience with TraffMind AI, showcasing state-of-the-art technology in video traffic analysis. Dive into our newest models and explore how advanced AI can transform traffic data into actionable insights, driving efficiency and safety in urban mobility.
    """)

with col2:
    # Load and display an image (ensure the image 'traffmind-jamar.jpg' is in the same directory as your script)
    image = Image.open('traffmind-jamar.png')
    st.image(image, use_column_width=True)

