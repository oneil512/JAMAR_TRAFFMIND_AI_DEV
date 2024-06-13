import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from lib.aws import list_files_paginated, extract_first_frame, convert_lines_to_vectors, write_vectors_to_s3

# Function to handle button clicks
def handle_click(direction, index):
    st.session_state[f"button_{index}"] = direction

color_map = {
    0: "blue",
    1: "red",
    2: "green",
    3: "white",
    }

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
    fill_color="rgba(255, 0, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color='Black',
    background_color="#eee",
    background_image=st.session_state.get('bg_image', None),
    update_streamlit=True,
    height=480,
    drawing_mode=drawing_mode,
    display_toolbar=True,
    key=st.session_state['bg_video_name'] if st.session_state.get('bg_video_name', False) else "canvas"
)


if canvas_result.json_data is not None and canvas_result.json_data['objects'] != []:
    vectors = convert_lines_to_vectors(canvas_result.json_data['objects'])
    st.session_state['vectors'] = vectors

    for i, (x1, y1, x2, y2) in enumerate(vectors):
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.write(f":blue[{x1, y1, x2, y2}]")
        with col2:
            if col2.button("N", key=f"N_{i}"):
                handle_click("N", i)
        with col3:
            if col3.button("S", key=f"S_{i}"):
                handle_click("S", i)
        with col4:
            if col4.button("E", key=f"E_{i}"):
                handle_click("E", i)
        with col5:
            if col5.button("W", key=f"W_{i}"):
                handle_click("W", i)
    
    # Display the selected direction for each row
    st.write(f"Row {i} selected direction: {st.session_state.get(f'button_{i}', 'None')}")
    if st.button("Save vectors"):
        file_type = st.session_state.get('bg_video_name').split('.')[-1]

        v = {}
        # make a dictionary of directions to vectors
        for i, (x1, y1, x2, y2) in enumerate(vectors):
            v[st.session_state.get(f'button_{i}')] = ((x1, y1), (x2, y2))
        
        write_vectors_to_s3(v, "jamar", f'submissions/{st.session_state.get("bg_video_name").replace("." + file_type, "")}/vectors.txt')



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

