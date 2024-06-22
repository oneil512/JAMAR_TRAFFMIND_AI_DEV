import boto3
import pandas as pd
from pytz import timezone
import streamlit as st
import os

region = 'us-east-2'
access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

def generate_presigned_url(object_s3_uri, expiration=3600):
    s3_client = boto3.client('s3', region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    bucket_name, object_key = object_s3_uri.replace("s3://", "").split("/", 1)
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name, 'Key': object_key},
                                                    ExpiresIn=expiration)
    except Exception as e:
        print(e)
        return None
    return response

import boto3
import pandas as pd
import os
from pytz import timezone

def get_s3_status(tag_key, tag_value, region, access_key, secret_key, job_limit=50):
    sagemaker_client = boto3.client('sagemaker', region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    
    processing_jobs = []
    next_token = None
    
    # Paginate through the list of processing jobs
    while True:
        if next_token:
            response = sagemaker_client.list_processing_jobs(NextToken=next_token)
        else:
            response = sagemaker_client.list_processing_jobs()
        
        processing_jobs.extend(response['ProcessingJobSummaries'])
        next_token = response.get('NextToken')
        
        if not next_token or len(processing_jobs) >= job_limit:
            break
    
    # Limit the jobs to the first 50 if more than 50 were fetched
    processing_jobs = processing_jobs[:job_limit]
    
    filtered_jobs = []
    
    for job in processing_jobs:
        job_name = job['ProcessingJobName']
        
        # Get the tags for the processing job
        tags_response = sagemaker_client.list_tags(ResourceArn=job['ProcessingJobArn'])
        tags = tags_response['Tags']
        
        # Check if the tag exists
        for tag in tags:
            if tag['Key'] == tag_key and tag['Value'] == tag_value:
                job_details = sagemaker_client.describe_processing_job(ProcessingJobName=job_name)
                creation_time = job_details['CreationTime']
                end_time = job_details.get('ProcessingEndTime')
                duration = (end_time - creation_time).total_seconds() / 3600 if end_time else None
                status = job_details['ProcessingJobStatus']
                
                # Extract S3Input for InputName = input_path
                s3_input = None
                for input_item in job_details['ProcessingInputs']:
                    if input_item['InputName'] == 'input_path':
                        s3_input = input_item['S3Input']['S3Uri']
                        break
                
                # Extract only the file name from the S3 URI
                file_name = os.path.basename(s3_input) if s3_input else None

                # Extract S3Output for OutputName = output_video
                s3_output = None
                for output_item in job_details['ProcessingOutputConfig']['Outputs']:
                    if output_item['OutputName'] == 'output_video':
                        s3_output = output_item['S3Output']['S3Uri']
                        break
                
                download_link = None
                if status == 'Completed' and s3_output:
                    output_video_path = f"{s3_output}/{file_name.replace('.mp4', '').replace('.h264', '')}_post_process_tracks.mp4"
                    download_link = generate_presigned_url(output_video_path)
                
                filtered_jobs.append({
                    'File Name': file_name,
                    'Start Time': creation_time,
                    'End Time': end_time,
                    'Duration (hrs)': round(duration, 1) if duration else None,
                    'Status': status,
                    'Download Link': download_link
                })
                break
    
    if not filtered_jobs:
        return pd.DataFrame(columns=['File Name', 'Start Time', 'End Time', 'Duration (hrs)', 'Status', 'Download Link'])

    df = pd.DataFrame(filtered_jobs)
    est = timezone('America/New_York')    
    df['Start Time'] = pd.to_datetime(df['Start Time']).dt.tz_convert(est).dt.strftime('%Y-%m-%d %I:%M %p')
    df.sort_values(by=['Start Time'], ascending=False)
    df['End Time'] = df['End Time'].apply(lambda x: pd.to_datetime(x).tz_convert(est).strftime('%Y-%m-%d %I:%M %p') if pd.notnull(x) else None)
    return df

    
def show_table_with_links(df):
    df['Download Link'] = df['Download Link'].apply(lambda x: f'<a href="{x}" target="_blank">Download</a>' if x is not None else "")
    st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

st.set_page_config(page_title="Traffic Tracker - Processed Videos", layout="wide")

st.header("TraffMind AI Job Status")

st.markdown("""
Welcome to the TraffMind AI Job Status page. Follow the steps below to check the status of your submitted jobs and download processed videos.

**1. Download Video**: Use the main panel to download your processed videos.
""")
refresh = st.button('Refresh Data', key='refresh')

if 'first_load' not in st.session_state:
    st.session_state['first_load'] = True
    data_df = get_s3_status('Client', 'Jamar', region, access_key, secret_key)
    show_table_with_links(data_df)

if 'first_load' not in st.session_state or refresh:
    try:
        data_df = get_s3_status('Client', 'Jamar', region, access_key, secret_key)
        show_table_with_links(data_df)
        st.session_state['first_load'] = False
    except Exception as e:
        st.error(f"No jobs have been submitted yet. Please submit a job to view processed videos.")
        st.stop()

st.markdown("""
**2. Get Job Counts**: Click the button below to view the reports of your submitted jobs.
""")

st.page_link(
    "pages/1_Step 4: Traffic Reports.py",
    label=":blue[Step 4: Traffic Reports]",
    disabled=False
)
