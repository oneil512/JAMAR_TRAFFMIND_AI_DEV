import streamlit as st
import pandas as pd
import numpy as np
from streamlit_drawable_canvas import st_canvas

# Set up the Streamlit canvas
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
    stroke_width=2,
    stroke_color="rgba(0, 0, 255, 1)",  # Blue color for lines
    background_color="#fff",
    height=400,
    width=600,
    drawing_mode="line",  # Set drawing mode to 'line'
    key="canvas",
)

if canvas_result.json_data is not None:
    df = pd.json_normalize(canvas_result.json_data["objects"])
    if len(df) == 0:
        st.write("No lines drawn.")
    else:
        df["x1"] = df["x1"]
        df["y1"] = df["y1"]
        df["x2"] = df["x2"]
        df["y2"] = df["y2"]

        st.subheader("List of line drawings")
        for _, row in df.iterrows():
            st.markdown(
                f'Start coords: ({row["x1"]:.2f}, {row["y1"]:.2f}), End coords: ({row["x2"]:.2f}, {row["y2"]:.2f})'
            )
