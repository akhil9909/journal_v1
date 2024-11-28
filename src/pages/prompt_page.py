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
import yaml

client = OpenAI(api_key=get_openai_api_key())


if 'promptops_assistant' not in st.session_state:
    st.session_state['promptops_assistant'] = "Basic"

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False


### MAIN STREAMLIT UI STARTS HERE ###
st.set_page_config(
    page_title="My Prompts",
    layout="wide"
)

# Debugging: Print the sys.path to ensure the correct path is included
#st.write("Current sys.path:", sys.path)

if st.session_state.authenticated:
    promptops_assistant = st.selectbox(
        'Select a promptOps assistant:',
        ("Basic","Rumble"),key='promptops_assistant'
    )


    openai.api_key = get_openai_api_key()

    # Load the assistant mapping from a YAML file
    with open('/workspaces/journal_v1/src/mapping.yaml', 'r') as file:
        assistant_mapping = yaml.safe_load(file)

    # Retrieve the assistant ID based on the selected assistant
    promptops_assistant_id = assistant_mapping['assistants'].get(promptops_assistant)

    #debugging
    # st.write(promptops_assistant_id)
    # st.write(promptops_assistant)
    # st.write(assistant_mapping)

    if not promptops_assistant_id:
        st.write("Please select a valid assistant")

    with st.expander(label='click to see the original_instructions', expanded=False):
        my_assistant = openai.beta.assistants.retrieve(promptops_assistant_id)
        st.caption(my_assistant.instructions)

else:
    st.write("Please log in to view your conversation history.")
    st.page_link("./App.py", label="Log in", icon="🔒")