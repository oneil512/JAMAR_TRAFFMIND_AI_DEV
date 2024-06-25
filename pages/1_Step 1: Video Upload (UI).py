import streamlit as st
import logging
import boto3
from botocore.exceptions import NoCredentialsError
from lib.aws import send_discord_notification
import os

# Initialize logger
logger = logging.getLogger(__name__)

# Set Streamlit page configuration
st.set_page_config(layout="wide")

# AWS S3 configuration
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET = 'jamar'
UPLOAD_FOLDER = 'client_upload/'

logger.warning("test2")

# Function to upload file to S3
def upload_to_s3(file, bucket, folder, object_name=None):
    if object_name is None:
        object_name = folder + file.name

    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

    try:
        s3_client.upload_fileobj(file, bucket, object_name)
        return True
    except NoCredentialsError:
        return False

# Header
st.header("Insight AI Direct Video Upload")

st.markdown("""
You can now directly upload your videos through this page. Follow the steps below:

1. **Select Video File**:
    - Click on the "Browse files" button below to select the video file from your local device.
    - Supported formats: MP4, H264.
    - Maximum file size: 25 GB.

2. **Upload Video**:
    - After selecting the video file, it will automatically start uploading.
""")

uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "h264"], accept_multiple_files=False)

if uploaded_file is not None:
    if uploaded_file.size > 25 * 1024 * 1024 * 1024:
        st.error("File size exceeds 25 GB limit.")
    else:
        if upload_to_s3(uploaded_file, S3_BUCKET, UPLOAD_FOLDER):
            st.success(f"File {uploaded_file.name} uploaded successfully!")
            file_size_mb = uploaded_file.size / (1024 * 1024)
            send_discord_notification(
                file_name=uploaded_file.name,
                file_size_mb=file_size_mb,
                title="New Video File Uploaded",
                description=f"A new video file has been uploaded to S3 bucket {S3_BUCKET}.",
                color=3066993  # Discord green color
            )
        else:
            st.error("Failed to upload file to S3. Please check your AWS credentials.")

# Link to check status
st.markdown("""
**3. Job Submission**: Once the video is uploaded, submit the job for processing.
""")

st.page_link(
    "pages/1_Step 2: Job Submission.py",
    label=":blue[Step 2: Job Submission]",
    disabled=False)
