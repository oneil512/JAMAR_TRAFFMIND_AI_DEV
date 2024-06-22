import streamlit as st
from lib.aws import list_files_paginated, download_file
import pandas as pd

# Set page configuration
st.set_page_config(page_title="TraffMind AI Traffic Counter", layout="wide")

st.header("TraffMind AI Traffic Counter")

# Manage initial load and refresh with session state
if 'first_load' not in st.session_state or 'names' not in st.session_state or 'name_to_key' not in st.session_state:
    name_to_key = {}
    names = list_files_paginated("jamar","outputs/", file_type='txt')
    # get just file names
    name_to_key = {name.split('/')[-1]: name for name in names}

    # filter out keys that have 'crosswalk' in them
    names = [name for name in names if 'crosswalk' not in name]


    names = [name.split('/')[-1] for name in names]
    st.session_state['first_load'] = True
    st.session_state['names'] = names
    st.session_state['name_to_key'] = name_to_key

refresh = st.button('Refresh Counts', key='refresh')

# Dropdown for selecting counts file
count_file_name = st.selectbox("Select a count file", st.session_state.get('names', []))

if count_file_name:
    # download the file from s3
    if not st.session_state.get('name_to_key', False):
        st.rerun()

    key = st.session_state['name_to_key'][count_file_name]
    download_file("jamar", key, count_file_name)

    minute_increment = 15


    count_file_path = count_file_name
    try:
        with open(count_file_path, 'r') as f:

            movement_dict_list = eval(f.readlines()[0])
            # remove empty dicts from list
            movement_dict_list = [x for x in movement_dict_list if x]
            # remove index column

            rows = []

            for i, movement_dict in enumerate(movement_dict_list):
                for class_number in range(1, 7):
                    if class_number == 1:
                        row = {'From': f"{minute_increment * i} min", 'To': f"{minute_increment * (i + 1)} min",'class': class_number}
                    else:
                        row = {'From': '', 'To': '', 'class': class_number}
                    for feature, counts_dict in movement_dict.items():
                        row[feature] = counts_dict.get(class_number, 0)
                    rows.append(row)
            final_df = pd.DataFrame(rows)

            # convert na to 0
            final_df = final_df.fillna(0)
            # convert all columns except From and To to int
            for col in final_df.columns:
                if col not in ['From', 'To']:
                    final_df[col] = final_df[col].astype(int)

            n_rows = final_df.shape[0]

            st.dataframe(final_df.style.hide(axis="index"), hide_index=True, height = int(35.2*(n_rows+1)), width=1000)
    except Exception as e:
        st.error(f"Error loading counts file: {e}")



