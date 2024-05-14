import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import torch
from torchvision import transforms
import cv2
from ultralytics import RTDETR, YOLO
import supervision as sv
from lib import download_file
import openai
import os
import base64
import requests

device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Set your OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
client = openai.Client(api_key=openai_api_key)

# Download the model file
download_file('traffmind-models', 'rtdetr-l.pt', 'rtdetr-l.pt', region='us-east-1')

# Load the original classification model
class_model_path = './model/yolov8-cls.yaml'
check_point_dir = './model/yolov8n-cls-20240508-002451.pt'

state_dict = torch.load(check_point_dir, map_location=device)
class_model = YOLO(class_model_path)  # Assuming YOLO is a class you have defined or imported
class_model = class_model.model.model
class_model.to(device)
class_model.eval()
class_model.load_state_dict(state_dict)

# Transform and color map
size = 256
transform = transforms.Compose([
    transforms.Resize((size, size)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])
color_map = {
    'bin 1': 'red',
    'bin 2': 'blue',
    'bin 3': 'green',
    'bin 4': 'yellow',
    'bin 5': 'purple',
    'bin 6': 'orange',
    'bin 7': 'pink',
    'bin 8': 'brown',
    'bin 9': 'gray',
    'bin 10': 'cyan',
    'bin 11': 'magenta',
    'bin 12': 'lime',
    'bin 13': 'maroon'
}

def get_class_of_cropped_frame(cropped_frame, model, device):
    pil_image = Image.fromarray(cropped_frame)
    image_tensor = transform(pil_image).unsqueeze(0).to(device)
    with torch.no_grad():
        predictions = model(image_tensor)
    classes = [str(i) for i in range(13)]
    top_class_idx = torch.argmax(predictions, dim=1).item()
    top_class = classes[top_class_idx]
    return top_class

# Utility function to convert OpenCV image to base64
def cv2_to_base64(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode('utf-8')

# Function to get classes of cropped frames using OpenAI
def get_classes_of_cropped_frames_model_B(vehicles_base64):
    api_key = os.getenv("OPENAI_API_KEY")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Create the messages payload
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Classify the vehicles in these images into one of the following categories:\n"
                            "1. Motorcycles (F1)\n"
                            "2. Autos (F2)\n"
                            "3. 2 axle, 4-tire pickups, vans (F3)\n"
                            "4. Buses (F4)\n"
                            "5. 2 axle, 6-tire single-unit trucks (F5)\n"
                            "6. 3 axle single-unit trucks (F6)\n"
                            "7. 4 or more axle single-unit trucks (F7)\n"
                            "8. 4 or less axle vehicles, single-trailer trucks (F8)\n"
                            "9. 5 axle, single-trailer trucks (F9)\n"
                            "10. 6 or more axle, single-trailer trucks (F10)\n"
                            "11. 5 axle multi-trailer trucks (F11)\n"
                            "12. 6 axle multi-trailer trucks (F12)\n"
                            "13. 7 or more axle multi-trailer trucks (F13)\n"
                            "Note that you have to return in the same order as the images using this format without any text: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13\n"
                }
            ]
        }
    ]

    # Add each image to the messages payload
    for vehicle_base64 in vehicles_base64:
        messages[0]["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{vehicle_base64}"
            }
        })

    # Prepare the payload for the API request
    payload = {
        "model": "gpt-4o",
        "messages": messages,
        "max_tokens": 300
    }

    # Send the request to OpenAI API
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    result = response.json()

    # Extract and return only the bin numbers from the response
    bins = []
    if 'choices' in result:
        content = result['choices'][0]['message']['content']
        lines = content.split('\n')[0].split(', ')
        for line in lines:
            bins.append(line.strip())

    return bins

# Function to apply detections to a frame
def apply_detections_to_frame(frame, detections, class_results, model_name):
    pil_frame = Image.fromarray(frame)
    draw = ImageDraw.Draw(pil_frame, 'RGBA')

    # Get bounding box coordinates and class names
    detections_xyxy = detections.xyxy
    detections_class = class_results

    # Iterate over detections and class names
    for det, cls in zip(detections_xyxy, detections_class):
        x1, y1, x2, y2 = det
        # Get color for the class, default to white if class not in map
        box_color = color_map.get(f'bin {cls}', 'white')
        draw.rectangle([x1, y1, x2, y2], outline=box_color, width=3)
        draw.text((x1, y1), f'{model_name}: {cls}', fill=box_color)

    return pil_frame

