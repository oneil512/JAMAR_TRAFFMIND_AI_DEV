import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import logging
import boto3
from botocore.exceptions import ClientError
from lib.sagemaker_processing import run
import cv2

logger = logging.getLogger(st.__name__)

# AWS configuration
AWS_ACCESS_KEY_ID = st.secrets["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = st.secrets["AWS_SECRET_ACCESS_KEY"]
region = 'us-east-2'
bucket_name = "jamar"
prefix = "client_upload/"

# Function to handle button clicks
def handle_click(direction, index):
    st.session_state[f"button_{index}"] = direction

st.set_page_config(page_title="TraffMind AI Traffic Counter", layout="wide")

st.header("TraffMind AI Draw Vectors")
stroke_width = 3
drawing_mode = "line"
bg_image = None

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

# Initial load of vector names
if 'vector_names' not in st.session_state:
    st.session_state['vector_names'] = list_files_paginated()

refresh = st.button('Refresh Videos', key='refresh')

if refresh:
    st.session_state['vector_names'] = list_files_paginated()

# Dropdown for selecting a background image
bg_video_name = st.selectbox("Select a video to draw vectors on", st.session_state['vector_names'])

if bg_video_name:
    if 'bg_video_name' not in st.session_state or st.session_state['bg_video_name'] != bg_video_name:
        frame = extract_first_frame(f"{prefix}{bg_video_name}")
        if frame is not None:
            bg_image = get_image_from_frame(frame)
            st.session_state['bg_image'] = bg_image
            st.session_state['bg_video_name'] = bg_video_name
            st.session_state['canvas_result'] = None  # Clear canvas

if 'bg_image' in st.session_state:
    bg_image = st.session_state['bg_image']
    width, height = bg_image.size
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

    for i, (x1, y1, x2, y2) in enumerate(vectors):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f":blue[Vector {i + 1}]")
        with col2:
            directions_list = ["N", "S", "E", "W"]
            option = None
            option = st.selectbox(f"Vector {i + 1} Direction", directions_list, key=f"direction_{i}")
            if option:
                handle_click(option, i)

    if st.button("Save vectors and submit job"):
        file_type = st.session_state.get('bg_video_name').split('.')[-1]
        v = {st.session_state.get(f'button_{i}'): ((x1, y1), (x2, y2)) for i, (x1, y1, x2, y2) in enumerate(vectors)}
        
        write_vectors_to_s3(v, "jamar", f'submissions/{st.session_state.get("bg_video_name").replace("." + file_type, "")}/vectors.txt')
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

# Utility functions (add to lib/aws.py or another utility module)

def convert_lines_to_vectors(lines_json):
    vectors = []
    for line in lines_json:
        center_x = line['left']
        center_y = line['top']
        x1 = line['x1'] + center_x
        y1 = line['y1'] + center_y
        x2 = line['x2'] + center_x
        y2 = line['y2'] + center_y
        vectors.append((x1, y1, x2, y2))
    return vectors

def write_vectors_to_s3(vectors, bucket, key):
    s3_client = get_s3_client()
    l = [f"{int(point_pair[0][0])},{int(point_pair[0][1])},{direction}" 
         for direction, point_pair in vectors.items() 
         for _ in (0, 1)]
    out = "\n".join(l)
    s3_client.put_object(Body=out, Bucket=bucket, Key=key)
