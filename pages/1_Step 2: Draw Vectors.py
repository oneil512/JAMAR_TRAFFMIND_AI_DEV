import streamlit as st
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
from streamlit_drawable_canvas import st_canvas
from lib.aws import list_files_paginated, extract_first_frame
import base64
import cv2
import draw_lines
from collections import defaultdict

# Function to handle button clicks
def handle_click(direction, index):
    st.session_state[f"button_{index}"] = direction

# Manage initial load and refresh with session state
if 'vector_names' not in st.session_state:
    names = list_files_paginated("jamar", "client_upload/", file_type='*')
    st.session_state['vector_names'] = [name.split('/')[-1] for name in names]

if 'names_to_vectors' not in st.session_state:
    st.session_state['names_to_vectors'] = defaultdict(list)

refresh = st.button('Refresh Videos', key='refresh')

if refresh:
    names = list_files_paginated("jamar", "client_upload/", file_type='*')
    st.session_state['vector_names'] = [name.split('/')[-1] for name in names]

# Dropdown for selecting a background image
bg_video_name = st.selectbox("Select a video to draw vectors on", st.session_state['vector_names'])

@st.cache_data
def get_first_frame(video_name):
    return extract_first_frame("jamar", f"client_upload/{video_name}")

def base64_encode_image(frame):
    _, encoded_frame = cv2.imencode('.png', frame)
    return base64.b64encode(encoded_frame).decode('utf-8')

lines = []

if bg_video_name:
    if 'bg_video_name' not in st.session_state or st.session_state['bg_video_name'] != bg_video_name:
        frame = get_first_frame(bg_video_name)
        if frame is not None:
            image_height, image_width, _ = frame.shape
            st.session_state.image_height = image_height
            st.session_state.image_width = image_width
            st.session_state['bg_image'] = base64_encode_image(frame)
            st.session_state['bg_video_name'] = bg_video_name
            st.session_state['canvas_result'] = None  # Clear canvas

if 'bg_image' in st.session_state:
    bg_image_bytes = base64.b64decode(st.session_state['bg_image'])
    bg_image = Image.open(BytesIO(bg_image_bytes))
else:
    # Load a default background image from URL if no video is selected
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

# Add a button to update Streamlit and print drawn vectors
if st.button("Next"):
    if canvas_result.json_data is not None:
        objects = pd.json_normalize(canvas_result.json_data["objects"])
        for col in objects.select_dtypes(include=["object"]).columns:
            objects[col] = objects[col].astype("str")

        if not objects.empty:
            st.subheader("Updated List of Line Drawings")
            vectors = []
            for _, row in objects.iterrows():
                st.markdown(
                    f'Start coords: ({row["x1"]:.2f}, {row["y1"]:.2f}), End coords: ({row["x2"]:.2f}, {row["y2"]:.2f})'
                )
                vectors.append((row["x1"], row["y1"], row["x2"], row["y2"]))
            
            st.dataframe(objects)
            st.session_state['vectors'] = vectors
            st.session_state['names_to_vectors'][bg_video_name] = vectors

            for i, (x1, y1, x2, y2) in enumerate(vectors):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f":blue[Vector {i + 1}]")
                with col2:
                    directions_list = ["N", "E", "S", "W"]
                    option = None
                    option = st.selectbox(f"Vector {i + 1} Direction", directions_list, key=f"direction_{i}")
                    if option:
                        handle_click(option, i)

# Code to save vectors and submit job would go here if needed
