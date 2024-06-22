import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from streamlit_drawable_canvas import st_canvas
from lib.aws import list_files_paginated, extract_first_frame, convert_lines_to_vectors, write_vectors_to_s3
from lib.sagemaker_processing import run
import base64
import cv2
from collections import defaultdict
import os
import logging

logger = logging.getLogger(st.__name__)

# Function to handle button clicks
def handle_click(direction, index):
    st.session_state[f"button_{index}"] = direction

# Manage initial load and refresh with session state
if 'vector_names' not in st.session_state:
    names = list_files_paginated("jamar", "client_upload/", file_type='*')
    st.session_state['vector_names'] = [name.split('/')[-1] for name in names]

st.set_page_config(page_title="Insight AI Job Submission", layout="wide")

# Header
st.header("Insight AI Job Submission")

st.markdown("""
Welcome to the Insight AI Job Submission page. Follow the steps below to submit your video processing job:

1. **Select a Video and Draw Vectors**:
    - Choose a video from the dropdown menu below.
    - Use the canvas to draw vectors on the selected video frame. These vectors will be used to track objects in the video.
""")

# Dropdown for selecting a background image
bg_video_name = st.selectbox("Select a video to draw vectors on", st.session_state['vector_names'])

@st.cache_data
def get_first_frame(video_name):
    return extract_first_frame("jamar", f"client_upload/{video_name}")

@st.cache_data
def get_image_from_frame(frame):
    return Image.fromarray(frame)

if bg_video_name:
    if 'bg_video_name' not in st.session_state or st.session_state['bg_video_name'] != bg_video_name:
        frame = get_first_frame(bg_video_name)
        if frame is not None:
            bg_image = get_image_from_frame(frame)
            st.session_state['bg_image'] = bg_image
            st.session_state['bg_video_name'] = bg_video_name
            st.session_state['canvas_result'] = None  # Clear canvas

if 'bg_image' in st.session_state:
    bg_image = st.session_state['bg_image']
    width, height = bg_image.size
    fixed_height = 400
    aspect_ratio = width / height
    canvas_width = int(fixed_height * aspect_ratio)
    canvas_height = fixed_height
else:
    canvas_width, canvas_height = 800, 400

# Create a canvas component with fixed settings
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=3,  # Fixed stroke width
    stroke_color='rgba(255, 0, 0, 1)',  # Red stroke color
    background_image=bg_image,
    update_streamlit=True,  # Always update in real time
    height=canvas_height,
    width=canvas_width,
    drawing_mode="line",  # Always in line drawing mode
    display_toolbar=True,
    key=st.session_state['bg_video_name'] + 'canvas' if st.session_state.get('bg_video_name', False) else "canvas"
)

if canvas_result.json_data is not None and canvas_result.json_data['objects'] != []:
    vectors = convert_lines_to_vectors(canvas_result.json_data['objects'])
    st.session_state['vectors'] = vectors

    for i, (x1, y1, x2, y2) in enumerate(vectors):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f":blue[Vector {i + 1}]")
        with col2:
            directions_list = ["N", "S", "E", "W"]
            option = st.selectbox(f"Vector {i + 1} Direction", directions_list, key=f"direction_{i}")
            if option:
                handle_click(option, i)
                
    st.markdown("""
    3. **Review Labeling**:
        - Review the vectors and their labels in the image preview below.
    """)

    col1, col2 = st.columns([3, 1])
    with col1:
        if 'vectors' in st.session_state and st.session_state['vectors']:
            img = bg_image.copy()
            draw = ImageDraw.Draw(img)
            font_path = os.path.join(cv2.__path__[0], 'qt', 'fonts', 'DejaVuSans.ttf')
            font = ImageFont.truetype(font_path, size=20)  # Adjust font size as needed

            for i, (x1, y1, x2, y2) in enumerate(st.session_state['vectors']):
                direction = st.session_state.get(f"button_{i}", "")
                draw.line((x1, y1, x2, y2), fill=(255, 0, 0), width=3)  # Red lines
                text_x = (x1 + x2) / 2
                text_y = (y1 + y2) / 2 - 10  # Position the text above the center of the line
                draw.text((text_x, text_y), direction, fill=(0, 0, 0), font=font)  # Black text

            st.image(img, caption="Review your vectors and labels", use_column_width=True)

    with col2:
        if 'vectors' in st.session_state:
            for i, (x1, y1, x2, y2) in enumerate(st.session_state['vectors']):
                st.write(f":blue[Vector {i + 1}]")
                directions_list = ["N", "E", "S", "W"]
                option = st.selectbox(f"Vector {i + 1} Direction", directions_list, key=f"direction_{i}")
                if option:
                    handle_click(option, i)

    if st.button("Save vectors and submit job"):
        file_type = st.session_state.get('bg_video_name').split('.')[-1]

        v = {}
        for i, (x1, y1, x2, y2) in enumerate(vectors):
            v[st.session_state.get(f'button_{i}')] = ((x1, y1), (x2, y2))

        write_vectors_to_s3(v, "jamar", f'submissions/{st.session_state.get("bg_video_name").replace("." + file_type, "")}/vectors.txt')

        run(st.session_state.get("bg_video_name"))
        st.write("Vectors saved!")
        st.write("Job submitted!")

st.markdown("""
**4. Check Status**: Click the following link to check the status of your submission.
""")
st.page_link(
    "pages/1_Step 3: Traffic Tracker and Classifier.py",
    label=":blue[Step 3: Traffic Tracker and Classifier]",
    disabled=False
)
