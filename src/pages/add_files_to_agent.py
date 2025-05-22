import streamlit as st
import openai 
from openai import OpenAI
import os
import time
import sys
from io import BytesIO
if '/workspaces/journal_v1/src/' not in sys.path:
    sys.path.append('/workspaces/journal_v1/src/')
#if '/workspaces/journal_v1/src/pages/' not in sys.path:
#    sys.path.append('/workspaces/journal_v1/src/pages/')

from awsfunc import get_openai_api_key, get_promptops_entries, aws_error_log, get_and_add_learning_components,save_file_ids,delete_file_id,fetch_thread_ids,get_user_episodes
from functions import get_promptops_entries, fetch_static_prompts
from streamlit_session_states import get_session_states
#from learning_functions import *

import yaml

# Load configuration from YAML file
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
#st.session_state.config_path = os.path.join(ROOT_DIR, 'src', 'mapping.yaml')

if 'config_path' not in st.session_state:
    st.session_state.config_path = "error in the file path to mapping.yaml"


client = OpenAI(api_key=get_openai_api_key())

#Session states
# if 'learning_component' not in st.session_state:
#     st.session_state['learning_component'] = "todo"
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if "DEBUG" not in st.session_state:
    st.session_state.DEBUG = False

if "show_as_is" not in st.session_state:
    st.session_state.show_as_is = False

if "summarize_learning_component" not in st.session_state:
    st.session_state.summarize_learning_component = False

if "counter_summarize_learning_component" not in st.session_state:
    st.session_state.counter_summarize_learning_component = 0

# if "summary_of_component" not in st.session_state:
#     st.session_state.summary_of_component = ""

if "increment_counter" not in st.session_state:
    st.session_state.increment_counter = 0

# Get query parameters
try:
    if st.query_params["DEBUG"].lower() == "true":
        st.session_state.DEBUG = True
except KeyError:
    pass


@st.dialog("Add your space to Agent")
def save_file_to_agent():
    st.write("Select the agent to which you want to add the file")
    st.caption("This will add your notes of the space to the selected agent's knowledge base.")
    
    space_name_v1 = st.session_state['space_name']  # learning_component_p
    
    # Load assistant mapping from YAML file
    with open(st.session_state.config_path, 'r') as file:
        assistant_mapping = yaml.safe_load(file)

    # Retrieve assistant names
    assistant_names = list(assistant_mapping['assistants'].keys())

    your_assistant_v1 = st.selectbox(
        'Select your assistant:',
        assistant_names, key='your_assistant'
    )

    your_assistant_id_v1 = assistant_mapping['assistants'].get(your_assistant_v1)

    entries = get_promptops_entries(space_name_v1)
    text_blob = ""
    for entry in entries:
        text_blob += f"Title: {entry['title']}\nDescription: {entry['description']}\n\n"

    try:
        # List all filesclient.
        files_response = client.files.list()
        files = files_response.data  # list of files

        # Check if file with the same name exists
        file_name = f"{space_name_v1}_notes.txt"
        existing_file = next((f for f in files if f.filename == file_name), None)

        # If exists, delete it
        if existing_file:
            st.info("These notes already exist in the agent. Click submit button to save any updates.")
            st.write(f"File ID: {existing_file.id}")

            # Show list of all files
            st.write("### Files in your account:")
            for f in files:
                st.write(f"- {f.filename} (ID: {f.id})")
        
        if st.button("Submit", key='submit_v1'):

            # If exists, delete it
            if existing_file:
                st.info(f"Old file '{file_name}' found. Deleting it...")
                delete_file_id(existing_file.id)
                client.files.delete(existing_file.id)
                st.success(f"Old file '{file_name}' deleted.")

            # Upload new file
            file_like = BytesIO(text_blob.encode('utf-8'))
            file_like.name = file_name

            file_response = client.files.create(
                file=file_like,
                purpose="assistants"
            )
            # Call save_file_ids function before showing success
            save_file_ids(
                file_id=file_response.id,
                assistant_id=your_assistant_id_v1,
                assistant_name=your_assistant_v1,
                file_name=file_name
            )
            # For each thread_id, send a message to the thread with the new file id
            thread_ids = fetch_thread_ids(your_assistant_id_v1)
            for thread_id in thread_ids:
                try:
                    client.beta.threads.messages.create(
                        thread_id=thread_id,
                        role="user",
                        content="Here's a new file I'd like you to consider.",
                        attachments=[
                            {
                                "file_id": file_response.id,
                                "tools": [{"type": "file_search"}]
                            }
                        ]
                    )
                    st.info(f"Message sent to thread: {thread_id}")
                    if st.session_state.DEBUG:
                        st.write(f"Message sent to thread: {thread_id}")
                except Exception as e:
                    st.error(f"Failed to send message to thread {thread_id}: {e}")

            st.success(f"File uploaded successfully! File ID: {file_response.id}")

        # Here you can add logic to associate the file ID with your assistant ID in your own storage if needed.

    except Exception as e:
        st.error(f"Error during upload or association: {e}")
        aws_error_log(e, "save_file_to_agent")

    #######
    
    
