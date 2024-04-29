import streamlit as st
from PIL import Image
from lib import download_file, list_files

st.set_page_config(layout="wide")

# Simulated mapping of submission names to background image files.
# Replace these with your actual data.

bucket = "traffmind-client-processed-jamar"

# Example list of processed videos - this list is empty to simulate the current situation
background_images = list_files(bucket, '*', 'png')  # Update this with actual processed videos once available

# Introduction and user guidance
st.markdown("""
Explore the power of our background detection technology. This feature allows you to see the extracted background from your previously submitted videos. Here’s how to view your backgrounds:
""")
st.markdown("""
1. **Select Your Submission**: Use the dropdown menu in the side panel to select one of your previous submissions.
""")

selected_submission = st.selectbox("Previous Submissions", options=background_images)

# Main panel for displaying the background image
st.header("Extracted Background Image")

st.markdown("""
2. **View the Background**: The extracted background image from your selected video will be displayed in the main panel.
""")

# if video selected, display download button, if clicked, download the video
if background_images:
    if selected_submission:
        file_name = selected_submission.split("/")[-1]
        download_file(bucket, file_name, selected_submission)
        with open(file_name, "rb") as file:
            print(f'reading file {file_name}')
            file_bytes = file.read()

        st.download_button(label="Click here to download the background image", data=file_bytes, file_name=selected_submission)


try:

    # Attempt to display the background image
    st.image(file_name, caption=f"Background for {selected_submission}", use_column_width=True)
except Exception as e:
    st.error("The background image for this submission is currently unavailable.")
