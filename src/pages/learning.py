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

from awsfunc import get_openai_api_key, save_new_promptops_entry_to_DB, get_promptops_entries,update_promptops_entry_to_DB,delete_promptops_entry_from_DB, aws_error_log, get_and_add_learning_components,download_and_save_image, fetch_image_metadata, delete_image_metadata,generate_presigned_url
from functions import fetch_and_summarize_entries,generate_image_prompt
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
if 'image_not_saved' not in st.session_state:
    st.session_state.image_not_saved = True
if 'learning_component_linked' not in st.session_state:
    st.session_state.learning_component_linked = None
if 'summarized_topics' not in st.session_state:
    st.session_state.summarized_topics = None
if 'image_alt_text_values' not in st.session_state:
    st.session_state.image_alt_text_values = []

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
    if st.checkbox("I Want to change the space for this note", value=False):    
        change_learning_component_names = get_and_add_learning_components('get','redundant','dev')
        changed_learning_component = st.selectbox(
            'select the new space for this note:',
            change_learning_component_names,key='changed_learning_component'
        )
    else:
        changed_learning_component = st.session_state.learning_component
    if title == "#":
        modified_title = "#"
    else:
        modified_title = st.text_input("Topic Heading",value=title,key='modify_text_input_key')

    modified_input = st.text_area("Edit the description below, Press Command/Ctrl Enter to Apply",value=description,key='modify_text_area_key')
    modified_stage_key = st.checkbox("Do not stage this note for Visuals", value=do_not_stage)
    if st.button("Save"):
        update_flag = update_promptops_entry_to_DB(uuid_promptops,date_promptops,modified_input,modified_stage_key,modified_title,changed_learning_component)
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
        'Select your space:',
        learning_component_names + ['Add New'],key='learning_component'
    )

    if learning_component == 'Add New':
        new_learning_component = st.text_input(':blue[Enter your new space name:]', key='new_learning_component')
        new_learning_component_description = st.text_area(':blue[What is this about? Is this space about work, a book, a lecture or something else?]', key='new_learning_component_description')
        if st.button('Add'):
            if new_learning_component:
                if (get_and_add_learning_components('add',new_learning_component,'dev')):
                    if new_learning_component_description:
                        try:
                            save_new_promptops_entry_to_DB("#",new_learning_component_description,new_learning_component)
                            st.success(f'Learning component "{new_learning_component}" added successfully Please select it from the dropdown.')
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            aws_error_log = aws_error_log + f"Error adding description: {e}"
                            st.error(f"Error adding description: please use DEBUG mode to check logs.")
                            if st.session_state.DEBUG:
                                with st.sidebar:
                                    st.text("Failed at adding a new learning component description"
                                        f"Error Log: {aws_error_log}")
                    else:
                        st.error("Please provide a description for the new learning component.")
            else:
                st.warning('Error Adding a Learning Component: Please use DEBUG mode to check logs.')
                if st.session_state.DEBUG:
                    with st.sidebar:
                        st.text("Failed at adding a new learning component"
                            f"Error Log: {aws_error_log}")

    openai.api_key = get_openai_api_key()


    #st.session_state.promptops_entries = get_promptops_entries(st.session_state.learning_component)
    hash_entry = get_promptops_entries(st.session_state.learning_component)
    for entry in reversed(hash_entry):
        if "#" in entry['title']:
            st.markdown("#### :blue[*About your space!*]")
            st.write(entry['description'],divider="blue")
            st.button("Edit", key='edit' + entry['uuid_promptops'], on_click=modify_entry, args=(entry['uuid_promptops'], entry['date_promptops'], entry['title'], entry['description'], entry['do_not_stage']))
            st.divider()
            

    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        st.header(":gray[Add your notes]")
        entries = get_promptops_entries(st.session_state.learning_component)
        for entry in reversed(entries):
            if "#" not in entry['title']:
                st.subheader(entry['title'], divider="blue")
                if entry['do_not_stage']:
                    st.caption(":old_key:[This will not be staged for changes]")
                    st.write(entry['description'])
                else:
                    st.write(entry['description'])
                st.button("Modify", key='modify' + entry['uuid_promptops'], on_click=modify_entry, args=(entry['uuid_promptops'], entry['date_promptops'], entry['title'], entry['description'], entry['do_not_stage']))
                
            
        #st.caption(":blue[Add a new topic]")
        todo_text_input_widget = st.text_input('Title',key='todo_text_input_key'+str(st.session_state.counter)) #value=st.session_state.todo_text_input,
        todo_text_area_widget = st.text_area('Details |      :blue[Press Ctrl/Cmd Enter to Apply]',key='to_do_text_area_key'+str(st.session_state.counter)) #value=st.session_state.to_do_text_area,
                    
        
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

        if (st.button('Visualize your notes',type='primary')):
            st.header("Summary of your notes")
            summary = fetch_and_summarize_entries(st.session_state.learning_component)
            st.session_state.summarized_topics = summary
            #st.write("Raw response:", summary)
            # Create a prompt for image generation
            #image_prompt = generate_image_prompt(summary)
            #st.session_state.image_alt_text_value = image_prompt
            # Generate and display the infographic using OpenAI's image generation
            with st.spinner('Generating infographic...'):
                st.session_state.image_urls, image_alt_texts = generate_image_prompt(summary)
                st.session_state.image_alt_text_values = image_alt_texts
                st.session_state.image_not_saved = True
                st.session_state.learning_component_linked = st.session_state.learning_component
        #added in try block because st.session_state.learning_component_linked is not initialized

        # if st.session_state.summarized_topics:
        #     with st.expander(":green[*Summary of your notes*]", expanded=False):
        #         st.caption(f":blue[{st.session_state.summarized_topics}]") 
        #         #write a function to save the summary to the database, but a generic function rather than a specific one

        if st.session_state.image_not_saved:
            if 'image_urls' in st.session_state and st.session_state.learning_component_linked == st.session_state.learning_component:
                for image_url, image_alt_text_value in zip(st.session_state.image_urls, st.session_state.image_alt_text_values):
                    st.session_state.image_url = image_url
                    st.session_state.image_alt_text_value = image_alt_text_value
                    st.image(st.session_state.image_url, caption="AI-Generated Topic Relationship Infographic", use_column_width=True)
                    with st.expander("Notes for this image"):
                        st.caption(f"{st.session_state.image_alt_text_value}")
                    
                    if download_and_save_image(st.session_state.image_url, st.session_state.learning_component, 'dev',st.session_state.image_alt_text_value, st.session_state.summarized_topics):
                        st.success("downloading and saving images")
                        #keep a session state as True, and update ot False on any error here, in each iteration of loop, just and to previou state, 
                        # so false is captured and you show st.error in th end before setting the image saved session state to false
                    else:
                        if st.session_state.DEBUG:
                            with st.sidebar:
                                st.text("Failed at save image"
                                    f"Error Log: {aws_error_log}")
                with st.expander("Clustering raw data"):
                    st.caption(f"{st.session_state.summarized_topics}")
                
                st.session_state.image_not_saved = False
                    #show this only when debug is on

        #the save should disappear after saved, used logic on not error``
        st.subheader("Saved Images")
        image_metadata = fetch_image_metadata(st.session_state.learning_component,'dev')
        for image in reversed(image_metadata):
            signed_url = generate_presigned_url(image)
            st.image(signed_url, caption=image, use_column_width=True)
            if st.button("Delete", key="delete_image"+image, on_click=delete_image_metadata, args=({image})):
                time.sleep(2)
                st.rerun()

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