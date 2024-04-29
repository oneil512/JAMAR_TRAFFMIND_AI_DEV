import streamlit as st
import logging
import boto3
from botocore.exceptions import ClientError
import requests
from lib import run
import os

def generate_presigned_url(s3_client, client_method, method_parameters, expires_in):
    """
    Generate a presigned Amazon S3 URL that can be used to perform an action.

    :param s3_client: A Boto3 Amazon S3 client.
    :param client_method: The name of the client method that the URL performs.
    :param method_parameters: The parameters of the specified client method.
    :param expires_in: The number of seconds the presigned URL is valid for.
    :return: The presigned URL.
    """
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod=client_method, Params=method_parameters, ExpiresIn=expires_in
        )
        logger.info("Got presigned URL: %s", url)
    except ClientError:
        logger.exception(
            "Couldn't get a presigned URL for client method '%s'.", client_method
        )
        raise
    return url

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")

st.header("TraffMind AI Job Submission")

# Step 1: Select a video
st.markdown("""
**1. Select a Video**: You can drag and drop or select a video file to upload by clicking the uploader below. Only MP4 and h264 formats are supported.
""")

# File uploader for video selection
uploaded_video = st.file_uploader("Upload your video", type=['mp4', 'h264'])

# Step 2: Submit
st.markdown("""
**2. Submit**: Click the submit button to send your video for processing.
""")

# Submit button
if st.button("Submit", key='submit'):
    if uploaded_video is not None:
        st.sidebar.success("Your submission is received!")
        print(uploaded_video.name)

        # Read keys in from environment variables
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        s3_client = boto3.client(
            "s3",
            region_name='us-east-2',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        url = generate_presigned_url(
            s3_client,
            "put_object",
            {"Bucket": 'traffmind-client-unprocessed-jamar', "Key": uploaded_video.name},
            1000
        )
     
        response = requests.put(url, data=uploaded_video.getvalue())

        if response.status_code == 200:
            run(uploaded_video.name)

    else:
        st.sidebar.error("Please upload a video and provide a name for your submission.")

# Step 3: Check Status
st.markdown("""
**3. Check Status**: Click the following link to check the status of your submission.
""")

st.page_link(
    "pages/1_Step 2: Traffic Tracker.py",
    label=":blue[Step 2: Traffic Tracker]",
    disabled=False
)
