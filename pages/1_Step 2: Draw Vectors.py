import base64
import io
import os
from dataclasses import dataclass
from hashlib import md5

import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import streamlit.elements.image as st_image
from PIL import Image
import requests

# Component declaration
_RELEASE = True  # on packaging, pass this to True

if not _RELEASE:
    _component_func = components.declare_component(
        "st_canvas",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("st_canvas", path=build_dir)

@dataclass
class CanvasResult:
    image_data: np.array = None
    json_data: dict = None

def _data_url_to_image(data_url: str) -> Image:
    """Convert DataURL string to the image."""
    _, _data_url = data_url.split(";base64,")
    return Image.open(io.BytesIO(base64.b64decode(_data_url)))

def _resize_img(img: Image, new_height: int = 700, new_width: int = 700) -> Image:
    """Resize the image to the provided resolution."""
    h_ratio = new_height / img.height
    w_ratio = new_width / img.width
    img = img.resize((int(img.width * w_ratio), int(img.height * h_ratio)))
    return img

def get_background_image_url(img: Image, key: str):
    """Convert the image to URL and handle server base URL path if needed."""
    image_url = st_image.image_to_url(
        img, width=None, clamp=True, channels="RGB", output_format="PNG",
        image_id=f"drawable-canvas-bg-{md5(img.tobytes()).hexdigest()}-{key}"
    )
    base_url_path = st._config.get_option("server.baseUrlPath").strip("/")
    if base_url_path:
        base_url_path = "/" + base_url_path
    return base_url_path + image_url

def st_canvas(
    fill_color: str = "#eee",
    stroke_width: int = 20,
    stroke_color: str = "black",
    background_color: str = "",
    background_image: Image = None,
    update_streamlit: bool = True,
    height: int = 400,
    width: int = 600,
    drawing_mode: str = "freedraw",
    initial_drawing: dict = None,
    display_toolbar: bool = True,
    point_display_radius: int = 3,
    key=None,
) -> CanvasResult:
    """Create a drawing canvas in Streamlit app. Retrieve the RGBA image data into a 4D numpy array (r, g, b, alpha)
    on mouse up event.
    """
    background_image_url = None
    if background_image:
        background_image = _resize_img(background_image, height, width)
        background_image_url = get_background_image_url(background_image, key)

        background_color = ""

    initial_drawing = (
        {"version": "4.4.0"} if initial_drawing is None else initial_drawing
    )
    initial_drawing["background"] = background_color

    component_value = _component_func(
        fillColor=fill_color,
        strokeWidth=stroke_width,
        strokeColor=stroke_color,
        backgroundColor=background_color,
        backgroundImageURL=background_image_url,
        realtimeUpdateStreamlit=update_streamlit and (drawing_mode != "polygon"),
        canvasHeight=height,
        canvasWidth=width,
        drawingMode=drawing_mode,
        initialDrawing=initial_drawing,
        displayToolbar=display_toolbar,
        displayRadius=point_display_radius,
        key=key,
        default=None,
    )
    if component_value is None:
        return CanvasResult

    return CanvasResult(
        np.asarray(_data_url_to_image(component_value["data"])),
        component_value["raw"],
    )

# Streamlit app implementation
background_image_url = "https://www.crowsonlaw.com/wp-content/webp-express/webp-images/uploads/2023/11/right-of-way-rules.jpg.webp"
response = requests.get(background_image_url)
bg_image = Image.open(BytesIO(response.content))

canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
    stroke_width=3,  # Fixed stroke width
    stroke_color="rgba(0, 0, 255, 1)",  # Fixed stroke color
    background_color="#eee",  # Fixed background color
    background_image=bg_image,
    update_streamlit=True,  # Always update in real time
    height=400,
    width=600,
    drawing_mode="line",  # Always in line drawing mode
    display_toolbar=False,
    key="full_app",
)

if canvas_result.json_data is not None:
    objects = pd.json_normalize(canvas_result.json_data["objects"])
    for col in objects.select_dtypes(include=["object"]).columns:
        objects[col] = objects[col].astype("str")

    if not objects.empty:
        st.subheader("List of line drawings")
        for _, row in objects.iterrows():
            st.markdown(
                f'Start coords: ({row["x1"]:.2f}, {row["y1"]:.2f}), End coords: ({row["x2"]:.2f}, {row["y2"]:.2f})'
            )
    st.dataframe(objects)
