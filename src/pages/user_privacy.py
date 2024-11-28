import streamlit as st
import yaml
import os
import uuid

#st.title("Project Details")

st.set_page_config(
    page_title="Apps page, can make it dynamic",
    layout="wide"
)

# Load configuration from YAML file
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
config_path = os.path.join(ROOT_DIR, 'src', 'page_config.yaml')
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

#authenticate
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if st.session_state.authenticated:
    st.title(" User Input Details Page ")
    #st.selectbox("Select Section1", list(config.keys()))
    st.session_state.section = st.selectbox("Select Page", config.keys())

    section = st.session_state.section
    #Change the section from the sesison state controlled by admin

    # Display the selected section's details 
    if section in config:
        for expander in config[section].keys():
            with st.expander(f"Details for {config[section][expander]['expander_title']}"):
                st.write("Inside expander")
                for row in config[section][expander].keys():
                    if row == 'expander_title':
                        continue
                    else:
                        if config[section][expander][row]['no_of_cols'] == 1:
                            streamlit_func = config[section][expander][row]['col1']['type']
                            label = config[section][expander][row]['col1']['label']
                            getattr(st, streamlit_func)(label, key=uuid.uuid4())
                            st.write("----------------------")
                        else:
                            cols = st.columns(config[section][expander][row]['no_of_cols'])
                            for col_index, col in enumerate(cols):
                                with col:
                                    streamlit_func = config[section][expander][row][f"col{col_index + 1}"]['type']
                                    label = config[section][expander][row][f"col{col_index + 1}"]['label']
                                    getattr(st, streamlit_func)(label, key=uuid.uuid4())                                
                                    st.write("----------------------")
else:
    st.write("Please log in to view your User Page.")
    st.page_link("./App.py", label="Log in", icon="🔒")