#review, and behind button




#add authentication here
st.set_page_config(page_title="Add Files to Agent", page_icon=":guardsman:", layout="wide")
st.title("Add your space to Agent")
st.write(":blue[This page allows you to add notes of your spaces to an agent.]") 
st.write("The files will be processed and added to the agent's knowledge base.")

#copy the prompt page, or add detials there... for eg. add button "save file to agent" or :file already added , or update file        

if st.session_state.authenticated:
    st.write("Select your space")
    learning_component_names = get_and_add_learning_components('get', 'redundant', 'dev')
    learning_component_p = st.selectbox(
        'Select a Learning Component:',
        learning_component_names, key='space_name'
    )

    entries = get_promptops_entries(learning_component_p)

    # Build and save the text blob once in session state
    text_blob = "\n\n".join([
        f"Title: {entry['title']}\nDescription: {entry['description']}" for entry in entries
    ])
    st.session_state.space_text_blob = text_blob

    # Show the notes in the UI
    with st.expander("Your Space Notes", expanded=False):
        for entry in reversed(entries):
            st.subheader(entry['title'])
            st.caption(entry['description'])

    # Allow download of the notes
    st.download_button(
        label="Download Notes as Text File",
        data=st.session_state.space_text_blob,
        file_name=f"{learning_component_p}_notes.txt",
        mime="text/plain"
    )

    # Add to Agent button
    st.button("Add to Agent", key='add_to_agent', type='primary', on_click=save_file_to_agent)
    if st.button("Sync remember-me episodes with Agent", key='sync_episodes'):
        episodes_text_blob = get_user_episodes('dev')
        if episodes_text_blob is not None and episodes_text_blob != "":
            user_id = 'dev'
            files_response_episodes = client.files.list()
            episodes = files_response_episodes.data  # list of files

            # Check if file with the same name exists
            file_name_episodes = f"{user_id}_episodes.txt"
            existing_file_episodes = next((f for f in episodes if f.filename == file_name_episodes), None)


                # If exists, delete it
            if existing_file_episodes:
                st.info(f"Old file '{file_name_episodes}' found. Deleting it...")
                delete_file_id(existing_file_episodes.id)
                client.files.delete(existing_file_episodes.id)
                st.success(f"Old file '{file_name_episodes}' deleted.")

            # Upload new file
            file_like_episodes = BytesIO(episodes_text_blob.encode('utf-8'))
            file_like_episodes.name = file_name_episodes

            file_response = client.files.create(
                file=file_like_episodes,
                purpose="assistants"
            )

            st.success(f"New file '{file_name_episodes}' added.")

            # For each thread_id, send a message to the thread with the new file id
            #only attaching to all threads, but its a user memory, so differentiate on user later
            all_assistants = "all"
            
            thread_ids = fetch_thread_ids(all_assistants)
            for thread_id in thread_ids:
                st.success(f"Thread ID: {thread_id}")
                try:
                #add the file to all the threads in the code
                    client.beta.threads.messages.create(
                        thread_id=thread_id,
                        role="user",
                        content="Here's a new file I'd like you to consider.",
                        attachments=[
                            {
                                "file_id": file_response.id,
                                "tools": [{"type": "file_search"}]
                            }
                        ]
                        )
                    
                    if st.session_state.DEBUG:
                        st.write(f"Message sent to thread: {thread_id}")
                except Exception as e:
                    st.error(f"Failed to send message to thread {thread_id}: {e}")
                st.success(f"File uploaded successfully to C360 threads! File ID: {file_response.id}")
            


else:
    st.write("Please log in to access your spaces.")
    st.page_link("./App.py", label="Log in", icon="🔒")

if st.session_state.DEBUG:
    get_session_states()

   #ask chatgpt,
   # #can i uplod txt file to agent
   # should i save the txt blob as session state, can it be file in sesion state, or where should i save it intermediate before uplaoding
   # should i save in s3
   # save to agent and acknowledge base
   # thants it
   #  