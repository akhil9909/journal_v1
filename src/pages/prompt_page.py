#the root directory (ROOT_DIR) is defined explicity in the code, not imported from cached_functions.py
#in App.py it is imported from cached_functions.py since its outside of the pages folder
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

from awsfunc import get_openai_api_key, get_and_add_learning_components, get_promptops_entries
from streamlit_session_states import get_session_states

import yaml

client = OpenAI(api_key=get_openai_api_key())


if 'promptops_assistant' not in st.session_state:
    st.session_state['promptops_assistant'] = "Basic"

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if "DEBUG" not in st.session_state:
    st.session_state.DEBUG = False

if "explore_components" not in st.session_state:
    st.session_state.explore_components = False

if "show_as_is" not in st.session_state:
    st.session_state.show_as_is = False

if "summarize_learning_component" not in st.session_state:
    st.session_state.summarize_learning_component = False

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

# Load configuration from YAML file
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
st.session_state.config_path = os.path.join(ROOT_DIR, 'src', 'mapping.yaml')

if 'config_path' not in st.session_state:
    st.session_state.config_path = "error in the file path to mapping.yaml"

@st.dialog("Modify Instructions")
def modify_instructions(promptops_assistant_id,instructions):
    new_instructions = st.text_area("Modify Instructions", instructions)
    if st.button("Save Instructions"):
        try:
            openai.beta.assistants.update(
                promptops_assistant_id,
                instructions=new_instructions
            )
            st.success("Instructions updated successfully!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Error updating instructions: {e}")
    

if st.session_state.authenticated:
    openai.api_key = get_openai_api_key()

    # Load the assistant mapping from a YAML file
    with open(st.session_state.config_path, 'r') as file:
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
            if st.button("modify", key="modify_instructions", help="Click to modify the instructions"):
                modify_instructions(promptops_assistant_id, my_assistant.instructions)
        except:
            st.write("Please select a valid assistant")
    

    with st.expander(label='Explore your learnings', expanded=(st.session_state.show_as_is or st.session_state.summarize_learning_component)):
        learning_component_names = get_and_add_learning_components('get','redundant','dev')
        learning_component_p = st.selectbox(
            'Select a Learning Component:',
            learning_component_names,key='random1122'
        )
        if st.button("Show as is",key="random123"):
            st.session_state.show_as_is = True
        
        if st.session_state.show_as_is:
            entries = get_promptops_entries(learning_component_p)
            for entry in reversed(entries):
                st.write(entry['title'],divider="blue")
                st.caption(entry['description'])
        
        if st.button("Sumamrize Key Learnings",key="random789"):
            st.session_state.summarize_learning_component = True

        if st.session_state.summarize_learning_component:
            entries = get_promptops_entries(learning_component_p)
            # Concatenate all titles and descriptions into a single input text
            input_text = "\n\n".join(
                f"Title: {entry['title']}\nDescription: {entry['description']}"
                for entry in entries
            )

            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an assistant that summarizes learning material."},
                        {"role": "user", "content": f"Summarize key learnings and points from the following text data:\n\n{input_text}"}
                    ],
                    max_tokens=500,
                    temperature=0.7,
                )

                summary = response.choices[0].message.content.strip()
                
                st.write("#### Summary of "+ learning_component_p + " :")
                st.write(summary)
            except Exception as e:
                st.error(f"Error generating summary: {e}")

    if st.button("double click to reset",key='random4455'):
        st.session_state.show_as_is = False
        st.session_state.summarize_learning_component = False
else:
    st.write("Please log in to view your conversation history.")
    st.page_link("./App.py", label="Log in", icon="🔒")

if st.session_state.DEBUG:
    get_session_states()