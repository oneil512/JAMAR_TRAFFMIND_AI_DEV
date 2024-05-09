import os
import streamlit as st 
from PIL import Image, ImageOps
import numpy as np
from io import BytesIO
import tensorflow as tf
import cv2

# Function to preprocess the image for the model
def preprocess_image_for_prediction(image):
    # Read the image in grayscale mode
    temp_image = np.array(image.convert('L'))
    edges = cv2.Canny(temp_image, 150, 300)
    shape = np.shape(edges)
    left = np.sum(edges[0:shape[0] // 2, 0:shape[1] // 2])
    right = np.sum(edges[0:shape[0] // 2, shape[1] // 2:])

    if right > left:
        sky_side = 0
    else:
        sky_side = 1

    base_height = 400
    wpercent = (base_height / float(image.size[1]))
    wsize = int((float(image.size[0]) * float(wpercent)))
    image = image.resize((wsize, base_height), Image.Resampling.LANCZOS)
    
    if image.size[0] >= image.size[1]:
        if sky_side == 0:
            image = image.crop((0, 0, base_height, image.size[1]))
        else:
            image = image.crop((image.size[0] - base_height, 0, image.size[0], image.size[1]))
    else:
        base_width = 400
        wpercent = (base_width / float(image.size[0]))
        hsize = int((float(image.size[1]) * float(wpercent)))
        image = image.resize((base_width, hsize), Image.Resampling.LANCZOS)
        image = image.crop((0, 0, image.size[0], 400))

    image = ImageOps.invert(image)
    image = image.resize((100, 100), Image.Resampling.LANCZOS)
    img_array = np.array(image) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    return img_array
def app():
    st.set_page_config(page_title="Keras Prediction Interface", layout="wide")
    
    st.header("TraffMind AI Weather Detector")
    st.subheader("Beta 1 - Use images with visible sky for better accuracy")

    st.markdown("""
    **Welcome to the TraffMind AI Image Classifier!** This tool uses advanced neural networks to predict weather conditions from images. For best accuracy, please use images that include a portion of the sky. Follow the steps below to upload your image and receive predictions:
    """)
    
    # Step 1: Upload Image
    st.markdown("""
    **1. Upload Image**: Drag and drop or select an image file for prediction. Supported format: JPEG.
    """)
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg"])
    
    # Step 2: Identify and Predict
    if uploaded_file is not None:
        st.markdown("""
        **2. Identify and Predict**: Click 'Identify' to process and predict the weather condition in your image.
        """)
        if st.button('Identify', key='identify'):
            # Step 3: Results
            st.markdown("""
            **3. Results**: View the image and its predicted condition below.
            """)
            image = Image.open(uploaded_file)
            st.write("Identifying...")
            preprocessed_image = preprocess_image_for_prediction(image)
            model_path = "./model/traffmind_weather_beta1.h5"
            loaded_model = tf.keras.models.load_model(model_path)
            predictions = loaded_model.predict(preprocessed_image)
            classes = ['Cloudy', 'Sunny', 'Rainy', 'Snowy', 'Foggy']
            prediction = classes[np.argmax(predictions)]
            st.write('Prediction: %s' % (prediction))
            st.image(image, caption='Uploaded Image.', use_column_width=False)


if __name__=='__main__':
    app()
