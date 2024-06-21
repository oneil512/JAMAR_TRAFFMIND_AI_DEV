import streamlit as st
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Set Streamlit page configuration
st.set_page_config(layout="wide")

# Header
st.header("Insight AI Direct Video Upload")

st.markdown("""
You can now directly upload your videos through this page. Follow the steps below:

1. **Select Video File**:
    - Click on the "Browse files" button below to select the video file from your local device.
    - Make sure the video file format is supported (e.g., MP4, AVI, MOV).

2. **Upload Video**:
    - After selecting the video file, it will automatically start uploading.
""")

uploaded_file = st.file_uploader("Choose a video file", type=["mp4", "avi", "mov"])

if uploaded_file is not None:
    # Save the uploaded file
    with open(f"./uploaded_videos/{uploaded_file.name}", "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"File {uploaded_file.name} uploaded successfully!")

# Link to check status
st.markdown("""
**3. Job Submission**: Once the video is uploaded, submit the job for processing.
""")

st.markdown('[Step 2: Job Submission](pages/1_Step 2: Job Submission.py)')
