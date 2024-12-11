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

from awsfunc import get_openai_api_key, save_new_promptops_entry_to_DB, get_promptops_entries,update_promptops_entry_to_DB,delete_promptops_entry_from_DB, aws_error_log, get_and_add_learning_components
from functions import fetch_and_summarize_entries, generate_image_from_gpt,generate_image_prompt
from streamlit_session_states import get_session_states

client = OpenAI(api_key=get_openai_api_key())

#Session states
# if 'learning_component' not in st.session_state:
#     st.session_state['learning_component'] = "todo"
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'counter' not in st.session_state:
    st.session_state.counter = 0
if "DEBUG" not in st.session_state:
    st.session_state.DEBUG = False

### MAIN STREAMLIT UI STARTS HERE ###
st.set_page_config(
    page_title="My Learning",
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


#functions

#MOdify the entries added in dev/todo
@st.dialog("Modify Topic")
def modify_entry(uuid_promptops,date_promptops,title,description,do_not_stage):
    st.write("Topic:",title)
    modified_input = st.text_area("Edit the description below, Press Command/Ctrl Enter to Apply",value=description,key='modify_text_area_key')
    modified_stage_key = st.checkbox("Do not stage this topic for changes", value=do_not_stage)
    if st.button("Save"):
        update_flag = update_promptops_entry_to_DB(uuid_promptops,date_promptops,modified_input,modified_stage_key)
        time.sleep(2)
        if update_flag:
            st.success("Changes saved successfully.")
            time.sleep(2)
            st.rerun()
        else:
            st.error(f"Failed to save changes, please use DEBUG support")
            if st.session_state.DEBUG:
                with st.sidebar:
                    st.text("Failed at save learning entries update"
                        f"Error Log: {aws_error_log}")
    st.caption(':blue[OG Description]')
    st.caption(description)
    st.write("If you would like to delete the item, confirm deletion by writing 'delete' in the text box below.")
    delete_box = st.text_input("Type 'delete' to confirm deletion and press enter.")
    if(delete_box == "delete"):
        if (delete_promptops_entry_from_DB(uuid_promptops,date_promptops)):
            st.success("Entry deleted successfully.")
            st.session_state.boolean_flag_to_show_topics = True #this is not required, remove it and chekc if it works
            time.sleep(2)
            st.rerun()
        else:
            st.error("Failed to delete entry. Use debug mode to check logs.")
            if st.session_state.DEBUG:
                with st.sidebar:
                    st.text("Failed at delete learning entries"
                        f"Error Log: {aws_error_log}")




if st.session_state.authenticated:
    learning_component_names = get_and_add_learning_components('get','redundant','dev')
    learning_component = st.selectbox(
        'Select a Learning Component:',
        learning_component_names + ['Add New'],key='learning_component'
    )

    if learning_component == 'Add New':
        new_learning_component = st.text_input('Enter a new learning component name:', key='new_learning_component')
        if st.button('Add'):
            if new_learning_component:
                if (get_and_add_learning_components('add',new_learning_component,'dev')):
                    st.success(f'Learning component "{new_learning_component}" added successfully Please select it from the dropdown.')
                    time.sleep(2)
                st.rerun()
            else:
                st.warning('Error Adding a Learning Component: Please use DEBUG mode to check logs.')
                if st.session_state.DEBUG:
                    with st.sidebar:
                        st.text("Failed at adding a new learning component"
                            f"Error Log: {aws_error_log}")

    openai.api_key = get_openai_api_key()



    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        st.header(":gray[Topics for Staging]")
        entries = get_promptops_entries(st.session_state.learning_component)
        for entry in reversed(entries):
            st.subheader(entry['title'],divider="blue")
            if(entry['do_not_stage']):
                st.caption(":old_key:[This will not be staged for changes]")
                st.write(entry['description'])
            else:
                st.write(entry['description'])
            st.button("Modify", key='modify'+entry['uuid_promptops'], on_click=modify_entry, args=(entry['uuid_promptops'],entry['date_promptops'],entry['title'],entry['description'],entry['do_not_stage']))
                
            
        st.caption(":blue[Add a new topic]")
        todo_text_input_widget = st.text_input('topic heading',key='todo_text_input_key'+str(st.session_state.counter)) #value=st.session_state.todo_text_input,
        todo_text_area_widget = st.text_area('topic details |      :blue[Press Ctrl/Cmd Enter to Apply]',key='to_do_text_area_key'+str(st.session_state.counter)) #value=st.session_state.to_do_text_area,
                    
        
        if(st.button('save', type='primary') and len(todo_text_input_widget)>0 and len(todo_text_area_widget)>0):
            if (save_new_promptops_entry_to_DB(todo_text_input_widget,todo_text_area_widget,st.session_state.learning_component)):
                st.success("Topic added successfully.")
                st.session_state.counter += 1
                time.sleep(1)
                st.rerun()
            else:
                st.error("Failed to add topic. Use debug mode to check logs.")
                if st.session_state.DEBUG:
                    with st.sidebar:
                        st.text("Failed at save a new learning entry"
                            f"Error Log: {aws_error_log}")

    #todolist container

    with col_b:

        if (st.button('Summarize Staged Topics',type='primary')):
            st.header("Summary of Topics")
            summary = fetch_and_summarize_entries(st.session_state.learning_component)
            st.write(summary)
            # Create a prompt for image generation
            image_prompt = generate_image_prompt(summary)
            st.write(image_prompt)
            
            # Generate and display the infographic using OpenAI's image generation
            with st.spinner('Generating infographic...'):
                image_url = generate_image_from_gpt(image_prompt)
                st.image(image_url, caption="AI-Generated Topic Relationship Infographic", use_column_width=True)
        
        #  #Create and display the infographic using network X function
        #     with st.spinner('Generating infographic...'):
        #         infographic_buf = create_infographic(summary)
        #         st.image(infographic_buf, caption="Topic Relationship Infographic", use_column_width=True)
        #     else:
        #         st.warning("No topics found in DynamoDB.")
else:
    st.write("Please log in to view your conversation history.")
    st.page_link("./App.py", label="Log in", icon="🔒")

if st.session_state.DEBUG:
    get_session_states()