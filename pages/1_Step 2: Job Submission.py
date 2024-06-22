import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw
from io import BytesIO
from streamlit_drawable_canvas import st_canvas
from lib.aws import list_files_paginated, extract_first_frame, convert_lines_to_vectors, write_vectors_to_s3
from lib.sagemaker_processing import run
import base64
import cv2
import os

# Function to handle button clicks
def handle_click(direction, index):
    st.session_state[f"button_{index}"] = direction

# Manage initial load and refresh with session state
if 'vector_names' not in st.session_state:
    names = list_files_paginated("jamar", "client_upload/", file_type='*')
    st.session_state['vector_names'] = [name.split('/')[-1] for name in names]

if 'names_to_vectors' not in st.session_state:
    st.session_state['names_to_vectors'] = defaultdict(list)

@st.cache_data
def get_first_frame(video_name):
    return extract_first_frame("jamar", f"client_upload/{video_name}")

@st.cache_data
def get_image_from_frame(frame):
    return Image.fromarray(frame)

def base64_encode_image(frame):
    _, encoded_frame = cv2.imencode('.png', frame)
    return base64.b64encode(encoded_frame).decode('utf-8')

# Header
st.header("Insight AI Job Submission")

st.markdown("""
Welcome to the Insight AI Job Submission page. Follow the steps below to submit your video processing job:

1. **Select a Video and Draw Vectors**:
    - Choose a video from the dropdown menu below.
    - Use the canvas to draw vectors on the selected video frame. These vectors will be used to track objects in the video.
""")

bg_video_name = st.selectbox("Select a video to draw vectors on", st.session_state['vector_names'], key='video_select')

if bg_video_name:
    if 'bg_video_name' not in st.session_state or st.session_state['bg_video_name'] != bg_video_name:
        frame = get_first_frame(bg_video_name)
        if frame is not None:
            image = get_image_from_frame(frame)
            st.session_state.image_height, st.session_state.image_width = image.size
            st.session_state['bg_image'] = image
            st.session_state['bg_video_name'] = bg_video_name
            st.session_state['canvas_result'] = None  # Clear canvas

if 'bg_image' in st.session_state:
    bg_image = st.session_state['bg_image']
    width, height = bg_image.size

    # Create a canvas component with flexible settings
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=3,  # Fixed stroke width
        stroke_color="Black",  # Black stroke color
        background_image=bg_image,
        update_streamlit=True,  # Always update in real time
        height=height,
        width=width,
        drawing_mode="line",  # Always in line drawing mode
        display_toolbar=True,
        key="canvas",
    )

    st.markdown("""
2. **Label Vectors**:
    - Click the 'Label Vectors' button below to proceed to labeling the directions for each vector.
    """)

    if st.button("Label Vectors"):
        if canvas_result.json_data is not None:
            vectors = convert_lines_to_vectors(canvas_result.json_data['objects'])
            st.session_state['vectors'] = vectors
            st.session_state['names_to_vectors'][bg_video_name] = vectors

    st.markdown("""
3. **Review Labeling**:
    - Review the vectors and their labels in the image preview below.
    """)

    col1, col2 = st.columns([3, 1])
    with col1:
        if 'vectors' in st.session_state and st.session_state['vectors']:
            img = bg_image.copy()
            draw = ImageDraw.Draw(img)
            for (x1, y1, x2, y2) in st.session_state['vectors']:
                draw.line((x1, y1, x2, y2), fill=(255, 0, 0), width=3)  # Red lines

            st.image(img, caption="Review your vectors", width=width)

    with col2:
        if 'vectors' in st.session_state:
            for i, (x1, y1, x2, y2) in enumerate(st.session_state['vectors']):
                st.write(f":blue[Vector {i + 1}]")
                directions_list = ["N", "E", "S", "W"]
                option = st.selectbox(f"Vector {i + 1} Direction", directions_list, key=f"direction_{i}")
                if option:
                    handle_click(option, i)

st.markdown("""
4. **Submit Job**:
    - Once all vectors are drawn and directions are specified, click the 'Submit Job' button to submit your video for processing.
    """)

# Add a button to submit the job
if st.button("Submit Job"):
    if 'vectors' in st.session_state and st.session_state['vectors']:
        vectors = st.session_state['vectors']
        directions = {st.session_state[f"button_{i}"]: vectors[i] for i in range(len(vectors))}
        write_vectors_to_s3(directions, "jamar", f'submissions/{st.session_state["bg_video_name"].replace(".", "_")}/vectors.txt')

        # Run the processing job
        run(st.session_state["bg_video_name"])
        st.success("Job submitted successfully!")
    else:
        st.error("Please draw vectors and specify directions before submitting the job.")
