import streamlit as st
from PIL import Image

st.set_page_config(layout="wide")

col1, col2 = st.columns(2)

with col1:
    st.header("Welcome to the TraffMind AI JAMAR Portal V1.2")
    st.write("""
    This portal is designed to allow JAMAR to get a hands-on experience with TraffMind AI, showcasing state-of-the-art technology in video traffic analysis. Dive into our newest models and explore how advanced AI can transform traffic data into actionable insights, driving efficiency and safety in urban mobility.
    """)

with col2:
    # Load and display an image (ensure the image 'traffmind-jamar.jpg' is in the same directory as your script)
    image = Image.open('traffmind-jamar.png')
    st.image(image, use_column_width=True)
