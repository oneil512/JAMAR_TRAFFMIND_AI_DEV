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
import random

logger = logging.getLogger(st.__name__)

# Function to handle button clicks
def handle_click(direction, index):
    st.session_state[f"button_{index}"] = direction

# Set page configuration
st.set_page_config(page_title="TraffMind AI Traffic Counter", layout="wide")

st.header("TraffMind AI Draw Vectors")
stroke_width = 3
drawing_mode = "line"
bg_image = None

# Manage initial load and refresh with session state
if 'vector_names' not in st.session_state:
    names = list_files_paginated("jamar", "client_upload/", file_type='*')
    st.session_state['vector_names'] = [name.split('/')[-1] for name in names]

refresh = st.button('Refresh Videos', key='refresh')

if refresh:
    names = list_files_paginated("jamar", "client_upload/", file_type='*')
    st.session_state['vector_names'] = [name.split('/')[-1] for name in names]

# Dropdown for selecting a background image
bg_video_name = st.selectbox("Select a video to draw vectors on", st.session_state['vector_names'])

@st.cache_data
def get_first_frame(video_name):
    return extract_first_frame("jamar", f"client_upload/{video_name}")

@st.cache_data
def get_image_from_frame(frame):
    return Image.fromarray(frame)

if bg_video_name:
    logger.warning(f"line 44, calling get image from frame: {bg_video_name}")
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
    width = int(fixed_height * aspect_ratio)
    height = fixed_height
else:
    width, height = 800, 800

logger.warning(f"about to draw canvas")
logger.warning(f"bg_image value: {bg_image}")
logger.warning(f"bg_image session state value: {st.session_state.get('bg_image', None)}")
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color='Black',
    background_color="#000000",
    background_image=st.session_state.get('bg_image'),
    update_streamlit=True,
    width=width,
    height=height,
    drawing_mode=drawing_mode,
    display_toolbar=True,
    key=st.session_state['bg_video_name'] + 'canvas' if st.session_state.get('bg_video_name', False) else "canvas"
)

if canvas_result.json_data is not None and canvas_result.json_data['objects'] != []:
    vectors = convert_lines_to_vectors(canvas_result.json_data['objects'])
    st.session_state['vectors'] = vectors

    col1, col2 = st.columns([3, 1])
    with col1:
        if 'vectors' in st.session_state and st.session_state['vectors']:
            img = st.session_state['bg_image'].resize((width, height))
            draw = ImageDraw.Draw(img)
            font_path = os.path.join(cv2.__path__[0], 'qt', 'fonts', 'DejaVuSans.ttf')
            font = ImageFont.truetype(font_path, size=20)

            # Assign unique colors to each vector
            colors = ['#%06X' % random.randint(0, 0xFFFFFF) for _ in range(len(st.session_state['vectors']))]

            for i, (x1, y1, x2, y2) in enumerate(st.session_state['vectors']):
                direction = st.session_state.get(f"button_{i}", "")
                draw.line((x1, y1, x2, y2), fill=colors[i], width=3)
                text_x = (x1 + x2) / 2
                text_y = (y1 + y2) / 2 - 10
                draw.text((text_x, text_y), f"V{i+1}", fill=colors[i], font=font)

            st.image(img, caption="Review your vectors and labels", use_column_width=True)

    with col2:
        if 'vectors' in st.session_state:
            for i, (x1, y1, x2, y2) in enumerate(st.session_state['vectors']):
                st.markdown(f"<span style='color:{colors[i]}'>{i + 1}</span>", unsafe_allow_html=True)
                st.write(f":blue[Vector {i + 1}]")
                directions_list = ["N", "E", "S", "W"]
                option = st.selectbox(f"Vector {i + 1} Direction", directions_list, key=f"direction_{i}")
                if option:
                    handle_click(option, i)

    # Display the selected direction for each row
    if st.button("Save vectors and submit job"):
        file_type = st.session_state.get('bg_video_name').split('.')[-1]

        v = {}
        # Make a dictionary of directions to vectors
        for i, (x1, y1, x2, y2) in enumerate(vectors):
            v[st.session_state.get(f'button_{i}')] = ((x1, y1), (x2, y2))

        write_vectors_to_s3(v, "jamar", f'submissions/{st.session_state.get("bg_video_name").replace("." + file_type, "")}/vectors.txt')

        # Run the processing job
        run(st.session_state.get("bg_video_name"))
        st.write(f"Vectors saved!")
        st.write(f"Job submitted!")

st.markdown("""
**3. Check Status**: Click the following link to check the status of your submission.
""")
st.page_link(
    "pages/1_Step 3: Traffic Tracker and Classifier.py",
    label=":blue[Step 3: Traffic Tracker and Classifier]",
    disabled=False
)
