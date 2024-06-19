import streamlit as st
from PIL import Image
import logging
import boto3
import cv2

logger = logging.getLogger(st.__name__)

# AWS configuration
AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
region = 'us-east-2'
bucket_name = "jamar"
prefix = "client_upload/"

st.set_page_config(page_title="TraffMind AI Video Frame Extractor", layout="wide")

st.header("TraffMind AI Video Frame Extractor")

# AWS S3 client
def get_s3_client():
    return boto3.client('s3', region_name=region, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

# Function to list files from S3
@st.cache_data
def list_files_paginated():
    s3_client = get_s3_client()
    paginator = s3_client.get_paginator('list_objects_v2')
    names = []
    
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            names.append(key)

    return [name.split('/')[-1] for name in names]

# Function to extract the first frame from a video
@st.cache_data
def extract_first_frame(key):
    s3_client = get_s3_client()
    url = s3_client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': key}, ExpiresIn=7600)
    cap = cv2.VideoCapture(url)
    ret, frame = cap.read()
    cap.release()
    
    if ret and frame is not None:
        frame = frame[:, :, ::-1]  # Convert BGR to RGB
        return frame
    return None

# Function to convert frame to PIL Image
@st.cache_data
def get_image_from_frame(frame):
    return Image.fromarray(frame)

# Initial load of video names
if 'video_names' not in st.session_state:
    st.session_state['video_names'] = list_files_paginated()

refresh = st.button('Refresh Videos', key='refresh')

if refresh:
    st.session_state['video_names'] = list_files_paginated()

# Dropdown for selecting a video
video_name = st.selectbox("Select a video to extract the first frame", st.session_state['video_names'])

if video_name:
    if 'selected_video_name' not in st.session_state or st.session_state['selected_video_name'] != video_name:
        frame = extract_first_frame(f"{prefix}{video_name}")
        if frame is not None:
            bg_image = get_image_from_frame(frame)
            st.session_state['bg_image'] = bg_image
            st.session_state['selected_video_name'] = video_name

if 'bg_image' in st.session_state:
    st.image(st.session_state['bg_image'], caption=f"First frame of {st.session_state['selected_video_name']}")
else:
    st.write("No image to display.")
