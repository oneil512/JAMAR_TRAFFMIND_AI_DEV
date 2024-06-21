import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO
from streamlit_drawable_canvas import st_canvas

# Function to handle the URL modification
def get_modified_background_image_url(background_image_url: str):
    base_url_path = st._config.get_option("server.baseUrlPath").strip("/")
    if base_url_path:
        base_url_path = "/" + base_url_path
    return base_url_path + background_image_url

# Background image URL
background_image_url = "https://www.crowsonlaw.com/wp-content/webp-express/webp-images/uploads/2023/11/right-of-way-rules.jpg.webp"

# Load background image
response = requests.get(background_image_url)
bg_image = Image.open(BytesIO(response.content))

# Modify the background image URL if necessary
modified_image_url = get_modified_background_image_url(background_image_url)

# Create a canvas component
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
    stroke_width=3,  # Fixed stroke width
    stroke_color="rgba(0, 0, 255, 1)",  # Fixed stroke color
    background_color="#eee",  # Fixed background color
    background_image=bg_image,
    update_streamlit=True,  # Always update in real time
    height=400,
    width=600,
    drawing_mode="line",  # Always in line drawing mode
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
