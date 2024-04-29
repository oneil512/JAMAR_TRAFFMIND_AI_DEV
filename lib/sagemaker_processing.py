import boto3
import sys
import hashlib
import datetime
import time
from botocore.exceptions import ClientError
import os

import logging
import streamlit

logger = logging.getLogger(streamlit.__name__)

# read keys in from environment variables


def start_sagemaker_processing_job(infile,machine_type, environment_variables):
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    region = 'us-east-2'
    print(f"Starting sagemaker processing job for {infile}")
    logger.info(f" starting sagemaker processing job for {infile}")
    VERSION = "1.0.58"
    datetime_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    # Initialize the SageMaker client
    sagemaker_client = boto3.client('sagemaker', region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    # Specify the S3 bucket and file paths
    bucket = "traffmind-client-unprocessed-jamar"
    out_bucket = "traffmind-client-processed-jamar"

    input_path = f's3://{bucket}/{infile}'
    output_path = f's3://{out_bucket}/{datetime_str}/'

    # epoch
    epoch_time = int(time.time())

    version_number = VERSION.replace(".", "-")

    # hash filename
    hash_object = hashlib.md5(infile.encode())
    hash_filename = hash_object.hexdigest()

    

    # Define the processing job configuration
    processing_job_name = f"fn-{hash_filename}-vn-{version_number}-e-{epoch_time}"
    processing_job_config = {
        'ProcessingJobName': processing_job_name,
        'RoleArn': 'arn:aws:iam::134350563342:role/service-role/AmazonSageMaker-ExecutionRole-20240119T144933',
        'AppSpecification': {
            'ImageUri': f'134350563342.dkr.ecr.us-east-2.amazonaws.com/traffmind:{VERSION}',
        },
        'ProcessingInputs': [{
            'InputName': 'input1',
            'S3Input': {
                'S3Uri': input_path,
                'LocalPath': '/opt/ml/processing/input',
                'S3DataType': 'S3Prefix',
                'S3InputMode': 'File',
                'S3DataDistributionType': 'FullyReplicated'
            }
        }],
        "ProcessingOutputConfig": {
            "Outputs": [{
                "OutputName": "output1",
                
            "S3Output": {
                "S3Uri": output_path,
                "LocalPath": "/opt/ml/processing/output/",
                "S3UploadMode": "EndOfJob"
            }
        },
        {
                "OutputName": "output2",
                
            "S3Output": {
                "S3Uri": output_path,
                "LocalPath": "/opt/ml/processing/median_frame/",
                "S3UploadMode": "EndOfJob"
            }
        }
        ]
        },
        'Environment': environment_variables,
        'ProcessingResources': {
            'ClusterConfig': {
                'InstanceCount': 1,
                'InstanceType': machine_type,
                'VolumeSizeInGB': 1
            }
        },
        'StoppingCondition': {
            'MaxRuntimeInSeconds': 14400
        }
    }

    # Start the processing job
    response = sagemaker_client.create_processing_job(**processing_job_config)
    print(f"Processing job started with ARN: {response['ProcessingJobArn']}")
    return response


def run(infile):
    machine_types = ["ml.c5.xlarge", "ml.c5.2xlarge", "ml.c5.4xlarge", "ml.c5.9xlarge", "ml.c5.18xlarge"]
    while machine_types:
        machine_type = machine_types.pop()
        try:
            start_sagemaker_processing_job(infile, machine_type, {"AWS": "True", "EVERY": "3"})
            break
        except ClientError as e:
            print(e)
            logger.info(f"Failed to start processing job. error: {e}")
        except Exception as e:
            logger.info(f"Failed to start processing job. error: {e}")
            print(e)
            raise
