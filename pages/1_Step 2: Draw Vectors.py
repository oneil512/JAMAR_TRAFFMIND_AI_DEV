import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO
from streamlit_drawable_canvas import st_canvas
import requests
import hashlib

def get_background_image_url(img: Image, key: str):
    """Convert the image to URL and handle server base URL path if needed."""
    image_url = st.image_to_url(
        img, width=None, clamp=True, channels="RGB", output_format="PNG",
        image_id=f"drawable-canvas-bg-{hashlib.md5(img.tobytes()).hexdigest()}-{key}"
    )
    base_url_path = st._config.get_option("server.baseUrlPath").strip("/")
    if base_url_path:
        base_url_path = "/" + base_url_path
    return base_url_path + image_url

# Load background image from URL
background_image_url = "https://www.crowsonlaw.com/wp-content/webp-express/webp-images/uploads/2023/11/right-of-way-rules.jpg.webp"
response = requests.get(background_image_url)
bg_image = Image.open(BytesIO(response.content))

# Convert the background image to URL
background_image_url = get_background_image_url(bg_image, key="full_app")

# Create a canvas component with fixed settings
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
