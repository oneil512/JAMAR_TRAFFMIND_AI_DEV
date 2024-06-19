import streamlit as st
from PIL import Image
import boto3
import os
import pandas as pd
import requests
import json
import hashlib
import time
import datetime
import plotly.graph_objects as go
from botocore.exceptions import ClientError
from lib.aws import list_files_paginated, extract_first_frame, convert_lines_to_vectors, write_vectors_to_s3
from lib.sagemaker_processing import run

st.set_page_config(page_title="TraffMind AI Traffic Counter", layout="wide")

st.header("TraffMind AI Draw Vectors")

names = list_files_paginated("jamar", "client_upload/", file_type='*')
if st.button('Refresh Videos', key='refresh'):
    names = list_files_paginated("jamar", "client_upload/", file_type='*')

names = [name.split('/')[-1] for name in names]

bg_video_name = st.selectbox("Select a video to draw vectors on", names)

@st.cache_data
def get_first_frame(video_name):
    return extract_first_frame("jamar", f"client_upload/{video_name}")

@st.cache_data
def get_image_from_frame(frame):
    return Image.fromarray(frame)

if bg_video_name:
    frame = get_first_frame(bg_video_name)
    if frame is not None:
        bg_image = get_image_from_frame(frame)

if bg_image:
    fig = plotly_draw_vectors(frame)
    st.plotly_chart(fig)

if st.button("Save vectors and submit job"):
    drawn_shapes = st.session_state['drawn_shapes']
    vectors = convert_lines_to_vectors(drawn_shapes)
    
    file_type = bg_video_name.split('.')[-1]
    v = {}
    for i, (x1, y1, x2, y2) in enumerate(vectors):
        v[st.session_state.get(f'button_{i}')] = ((x1, y1), (x2, y2))
    
    write_vectors_to_s3(v, "jamar", f'submissions/{bg_video_name.replace("." + file_type, "")}/vectors.txt')
    run(bg_video_name)
    st.write("Vectors saved!")
    st.write("Job submitted!")
