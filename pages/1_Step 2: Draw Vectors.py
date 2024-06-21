import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
from streamlit_drawable_canvas import st_canvas

# Load background image from URL
background_image_url = "https://www.crowsonlaw.com/wp-content/webp-express/webp-images/uploads/2023/11/right-of-way-rules.jpg.webp"
response = requests.get(background_image_url)

# Verify that the image was fetched successfully
if response.status_code == 200:
    bg_image = Image.open(BytesIO(response.content)).convert("RGBA")
    
    # Display the background image
    st.image(bg_image, caption="Background Image for Debugging")

    # Create a canvas component with a transparent background
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=3,  # Fixed stroke width
        stroke_color="rgba(0, 0, 255, 1)",  # Fixed stroke color
        background_color=None,  # Transparent background color
        background_image=None,  # No background image in the canvas itself
        update_streamlit=True,  # Always update in real time
        height=bg_image.height,  # Match the height of the background image
        width=bg_image.width,  # Match the width of the background image
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
else:
    st.error("Failed to load image from URL")
