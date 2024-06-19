import boto3
import os
import pandas as pd
import requests
import json
import logging
import streamlit as st

logger = logging.getLogger(st.__name__)


# read keys in from environment variables
access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
discord_webhook_url = os.getenv("WEBHOOK_URL")
region = 'us-east-2'

def download_file(bucket_name, key, local_path):

    s3_client = boto3.client("s3", region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    print(f"Downloading. bucket: {bucket_name}, key: {key}, local_path: {local_path}")
    s3_client.download_file(bucket_name, key, local_path)

def list_files(bucket_name, prefix, file_type='*'):
    
    s3 = boto3.client("s3", region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    response = s3.list_objects_v2(Bucket=bucket_name)

    files = []
    for obj in response.get('Contents', []):
        if file_type == '*':
            files.append(obj['Key'])
        elif obj['Key'].endswith(file_type):
            files.append(obj['Key'])

    return files

def list_files_paginated(bucket_name, prefix, file_type='*'):

    s3_client = boto3.client('s3')
    paginator = s3_client.get_paginator('list_objects_v2')

    names = []
    
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            if type(file_type) is list:
                for ft in file_type:
                    if key.endswith(ft):
                        names.append(key)
            elif file_type == '*' or key.endswith(file_type):
                # get presigned url
                names.append(key)

    return names


import boto3
from botocore.exceptions import ClientError
import logging

def generate_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object.

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    # Generate a presigned URL for the S3 object
    s3_client = boto3.client("s3", region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    return response

def send_discord_notification(file_name, file_size_mb, title, description, color):
    webhook_url = discord_webhook_url  # Make sure to define your Discord webhook URL
    data = {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color,
            "fields": [
                {"name": "File Name", "value": file_name, "inline": False},
                {"name": "Size", "value": f"{file_size_mb:.2f} MB", "inline": False}
            ],
            "footer": {
                "text": "Streamlit App Notification"
            }
        }],
        "username": "TraffMind AI"
    }
    response = requests.post(
        webhook_url, data=json.dumps(data),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 204:
        raise Exception(f"Request to Discord returned an error {response.status_code}, the response is:\n{response.text}")



def convert_lines_to_vectors(lines_json):
    vectors = []
    for line in lines_json:
        center_x = line['left']
        center_y = line['top']

        x1 = line['x1']
        y1 = line['y1']
        x2 = line['x2']
        y2 = line['y2']

        # transform into proper coordinates
        x1 = x1 + center_x
        y1 = y1 + center_y

        x2 = x2 + center_x
        y2 = y2 + center_y

        vectors.append((x1, y1, x2, y2))

    return vectors

def write_vectors_to_s3(vectors, bucket, key):
    l = []
    print(f"Writing vectors to S3: {bucket}/{key}")
    s3_client = boto3.client('s3')
    for direction,point_pair in vectors.items():
        l.append(f"{int(point_pair[0][0])},{int(point_pair[0][1])},{direction}")
        l.append(f"{int(point_pair[1][0])},{int(point_pair[1][1])},{direction}")

    out = "\n".join(l)

    s3_client.put_object(Body=out, Bucket=bucket, Key=key)




def extract_first_frame(bucket, key):
    import cv2

    from botocore.config import Config

    my_config = Config(
        signature_version = 's3v4',
    )

    s3_client = boto3.client('s3', region_name="us-east-2", aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    logger.warning("generating presigned url")
    
    # Generate a pre-signed URL to access the video
    url = s3_client.generate_presigned_url('get_object', 
                                           Params={'Bucket': bucket, 'Key': key}, 
                                           ExpiresIn=7600)

    logger.warning(f"presigned url: {url}")
    # Use OpenCV to capture the first frame
    logger.warning(f"capturing video from {url}")
    cap = cv2.VideoCapture(url)
    ret, frame = cap.read()
    cap.release()
    logger.warning(f"frame is not None: {frame is not None}")

    # convert to RGB from BGR without opencv, just permute the channels

    if ret and frame is not None:
        frame = frame[:, :, ::-1]
        return frame
    else:
        logger.warning(f'Failed to capture video from {url}')
        return None
