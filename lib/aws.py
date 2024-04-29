import boto3
import os
import pandas as pd
from pytz import timezone
import hashlib

# read keys in from environment variables
access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

region = 'us-east-2'

def download_file(bucket_name, file_name, path):

    s3_client = boto3.client("s3", region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    print(f"Downloading. bucket: {bucket_name}, file: {file_name}, path: {path}")
    s3_client.download_file(bucket_name, path, file_name)

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

def get_s3_status():

    # Initialize SageMaker client
    sm = boto3.client("sagemaker", region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    jobs = sm.list_processing_jobs()  # List SageMaker processing jobs
    jobs_df = pd.DataFrame(jobs['ProcessingJobSummaries'])
    jobs_df['hash_name'] = jobs_df['ProcessingJobName'].apply(lambda x: x.split('-')[1])
    jobs_df['CreationTime'] = pd.to_datetime(jobs_df['CreationTime'], utc=True)
    jobs_df['ProcessingEndTime'] = pd.to_datetime(jobs_df['ProcessingEndTime'], utc=True)
    jobs_df['LastModifiedTime'] = pd.to_datetime(jobs_df['LastModifiedTime'], utc=True)

    # Initialize S3 client
    s3 = boto3.client("s3", region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)
    unprocessed_files = s3.list_objects_v2(Bucket="traffmind-client-unprocessed-jamar")
    status_df = pd.DataFrame(unprocessed_files['Contents'])
    status_df['hash_name'] = status_df['Key'].apply(lambda x: hashlib.md5(x.encode()).hexdigest())
    status_df['LastModified'] = pd.to_datetime(status_df['LastModified'], utc=True)

    processed_files = s3.list_objects_v2(Bucket="traffmind-client-processed-jamar")
    processed_files_df = pd.DataFrame(processed_files['Contents'])
    processed_files_df['file_path'] = processed_files_df['Key']
    processed_files_df['Key'] = processed_files_df['Key'].apply(lambda x: x.split('/')[1])
    processed_files_df['extension'] = processed_files_df['Key'].apply(lambda x: x.split('.')[1])
    processed_files_df = processed_files_df[processed_files_df['extension'] == 'mp4']
    processed_files_df['Key'] = processed_files_df['Key'].apply(lambda x: x.split('_2024-')[0])
    processed_files_df = processed_files_df[['Key', 'file_path']]

    # Merge DataFrames on hash_name
    merged_df = pd.merge(status_df, jobs_df, on='hash_name', how='left')
    time_difference = merged_df['LastModified'] - merged_df['CreationTime']
    merged_df = merged_df[time_difference.abs() <= pd.Timedelta(minutes=5)]

    # Calculate processing duration in hours and format datetime fields for EST
    merged_df['Duration (hrs)'] = ((merged_df['ProcessingEndTime'] - merged_df['CreationTime']).dt.total_seconds() / 3600).round(1)
    est = timezone('America/New_York')
    merged_df['CreationTime'] = merged_df['CreationTime'].dt.tz_convert(est).dt.strftime('%Y-%m-%d %I:%M %p')
    merged_df['ProcessingEndTime'] = merged_df['ProcessingEndTime'].dt.tz_convert(est).dt.strftime('%Y-%m-%d %I:%M %p')
    merged_df['Key'] = merged_df['Key'].str.replace('.mp4', '', regex=False)
    merged_df['Key'] = merged_df['Key'].str.replace('.h264', '', regex=False)
    merged_df = pd.merge(merged_df, processed_files_df, on='Key', how='left')
    # add download link if Status is Completed
    merged_df['Download Link'] = merged_df.apply(lambda x: generate_presigned_url("traffmind-client-processed-jamar", x['file_path']) if x['ProcessingJobStatus'] == 'Completed' else None, axis=1)

    # Rename columns and filter necessary fields
    merged_df = merged_df.rename(columns={'Key': 'File Name', 'CreationTime': 'Start Time', 'ProcessingEndTime': 'End Time', 'ProcessingJobStatus': 'Status'})
    merged_df = merged_df[['File Name', 'Start Time', 'End Time', 'Duration (hrs)', 'Status', 'Download Link']]
    merged_df.reset_index(drop=True, inplace=True)
    
    return merged_df


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
