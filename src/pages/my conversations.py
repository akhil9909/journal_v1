#the root directory (ROOT_DIR) is defined explicity in the code, not imported from cached_functions.py
#in App.py it is imported from cached_functions.py since its outside of the pages folder
import boto3
from boto3.dynamodb.conditions import Key
from awsfunc import fetch_conversations
import streamlit as st
from streamlit_session_states import get_session_states
import time
import yaml
import os


if 'DEBUG' not in st.session_state:
    st.session_state.DEBUG = False

#get query parameters
try:
    if st.query_params["DEBUG"].lower() == "true":
        st.session_state.DEBUG = True
except KeyError:
    pass

# Load configuration from YAML file
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
st.session_state.config_path = os.path.join(ROOT_DIR, 'src', 'mapping.yaml')

if 'config_path' not in st.session_state:
    st.session_state.config_path = "error in the file path to mapping.yaml"

def load_session_state(thread_id, log,selected_assistant):
    with open(st.session_state.config_path, 'r') as file:
        assistant_mapping = yaml.safe_load(file)
    st.write("Navigating to the App page...")
    st.session_state.thread_id = thread_id
    st.session_state.LOG = log
    st.session_state.main_called_once = True
    st.session_state.files_attached = True # you dont want the conversation to attach the file when it goes to app.py
    st.session_state.assistant = selected_assistant
    for key, value in assistant_mapping['assistants'].items():
        if value == st.session_state.assistant:
            st.session_state.promptops_assistant = key
    if st.session_state.DEBUG:
        st.warning("uploading session states of selected conversation, sleep 10")
        get_session_states()
        time.sleep(10)
    st.switch_page("./App.py") # error here, page link also not working
    #Memory in session state is not needed as it is not used in the App page, remove it
    #not workking
    #add authg first


def display_conversations():
    conversations = fetch_conversations()
    # Load assistant mappings from the YAML file
    
    st.title("_:blue[My Journals History]_")
    st.write("------")
    col_1, col_2, col_3 = st.columns(3)
    with col_1:
        st.subheader(":gray[Date]")
    with col_2:
        st.subheader(":gray[Journal Entry]")
    with col_3:
        st.subheader(":gray[Actions]")

    for conversation in conversations:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(conversation['date'])
        with col2:
            st.write(conversation['prompt'])
        with col3:
            if st.button(":blue[View Conversation]", key="c"+conversation['thread_id']):
                load_session_state(conversation['thread_id'], conversation['history'], conversation['assistant'])

        #can i put the "1" emoi as part of loop

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if st.session_state.authenticated:
    display_conversations()
else:
    st.write("Please log in to view your conversation history.")
    st.page_link("./App.py", label="Log in", icon="🔒")

if st.session_state.DEBUG:
    get_session_states()