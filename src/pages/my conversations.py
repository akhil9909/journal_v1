
import boto3
from boto3.dynamodb.conditions import Key
from awsfunc import fetch_conversations
import streamlit as st
from streamlit_session_states import get_session_states

if 'DEBUG' not in st.session_state:
    st.session_state.DEBUG = False

#get query parameters
try:
    if st.query_params["DEBUG"].lower() == "true":
        st.session_state.DEBUG = True
except KeyError:
    pass

def load_session_state(thread_id, log,selected_assistant):
    st.write("Navigating to the App page...")
    st.session_state.thread_id = thread_id
    st.session_state.LOG = log
    st.session_state.main_called_once = True
    st.session_state.assistant = selected_assistant
    st.switch_page("./App.py") # error here, page link also not working
    #Memory in session state is not needed as it is not used in the App page, remove it
    #not workking
    #add authg first


def display_conversations():
    conversations = fetch_conversations()
    
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