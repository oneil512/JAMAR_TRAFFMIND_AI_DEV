import boto3
from sqlalchemy import create_engine, text
import pandas as pd
from pytz import timezone
import streamlit as st
import os

region = 'us-east-2'
access_key = os.getenv("AWS_ACCESS_KEY_ID")
secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
connection_string = st.secrets["POSTGRES_CONNECTION_STRING"]

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

def get_s3_status(client):
    try:
        # Create the database engine
        engine = create_engine(connection_string)
        
        # Define your query with a parameter placeholder for client
        query = """
        SELECT "File Name", "Start Time", "End Time", "Duration (hrs)", "Status", "Write Video", "Output Path"
        FROM traffmind
        WHERE "Client" = :client
        ORDER BY "Start Time" DESC;
        """

        # Execute the query and fetch the data into a DataFrame
        with engine.connect() as connection:
            result = connection.execute(text(query), {'client': client})
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        
        # Generate download links for rows with Write Video == True and Status == Completed
        df['Download Link'] = df.apply(
            lambda row: generate_presigned_url(
                f"{row['Output Path']}/{row['File Name'].replace('.mp4', '').replace('.h264', '')}_post_process_tracks.mp4"
            ) if row['Write Video'] and row['Status'] == 'Completed' else None, axis=1
        )
        
        # Select only the required columns for the final DataFrame
        df = df[['File Name', 'Start Time', 'End Time', 'Duration (hrs)', 'Status', 'Download Link']]
        
        return df
    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame(columns=['File Name', 'Start Time', 'End Time', 'Duration (hrs)', 'Status', 'Download Link'])

def show_table_with_links(df):
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
    data_df = get_s3_status('Jamar')
    show_table_with_links(data_df)

if refresh or st.session_state['first_load']:
    try:
        data_df = get_s3_status('Jamar')
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
