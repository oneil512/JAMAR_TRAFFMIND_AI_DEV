import streamlit as st
import pandas as pd
from PIL import Image
from io import BytesIO
from streamlit_drawable_canvas import st_canvas
from lib.aws import list_files_paginated, extract_first_frame
import base64
import cv2
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

@st.cache_data
def get_first_frame(video_name):
    return extract_first_frame("jamar", f"client_upload/{video_name}")

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
            image_height, image_width, _ = frame.shape
            st.session_state.image_height = image_height
            st.session_state.image_width = image_width
            st.session_state['bg_image'] = base64_encode_image(frame)
            st.session_state['bg_video_name'] = bg_video_name
            st.session_state['canvas_result'] = None  # Clear canvas

if 'bg_image' in st.session_state:
    bg_image_bytes = base64.b64decode(st.session_state['bg_image'])
    bg_image = Image.open(BytesIO(bg_image_bytes))

    # Define colors for vectors
    vector_colors = ["rgba(255, 0, 0, 1)", "rgba(0, 255, 0, 1)", "rgba(0, 0, 255, 1)", "rgba(255, 165, 0, 1)", "rgba(128, 0, 128, 1)"]

    # Create a canvas component with dynamic settings
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=3,  # Fixed stroke width
        stroke_color=vector_colors[0],  # Initial stroke color
        background_image=bg_image,
        update_streamlit=True,  # Always update in real time
        height=st.session_state.image_height,
        width=st.session_state.image_width,
        drawing_mode="line",  # Always in line drawing mode
        display_toolbar=True,
        key="canvas",
    )

    st.markdown("""
2. **Label Vectors**:
    - Click the 'Label Vectors' button below to proceed to labeling the directions for each vector.
    """)

    # Add a button to update Streamlit and show labeling options
    if st.button("Label Vectors"):
        if canvas_result.json_data is not None:
            objects = pd.json_normalize(canvas_result.json_data["objects"])
            for col in objects.select_dtypes(include=["object"]).columns:
                objects[col] = objects[col].astype("str")

            if not objects.empty:
                vectors = []
                for _, row in objects.iterrows():
                    vectors.append((row["x1"], row["y1"], row["x2"], row["y2"]))

                st.session_state['vectors'] = vectors
                st.session_state['names_to_vectors'][bg_video_name] = vectors

                for i, (x1, y1, x2, y2) in enumerate(vectors):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"<span style='color:{vector_colors[i % len(vector_colors)]};'>Vector {i + 1}</span>", unsafe_allow_html=True)
                    with col2:
                        directions_list = ["N", "E", "S", "W"]
                        option = None
                        option = st.selectbox(f"Vector {i + 1} Direction", directions_list, key=f"direction_{i}")
                        if option:
                            handle_click(option, i)

    st.markdown("""
3. **Submit Job**:
    - Once all vectors are drawn and directions are specified, click the 'Submit Job' button to submit your video for processing.
    """)

    # Add a button to submit the job
    if st.button("Submit Job"):
        if 'vectors' in st.session_state and st.session_state['vectors']:
            # Code to save vectors and submit the job for processing goes here
            st.success("Job submitted successfully!")
        else:
            st.error("Please draw vectors and specify directions before submitting the job.")
