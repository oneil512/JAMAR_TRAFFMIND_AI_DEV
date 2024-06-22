import boto3
import sys
import random
import hashlib
import time
import datetime
import logging
import os

from botocore.exceptions import ClientError

import streamlit

logger = logging.getLogger(streamlit.__name__)


def start_sagemaker_processing_job(infile, machine, environment_variables):
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    datetime_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    
    region = 'us-east-2'
    logger.info(f" starting sagemaker processing job for {infile}")
    VERSION = "1.2.29"

    # Initialize the SageMaker client
    sagemaker_client = boto3.client('sagemaker', region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key)

    # Specify the S3 bucket and file paths
    bucket = "jamar"

    # Specify the S3 bucket and file paths
   
    # This maps model class ids to client facing class names
    # Eg model assigns 0 to motorcycle, but motorcycle is class 1 in 13 bin classification scheme
    class_mapping_path = "s3://traffmind-classifiers/yolov8m-cls-best-20240617-120845/class_mapping.json"
    classifier_model_path = "s3://traffmind-classifiers/yolov8m-cls-best-20240617-120845/model.pt"

    filetype = infile.split('.')[-1]
    base_filename = infile.split('/')[-1].replace(f'.{filetype}', '')
    input_path = f's3://{bucket}/client_upload/{infile}'
    output_path = f's3://{bucket}/outputs/{base_filename}_{datetime_str}'
    tracks_output_path = f'{output_path}/tracks/'

    epoch_time = int(time.time())
    version_number = VERSION.replace(".", "-")

    hash_object = hashlib.md5(infile.encode())
    hash_filename = hash_object.hexdigest()

    VECTORS_PREFIX = f"submissions/{base_filename}"

    #Add vectors prefix to environment variables
    environment_variables["VECTORS_PREFIX"] = VECTORS_PREFIX
    

    # Define the processing job configuration
    processing_job_name = f"fn-{hash_filename}-vn-{version_number}-e-{epoch_time}"
    processing_job_config = {
        'ProcessingJobName': processing_job_name,
        'RoleArn': 'arn:aws:iam::134350563342:role/service-role/AmazonSageMaker-ExecutionRole-20240119T144933',
        'Tags': [{'Key': 'Name', 'Value': base_filename},{'Key': 'FileType', 'Value': filetype}, {'Key': 'Client', 'Value': "Jamar"},{'Key': 'Version', 'Value': version_number}, {'Key': 'Datetime', 'Value': datetime_str}, {'Key': 'Machine', 'Value': machine}],
        'AppSpecification': {
            'ImageUri': f'134350563342.dkr.ecr.us-east-2.amazonaws.com/traffmind:{VERSION}',
        },
        'ProcessingInputs': [{
            'InputName': 'input_path',
            'S3Input': {
                'S3Uri': input_path,
                'LocalPath': '/opt/ml/processing/input',
                'S3DataType': 'S3Prefix',
                'S3InputMode': 'File',
                'S3DataDistributionType': 'FullyReplicated'
            }
        },
        {
            'InputName': 'class_mapping',
            'S3Input': {
                'S3Uri': class_mapping_path,
                'LocalPath': '/opt/ml/processing/class_mapping',
                'S3DataType': 'S3Prefix',
                'S3InputMode': 'File',
                'S3DataDistributionType': 'FullyReplicated'
            }
        },
        {
            'InputName': 'classifier_model',
            'S3Input': {
                'S3Uri': classifier_model_path,
                'LocalPath': '/opt/ml/processing/model',
                'S3DataType': 'S3Prefix',
                'S3InputMode': 'File',
                'S3DataDistributionType': 'FullyReplicated'
            }
        }
        ],
        "ProcessingOutputConfig": {
            "Outputs": [
                {
                "OutputName": "output_video",
                
            "S3Output": {
                "S3Uri": output_path,
                "LocalPath": "/opt/ml/processing/output/",
                "S3UploadMode": "EndOfJob"
            }
        },
        {
            "OutputName": "median_frame",
                
            "S3Output": {
                "S3Uri": output_path,
                "LocalPath": "/opt/ml/processing/median_frame/",
                "S3UploadMode": "EndOfJob"
            }
        },
        {
            "OutputName": "counts",
                
            "S3Output": {
                "S3Uri": output_path,
                "LocalPath": "/opt/ml/processing/counts/",
                "S3UploadMode": "EndOfJob"
            }
        },
        {
            "OutputName": "successful_tracks",
                
            "S3Output": {
                "S3Uri": tracks_output_path,
                "LocalPath": "/opt/ml/processing/all_tracks_objects/",
                "S3UploadMode": "EndOfJob"
            }
        }
        ]
        },
        'Environment': environment_variables,
        'ProcessingResources': {
            'ClusterConfig': {
                'InstanceCount': 1,
                'InstanceType': machine,
                'VolumeSizeInGB': 30
            }
        },
        'StoppingCondition': {
            'MaxRuntimeInSeconds': 3600 * 18
        }
    }

    # Start the processing job
    response = sagemaker_client.create_processing_job(**processing_job_config)
    print(f"Processing job started with ARN: {response['ProcessingJobArn']}")
    return response



def run(infile):
    classifier_yaml_path = "classifier/yolo_cls/yolov8m-cls-6.yaml"
    machine_types = ["ml.p3.2xlarge", "ml.g4dn.8xlarge"]
    while machine_types:
        machine_type = machine_types.pop()
        try:
            start_sagemaker_processing_job(infile, machine_type, {"AWS": "True", "VECTORS_BUCKET": "jamar",  "EVERY": "3", "SHOW_VECTORS": "True", "CLASSIFIER_YAML_PATH": classifier_yaml_path, "IMAGE_CLASSIFIER_PATH": "/opt/ml/processing/model/model.pt", "WRITE_VIDEO": "True", "WRITE_TRACKS": "True", "VECTORS_PATTERN": "vector"})
            break
        except ClientError as e:
            print(e)
            logger.info(f"Failed to start processing job. error: {e}")
        except Exception as e:
            logger.info(f"Failed to start processing job. error: {e}")
            print(e)
            raise
