import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from streamlit_drawable_canvas import st_canvas
from lib.aws import list_files_paginated, extract_first_frame, convert_lines_to_vectors, write_vectors_to_s3, send_discord_notification
from lib.sagemaker_processing import run
import base64
import cv2
from collections import defaultdict
import os
import json
import requests

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

    canvas_height = st.session_state.image_height
    canvas_width = st.session_state.image_width

    # Create a canvas component with fixed settings
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=3,  # Fixed stroke width
        stroke_color="rgba(255, 0, 0, 1)",  # Red stroke color
        background_image=bg_image,
        update_streamlit=True,  # Always update in real time
        height=canvas_height,
        width=canvas_width,
        drawing_mode="line",  # Always in line drawing mode
        display_toolbar=False,
        key="canvas",
    )

st.markdown("""
2. **Label Vectors**:
    - Click the 'Label Vectors' button below to proceed to labeling the directions for each vector.
""")

if st.button("Label Vectors"):
    if canvas_result.json_data is not None:
        objects = pd.json_normalize(canvas_result.json_data["objects"])
        for col in objects.select_dtypes(include=["object"]).columns:
            objects[col] = objects[col].astype("str")

        if not objects.empty:
            vectors = []
            for _, row in objects.iterrows():
                if row["type"] == "line":
                    left, top, width, height = float(row["left"]), float(row["top"]), float(row["width"]), float(row["height"])
                    center_x = left
                    center_y = top
                    x1 = center_x + float(row["x1"])
                    y1 = center_y + float(row["y1"])
                    x2 = center_x + float(row["x2"])
                    y2 = center_y + float(row["y2"])
                    vectors.append((x1, y1, x2, y2))

            st.session_state['vectors'] = vectors
            st.session_state['names_to_vectors'][bg_video_name] = vectors
        else:
            st.error("No vectors found. Please draw vectors first.")
    else:
        st.error("No vectors found. Please draw vectors first.")

st.markdown("""
3. **Review Labeling**:
    - Review the vectors and their labels in the image preview below.
""")

col1, col2 = st.columns([3, 1])
with col1:
    if 'vectors' in st.session_state and st.session_state['vectors']:
        img = Image.open(BytesIO(bg_image_bytes))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("lib/Arial.ttf", size=50)  # Example using Arial font

        for i, (x1, y1, x2, y2) in enumerate(st.session_state['vectors']):
            draw.line((x1, y1, x2, y2), fill=(255, 0, 0), width=3)
            text_x = (x1 + x2) / 2
            text_y = (y1 + y2) / 2 - 25
            draw.text((text_x, text_y), f"{i + 1}", fill=(255, 255, 255), font=font)  # Draw text in red

        st.image(img, caption="Review your vectors and labels", use_column_width=True)

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

# Add checkbox for video output option
write_video = st.checkbox("Include video output", value=True)

# Add a button to submit the job
if st.button("Submit Job"):
    if 'vectors' in st.session_state and st.session_state['vectors']:
        file_type = st.session_state.get('bg_video_name').split('.')[-1]

        v = {}
        for i, (x1, y1, x2, y2) in enumerate(st.session_state['vectors']):
            v[st.session_state.get(f'button_{i}')] = ((x1, y1), (x2, y2))

        row = {
            "File Name": st.session_state.get("bg_video_name"),
            "Vectors": json.dumps(v),
            "Write Video": write_video,
            "Status": "In Progress",
        }
        
        #upsert_row_to_db(row)
        write_vectors_to_s3(v, "jamar", f'submissions/{st.session_state.get("bg_video_name").replace("." + file_type, "")}/vectors.txt')

        run(st.session_state.get("bg_video_name"), write_video=write_video)
        st.success("Job submitted successfully!")
        
        # Send Discord notification
        send_discord_notification(
            file_name=st.session_state.get("bg_video_name"),
            title="New Job Submitted",
            description=f"A new job has been submitted for the video {st.session_state.get('bg_video_name')}.",
            color=3066993  # Discord green color
        )
    else:
        st.error("Please draw vectors and specify directions before submitting the job.")

# Link to check status
st.markdown("""
**5. Job Status**: Once the job is submitted, check the job status.
""")

st.page_link(
    "pages/1_Step 3: Job Status.py",
    label=":blue[Step 3: Job Status]",
    disabled=False)
