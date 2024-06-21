import streamlit as st
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Set Streamlit page configuration
st.set_page_config(layout="wide")

# Header
st.header("TraffMind AI Video Upload Using SFTP")


st.markdown("""

You can now upload your videos using an SFTP client such as Cyberduck. Follow the steps below:

1. **Download Cyberduck**:
    - Go to the [Cyberduck website](https://cyberduck.io/download/) and download the version suitable for your operating system.
    - Install Cyberduck following the instructions provided on the website.

2. **Login to SFTP Server**:
    - Open Cyberduck.
    - Click on "Open Connection".
    - Select "SFTP (SSH File Transfer Protocol)" from the dropdown menu.
    - Server: `s-98f5aabd378c4fbf8.server.transfer.us-east-2.amazonaws.com`
    - Username: `sftp-access-s3`
    - Password: Leave this blank.
    - SSH Private Key: Use the private key we provided to you.
    """)

st.image("https://raw.githubusercontent.com/edwardayoub/JAMAR_TRAFFMIND_AI/main/screenshots/traffmind_sftp_login.png", width=600)

st.markdown("""
3. **Upload Your Video**:
    - Once logged in, drag and drop your video file into Cyberduck to upload.
""")

st.image("https://raw.githubusercontent.com/edwardayoub/JAMAR_TRAFFMIND_AI/main/screenshots/traffmind_sftp_files.png", width=600)

# Link to check status
st.markdown("""
**4. Draw Vectors**: Before submitting the job, you can draw vectors on the video to track vehicles.
""")

st.page_link(
    "pages/1_Step 2: Draw Vectors.py",
    label=":blue[Step 2: Draw Vectors]",
    disabled=False
)
