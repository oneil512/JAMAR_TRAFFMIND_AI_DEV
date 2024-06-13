import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from lib.aws import list_files_paginated, extract_first_frame

st.set_page_config(page_title="TraffMind AI Traffic Counter", layout="wide")

drawing_mode ="line"

st.header("TraffMind AI Traffic Counter")

# Manage initial load and refresh with session state
if 'first_load' not in st.session_state:
    names = list_files_paginated("traffmind-client-unprocessed-jamar-dev","", file_type='mp4')
    st.session_state['first_load'] = True
    st.session_state['names'] = names

refresh = st.button('Refresh Videos', key='refresh')


# Dropdown for selecting a background image
bg_video_name = st.selectbox("Select a video to draw vectors on", st.session_state['names'])

# Set page configuration
stroke_width = 3

bg_image = None
canvas_result = None

if (st.session_state.get('bg_video_name', False) != bg_video_name) or not st.session_state.get('bg_image', False):
    print(f"Extracting first frame from {bg_video_name}")
    print(f"{bg_video_name}, {st.session_state.get('bg_image_shown', False)}")
    frame = extract_first_frame("traffmind-client-unprocessed-jamar-dev", bg_video_name)
    bg_image = Image.fromarray(frame)
    st.session_state['bg_image'] = bg_image
    st.session_state['bg_video_name'] = bg_video_name

    # clear the canvas
    st.session_state['canvas_result'] = None

canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
    stroke_width=stroke_width,
    stroke_color="c30010",
    background_color="#eee",
    background_image=st.session_state.get('bg_image', None),
    update_streamlit=True,
    height=480,
    drawing_mode=drawing_mode,
    display_toolbar=True,
    key=st.session_state['bg_video_name'] if st.session_state.get('bg_video_name', False) else "canvas"
)

if canvas_result.json_data is not None:
    st.session_state['canvas_result'] = canvas_result.json_data
    print(canvas_result.json_data)
    # objects = pd.json_normalize(canvas_result.json_data["objects"]) # need to convert obj to str because PyArrow
    # for col in objects.select_dtypes(include=['object']).columns:
    #     objects[col] = objects[col].astype("str")
    # st.dataframe(objects)


# Auto-refresh on the initial load or when the refresh button is pressed
if 'first_load' not in st.session_state or refresh:
    try:
        names = list_files_paginated("traffmind-client-unprocessed-jamar-dev","", file_type='mp4')
        st.session_state['names'] = names
        st.session_state['first_load'] = False
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.error(f"No jobs have been submitted yet. Please submit a job to view processed videos.")
        st.stop()
