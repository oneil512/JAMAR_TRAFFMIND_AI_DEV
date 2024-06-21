import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO
from streamlit_drawable_canvas import st_canvas

# Upload image file
uploaded_file = st.file_uploader("Upload a background image", type=["png", "jpg", "jpeg"])
if uploaded_file:
    bg_image = Image.open(uploaded_file)
else:
    bg_image = None

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
