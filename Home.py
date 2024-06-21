# import streamlit as st
# from PIL import Image
# header = st.container()
# header.title("Development Version")
# header.write("""<div class='fixed-header'/>""", unsafe_allow_html=True)

# ### Custom CSS for the sticky header
# st.markdown(
#     """
# <style>
#     div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
#         position: sticky;
#         top: 2.875rem;
#         background-color: red;
#         z-index: 999;
#     }
#     .fixed-header {
#         border-bottom: 1px solid black;
#     }
# </style>
#     """,
#     unsafe_allow_html=True
# )


# col1, col2 = st.columns(2)

# with col1:
#     st.header("Welcome to the TraffMind AI JAMAR Portal")
#     st.write("""
#     This portal is designed to allow JAMAR to get a hands-on experience with TraffMind AI, showcasing state-of-the-art technology in video traffic analysis. Dive into our newest models and explore how advanced AI can transform traffic data into actionable insights, driving efficiency and safety in urban mobility.
#     """)

# with col2:
#     # Load and display an image (ensure the image 'traffmind-jamar.jpg' is in the same directory as your script)
#     image = Image.open('traffmind-jamar.png')
#     st.image(image, use_column_width=True)


import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
from streamlit_drawable_canvas import st_canvas

# Load background image from URL
background_image_url = "https://www.crowsonlaw.com/wp-content/webp-express/webp-images/uploads/2023/11/right-of-way-rules.jpg.webp"
response = requests.get(background_image_url)
bg_image = Image.open(BytesIO(response.content))

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
