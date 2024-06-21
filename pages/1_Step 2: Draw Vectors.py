import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
from streamlit_drawable_canvas import st_canvas

# Load background image from URL
background_image_url = "https://www.crowsonlaw.com/wp-content/webp-express/webp-images/uploads/2023/11/right-of-way-rules.jpg.webp"
st.write("Fetching background image...")
response = requests.get(background_image_url)

if response.status_code == 200:
    st.write("Background image fetched successfully.")
    bg_image = Image.open(BytesIO(response.content))
else:
    st.error("Failed to load image from URL")

try:
    # Create a canvas component with a background image
    st.write("Creating canvas...")
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=3,  # Fixed stroke width
        stroke_color="rgba(0, 0, 255, 1)",  # Fixed stroke color
        background_image=bg_image,
        update_streamlit=True,  # Always update in real time
        height=400,
        width=600,
        drawing_mode="line",  # Always in line drawing mode
        display_toolbar=False,
        key="full_app",
    )

    st.write("Canvas created successfully.")
    # Process and display canvas data
    if canvas_result.json_data is not None:
        st.write("Processing canvas data...")
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
    else:
        st.write("No canvas data to process.")
except Exception as e:
    st.error(f"An error occurred: {e}")
