import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO
from streamlit_drawable_canvas import st_canvas
import requests

def get_background_image_url(url):
    base_url_path = st._config.get_option("server.baseUrlPath").strip("/")
    if base_url_path:
        base_url_path = "/" + base_url_path
    return base_url_path + url

# URL of the background image
background_image_url = "https://www.crowsonlaw.com/wp-content/webp-express/webp-images/uploads/2023/11/right-of-way-rules.jpg.webp"

# Modify the URL if necessary
modified_image_url = get_background_image_url(background_image_url)

# Load background image from the modified URL
response = requests.get(modified_image_url)
bg_image = Image.open(BytesIO(response.content))

# Create a canvas component
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=3,
    stroke_color="rgba(0, 0, 255, 1)",
    background_color="#eee",
    background_image=bg_image,
    update_streamlit=True,
    height=400,
    width=600,
    drawing_mode="line",
    display_toolbar=False,
    key="full_app",
)

# Process and display canvas data
if canvas_result.json_data is not None:
    objects = pd.json_normalize(canvas_result.json_data["objects"])
    for col in objects.select_dtypes(include=["object"]).columns:
        objects[col] = objects[col].astype("str")

    if not objects.empty:
        st.subheader("List of line drawings")
        for _, row in objects.iterrows():
            st.markdown(
                f'Start coords: ({row["x1"]:.2f}, {row["y1"]:.2f}), End coords: ({row["x2"]:.2f}, {row["y2"]:.2f})'
            )
    st.dataframe(objects)
