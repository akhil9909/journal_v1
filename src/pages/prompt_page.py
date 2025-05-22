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
from functions import structure_assistant_instructions, preview_add_notes_function

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

if "counter_summarize_learning_component" not in st.session_state:
    st.session_state.counter_summarize_learning_component = 0

if "summary_of_component" not in st.session_state:
    st.session_state.summary_of_component = ""

if "increment_counter" not in st.session_state:
    st.session_state.increment_counter = 0

if "preview_add_notes" not in st.session_state:
    st.session_state.preview_add_notes = False

if "show_notes_added_output" not in st.session_state:
    st.session_state.show_notes_added_output = False

if "notes_category" not in st.session_state:
    st.session_state.notes_category = ""

if "increment_add_notes_counter" not in st.session_state:
    st.session_state.increment_add_notes_counter = 0

if "show_added_notes_counter" not in st.session_state:
    st.session_state.show_added_notes_counter = 0

if "preview_added_notes" not in st.session_state:
    st.session_state.preview_added_notes = ""

if "notes_delta" not in st.session_state:
    st.session_state.notes_delta = ""

if "notes_added_original_checkbox" not in st.session_state:
    st.session_state.notes_added_original_checkbox = False

if "show_added_notes" not in st.session_state:
    st.session_state.show_added_notes = False

if "show_all_notes" not in st.session_state:
    st.session_state.show_all_notes = ""

### MAIN STREAMLIT UI STARTS HERE ###
st.set_page_config(
    page_title="Your Assistants",
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
#st.session_state.config_path = os.path.join(ROOT_DIR, 'src', 'mapping.yaml')

if 'config_path' not in st.session_state:
    st.session_state.config_path = "error in the file path to mapping.yaml"

@st.dialog("Format or Modify Instructions")
def modify_instructions(promptops_assistant_id,instructions):
    if st.button("Format or Structure Instructions",help="Click to format or structure the instructions in a clear concise manner"):
        try:
            structured_instructions = structure_assistant_instructions(instructions)
            st.success("Review and copy-paste Structured Instructions below!")
            st.write(structured_instructions)
        except Exception as e:
            st.error(f"Error structuring instructions: {e}")
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
    
def reset_session_states_for_buttons():
    st.session_state.show_as_is = False
    st.session_state.summarize_learning_component = False
    st.session_state.increment_counter = 0
    st.session_state.counter_summarize_learning_component = 0

if st.session_state.authenticated:
    openai.api_key = get_openai_api_key()

    # Load the assistant mapping from a YAML file
    with open(st.session_state.config_path, 'r') as file:
        assistant_mapping = yaml.safe_load(file)

    # Retrieve the assistant names from the YAML file
    assistant_names = list(assistant_mapping['assistants'].keys())

    promptops_assistant = st.selectbox(
        'Select your assistant:',
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
            st.session_state.instructions = my_assistant.instructions

            if st.button("modify", key="modify_instructions", help="Click to modify the instructions"):
                modify_instructions(promptops_assistant_id, my_assistant.instructions)
        except:
            st.write("Please select a valid assistant")
    

    with st.expander(label='Explore your notes', expanded=(st.session_state.show_as_is or st.session_state.summarize_learning_component)):
        learning_component_names = get_and_add_learning_components('get','redundant','dev')
        learning_component_p = st.selectbox(
            'Select a Learning Component:',
            learning_component_names,key='random1122',on_change=reset_session_states_for_buttons
        )
        if st.button("Show as is",key="random123",type="primary"):
            st.session_state.show_as_is = True
        
        if st.session_state.show_as_is:
            entries = get_promptops_entries(learning_component_p)
            for entry in reversed(entries):
                st.write(entry['title'],divider="blue")
                st.caption(entry['description'])
            if st.button(":blue[hide or reset]", key="random444"):
                st.session_state.show_as_is = False
                st.rerun()
        
        st.divider()

        if st.button("Summarize key points",key="random789",type="primary"):
            st.session_state.summarize_learning_component = True
            st.session_state.increment_counter = st.session_state.counter_summarize_learning_component + 1

        if st.session_state.summarize_learning_component:
            if st.session_state.increment_counter > st.session_state.counter_summarize_learning_component:
                entries = get_promptops_entries(learning_component_p)
                # Concatenate all titles and descriptions into a single input text
                input_text = "\n\n".join(
                    f"Title: {entry['title']}\nDescription: {entry['description']}"
                    for entry in entries
                )
                st.session_state.show_all_notes = input_text

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

                    st.session_state.summary_of_component = response.choices[0].message.content.strip()
                    
                except Exception as e:
                    st.error(f"Error generating summary: {e}")
                
            st.session_state.counter_summarize_learning_component = st.session_state.increment_counter
            
            st.write("#### Summary of "+ learning_component_p + " :")
            st.write(st.session_state.summary_of_component)
            if st.button(":blue[hide & reset]", key="random4444"):
                st.session_state.summarize_learning_component = False
                st.rerun()
            st.divider()
            preview_add_notes = st.toggle("Preview - Add your notes to the above instructions", value=False, key="preview_add_notes_mode_toggle", label_visibility="visible")
            if preview_add_notes:
                st.session_state.preview_add_notes = True
            else:
                st.session_state.preview_add_notes = False

            if st.session_state.preview_add_notes:
                notes_category = st.selectbox(
                    'My notes are additional ___ that I would like to add to my instructions:',
                    ['learnings', 'context', 'notes', 'ideas', 'thoughts', 'feedback','suggestions','instructions'],
                    key='notes_category_123'
                )

                st.session_state.notes_added_original_checkbox = st.checkbox("I want to add my original non-summarized notes to the assistant instructions", value=False, key="random_checkbox_123", label_visibility="visible")
                if st.session_state.notes_added_original_checkbox:
                    st.session_state.notes_delta = st.session_state.show_all_notes
                else:
                    st.session_state.notes_delta = st.session_state.summary_of_component


                if st.button("run", key="random3333", type="primary"):
                    st.session_state.show_notes_added_output = True
                    st.session_state.notes_category = notes_category
                    st.session_state.increment_add_notes_counter = st.session_state.show_added_notes_counter + 1
                
                if st.session_state.show_notes_added_output:
                    if st.session_state.increment_add_notes_counter > st.session_state.show_added_notes_counter:
                        st.session_state.show_added_notes_counter = st.session_state.increment_add_notes_counter
                        st.session_state.preview_added_notes = preview_add_notes_function(st.session_state.instructions, st.session_state.notes_category, st.session_state.notes_delta)
                        st.write(st.session_state.preview_added_notes)
                    else:
                        st.write(st.session_state.preview_added_notes)
                    
                    if st.button(":blue[hide & reset]", key="random5555"):
                        st.session_state.show_notes_added_output = False
                        st.session_state.increment_add_notes_counter = 0
                        st.session_state.show_added_notes_counter = 0
                        st.session_state.preview_added_notes = ""
                        st.rerun()
                    st.divider()


    if st.button("double click to reset",key='random4455'):
        st.session_state.show_as_is = False
        st.session_state.summarize_learning_component = False
        st.session_state.show_notes_added_output = False
        st.rerun()
else:
    st.write("Please log in to view your conversation history.")
    st.page_link("./App.py", label="Log in", icon="🔒")

if st.session_state.DEBUG:
    get_session_states()