# Function to detect objects and classify using Model A
def detect_objects_and_classify_model_a(image):
    frame = np.array(image)
    original_frame = frame.copy()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # Load the model and perform detection
    model = RTDETR('rtdetr-l.pt')  # Path to your model
    results = model(frame)[0]
    detections = sv.Detections.from_ultralytics(results)

    # Filter detections and convert to PIL
    detections = detections[(detections['class_name'] == 'car') | (detections['class_name'] == 'truck') | (detections['class_name'] == 'bus') | (detections['class_name'] == 'motorcycle')]
    detections = detections[(detections.confidence > 0.6)]
    
    class_results = []
    for i in range(len(detections.xyxy)):
        det = detections.xyxy[i]
        x1, y1, x2, y2 = map(int, det)  # Convert coordinates to integers
        cropped_frame = frame[y1:y2, x1:x2]
        if detections.data['class_name'][i] == 'motorcycle':
            result = '1'  # Bin 1 for motorcycles
        else:
            result = get_class_of_cropped_frame(cropped_frame, class_model, device)
        class_results.append(result)

    pil_frame = apply_detections_to_frame(original_frame, detections, class_results, 'Model A')
    
    return pil_frame

# Function to detect objects and classify using Model B
def detect_objects_and_classify_model_b(image):
    frame = np.array(image)
    original_frame = frame.copy()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # Load the model and perform detection
    model = RTDETR('rtdetr-l.pt')  # Path to your model
    results = model(frame)[0]
    detections = sv.Detections.from_ultralytics(results)

    # Filter detections and convert to PIL
    detections = detections[(detections['class_name'] == 'car') | (detections['class_name'] == 'truck') | (detections['class_name'] == 'bus') | (detections['class_name'] == 'motorcycle')]
    detections = detections[(detections.confidence > 0.6)]
    
    vehicles = []
    for i in range(len(detections.xyxy)):
        det = detections.xyxy[i]
        x1, y1, x2, y2 = map(int, det)  # Convert coordinates to integers
        cropped_frame = frame[y1:y2, x1:x2]
        vehicle = cv2_to_base64(cropped_frame)
        vehicles.append(vehicle)

    class_results = get_classes_of_cropped_frames_model_B(vehicles)
    pil_frame = apply_detections_to_frame(original_frame, detections, class_results, 'Model B')
    
    return pil_frame

# Streamlit app function
def app():
    st.set_page_config(page_title="Vehicle Detection Interface", layout="wide")
    
    st.header("Vehicle Detection System")
    st.subheader("Detect vehicles in uploaded images using advanced neural networks")

    st.markdown("""
    **Instructions:** Upload an image and the system will detect vehicles and highlight them.
    """)
    # Add text descriptions for bins and colors
    st.markdown(f"""
        <div style="background-color:black; padding:10px;">
        <span style="color:{color_map['bin 1']};">Bin 1: Motorcycles</span>, 
        <span style="color:{color_map['bin 2']};">Bin 2: Autos</span>, 
        <span style="color:{color_map['bin 3']};">Bin 3: 2 axle, 4-tire pickups, vans</span>, 
        <span style="color:{color_map['bin 4']};">Bin 4: Buses</span>, 
        <span style="color:{color_map['bin 5']};">Bin 5: 2 axle, 6-tire single-unit trucks</span>, 
        <span style="color:{color_map['bin 6']};">Bin 6: 3 axle single-unit trucks</span>,
        <span style="color:{color_map['bin 7']};">Bin 7: 4 or more axle single-unit trucks</span>,
        <span style="color:{color_map['bin 8']};">Bin 8: 4 or less axle vehicles, single-trailer trucks</span>,
        <span style="color:{color_map['bin 9']};">Bin 9: 5 axle, single-trailer trucks</span>,
        <span style="color:{color_map['bin 10']};">Bin 10: 6 or more axle, single-trailer trucks</span>,
        <span style="color:{color_map['bin 11']};">Bin 11: 5 axle multi-trailer trucks</span>,
        <span style="color:{color_map['bin 12']};">Bin 12: 6 axle multi-trailer trucks</span>,
        <span style="color:{color_map['bin 13']};">Bin 13: 7 or more axle multi-trailer trucks</span>
        </div>
        """, unsafe_allow_html=True)
                
    # Upload Image
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png"])
    
    # Detect and Display
    if uploaded_file is not None:
        st.markdown("**Detection Results:**")
        if st.button('Detect', key='detect'):
            image = Image.open(uploaded_file)

            # Run both classifiers
            processed_image_a = detect_objects_and_classify_model_a(image)
            processed_image_b = detect_objects_and_classify_model_b(image)
            
            # Display side by side
            col1, col2 = st.columns(2)
            with col1:
                st.image(processed_image_a, caption='Model A: Detected Vehicles', use_column_width=True)
            with col2:
                st.image(processed_image_b, caption='Model B: Detected Vehicles', use_column_width=True)

if __name__ == '__main__':
    app()
