import streamlit as st
import openai 
from openai import OpenAI
import os
import time
import sys
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
if '/workspaces/journal_v1/src/' not in sys.path:
    sys.path.append('/workspaces/journal_v1/src/')
#wirte if not exists

from awsfunc import get_openai_api_key
from streamlit_session_states import get_session_states

import yaml

client = OpenAI(api_key=get_openai_api_key())


if 'promptops_assistant' not in st.session_state:
    st.session_state['promptops_assistant'] = "Basic"

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if "DEBUG" not in st.session_state:
    st.session_state.DEBUG = False


### MAIN STREAMLIT UI STARTS HERE ###
st.set_page_config(
    page_title="My Prompts",
    layout="wide"
)

# Get query parameters
try:
    if st.query_params["DEBUG"].lower() == "true":
        st.session_state.DEBUG = True
except KeyError:
    pass

# Debugging: Print the sys.path to ensure the correct path is included
#st.write("Current sys.path:", sys.path)

if st.session_state.authenticated:
    openai.api_key = get_openai_api_key()

    # Load the assistant mapping from a YAML file
    with open('/workspaces/journal_v1/src/mapping.yaml', 'r') as file:
        assistant_mapping = yaml.safe_load(file)

    # Retrieve the assistant names from the YAML file
    assistant_names = list(assistant_mapping['assistants'].keys())

    promptops_assistant = st.selectbox(
        'Select a promptOps assistant:',
        assistant_names, key='promptops_assistant'
    )

    # Retrieve the assistant ID based on the selected assistant
    promptops_assistant_id = assistant_mapping['assistants'].get(promptops_assistant)

    if not promptops_assistant_id:
        st.write("Please select a valid assistant")

    with st.expander(label='click to see the original_instructions', expanded=False):
        try:
            my_assistant = openai.beta.assistants.retrieve(promptops_assistant_id)
            st.caption(my_assistant.instructions)
        except:
            st.write("Please select a valid assistant")

else:
    st.write("Please log in to view your conversation history.")
    st.page_link("./App.py", label="Log in", icon="🔒")

if st.session_state.DEBUG:
    get_session_states()