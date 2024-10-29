import streamlit as st
import openai
import os
import json
from functions import run_assistant, get_chat_history, get_chat_message, auto_save_chat_history
from awsfunc import save_chat_history, get_openai_api_key, get_credentials,save_feedback,aws_error_log
from cached_functions import get_css
import base64
import asyncio
import time
from main import main  # Import the main function
from helper import helpers  # Import the helpers

# Get OpenAI API key from environment variable
#openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = get_openai_api_key()

#initialize Prompt
INITIAL_PROMPT = "User prompt empty"

# Initialize session states
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if "thread_id" not in st.session_state:
    thread = openai.beta.threads.create()
    st.session_state.thread_id = thread.id

if "initial_prompt" not in st.session_state:
    st.session_state.initial_prompt = INITIAL_PROMPT;

if "chat_history" not in st.session_state:
    st.session_state.chat_history = ""

if "chat_history_status" not in st.session_state:
    st.session_state.chat_history_status = "Chat history NOT saved"

if "MEMORY" not in st.session_state:
    st.session_state.MEMORY = [{'role': "system", 'content': INITIAL_PROMPT}]

if "LOG" not in st.session_state:
    st.session_state.LOG = [INITIAL_PROMPT]

if "DEBUG" not in st.session_state:
    st.session_state.DEBUG = False

if "main_called_once" not in st.session_state:
    st.session_state.main_called_once = False

if "input_text" not in st.session_state:
    st.session_state.input_text = ""

if "rerun_trigger_for_updating_session_state" not in st.session_state:
    st.session_state.rerun_trigger_for_updating_session_state = True
    
if "feedback" not in st.session_state:
    st.session_state.feedback = ""

if "other_feedback" not in st.session_state:
    st.session_state.other_feedback = ""

if "feedback_provided" not in st.session_state:
    st.session_state.feedback_provided = False

if "chatbot_response" not in st.session_state:
    st.session_state.chatbot_response = ""

if "assistant" not in st.session_state:
    st.session_state.assistant = ""

if "analysis_mode" not in st.session_state:
    st.session_state.analysis_mode = False

# Get query parameters
try:
    if st.query_params["DEBUG"].lower() == "true":
        st.session_state.DEBUG = True
except KeyError:
    pass




## Helper Functions

def reset_session() -> dict:
    res = {'status': 0, 'message': "Success"}
    st.session_state.LOG = [INITIAL_PROMPT]
    st.session_state.chat_history = ""
    st.session_state.chat_history_status = "Chat history NOT saved"
    st.session_state.MEMORY = [{'role': "system", 'content': INITIAL_PROMPT}]
    st.session_state.main_called_once = False
    st.session_state.input_text = ""
    st.session_state.feedback = ""
    st.session_state.other_feedback = ""
    st.session_state.initial_prompt = INITIAL_PROMPT
    try:
        thread = openai.beta.threads.create()
        st.session_state.thread_id = thread.id
    except Exception as e:
        res['status'] = 1
        res['message'] = f"An error occurred in creating thread in reset session: {e}"
        return res
    return res
    
# Function to add helper text to the textarea
def add_helper_text(helper):
    st.session_state.input_text += " " + helper
    
#pop up to get the user feedback (st.dialog)
@st.dialog("Provide your feedback on the response")
def Feedback():
    st.write(f"Please Provide your feedback on the response")
    if st.session_state.feedback_provided:
        reason = st.multiselect("", ["useful", "too vague", "verbose", "offensive", "like it", "off-topic", "need more details"], default=st.session_state.feedback)
        other_feedback = st.text_input("Other Feedback", value=st.session_state.other_feedback)
    else:
        reason = st.multiselect("", ["useful", "too vague", "verbose", "offensive", "like it", "off-topic", "need more details"])
        other_feedback = st.text_input("Other Feedback")    
    if st.button("Submit"):
        st.session_state.feedback = reason
        st.session_state.other_feedback = other_feedback
        st.session_state.feedback_provided = True
        st.session_state.LOG.append(f"Feedback: (selected) {reason}")
        st.session_state.LOG.append(f"Feedback: (other) {other_feedback}")
        save_feedback(st.session_state.thread_id, st.session_state.assistant, st.session_state.chatbot_response, st.session_state.feedback,st.session_state.other_feedback)
        st.success("Feedback submitted successfully")
        ##auto save chat history if feedbakc sumbitted to enter feedback as part of chat history
        dummy_res = {'status': 0, 'message': "Success"}
        dummy_human_prompt = "dummy human prompt"
        auto_save_chat_history(dummy_res, st.session_state.assistant, INITIAL_PROMPT,True,dummy_human_prompt)
        ####end auto save chat history
        #only keep auto save chat history if feedback is provided, delete other columns update in dynamocdb logic
        time.sleep(1)  # sleep 1 second
        st.rerun()

### MAIN STREAMLIT UI STARTS HERE ###
st.set_page_config(
    page_title="Journal V3 App",
    layout="wide"
)

# Debug area
if st.session_state.DEBUG:
    with st.sidebar:
        st.subheader("Debug area")
        st.write(f"Assistant: {st.session_state.assistant}")
        st.write(f"Thread ID: {st.session_state.thread_id}")
        st.write(f"Initial Prompt: {st.session_state.initial_prompt}")
        st.write(f"Chat History: {st.session_state.chat_history}")
        st.write(f"Chat History Status: {st.session_state.chat_history_status}")
        st.write(f"Memory: {st.session_state.MEMORY}")
        st.write(f"Input Text: {st.session_state.input_text}")
        st.write(f"main_called_once: {st.session_state.main_called_once}")
        st.write(f"Log: {st.session_state.LOG}")
        st.write(f"Debug mode: {st.session_state.DEBUG}")
        st.write(f"Authenticated: {st.session_state.authenticated}")
        st.write(f"Username: {st.session_state.get('username', 'Not set')}")
        st.write(f"Rerun: {st.session_state.get('rerun', False)}")  # Check if rerun flag is set
        st.write(f"AWS error log: {aws_error_log}")
        st.write(f"Feedback: {st.session_state.feedback}")
        st.write(f"Other Feedback: {st.session_state.other_feedback}")
        st.write(f"Analysis mode flag: {st.session_state.analysis_mode}")

# Get available assistants (you'll need to implement this)
if st.session_state.assistant == "":
    assistants = ["asst_V1dqbgYTAdUEAWgBYQmBgVyZ", "No Assistant","asst_XgHiiDliPlsXljgFkSlG3zIG"]  # Replace with your logic
else:
    assistants = [st.session_state.assistant,"asst_V1dqbgYTAdUEAWgBYQmBgVyZ", "No Assistant","asst_XgHiiDliPlsXljgFkSlG3zIG"]  # Replace with your logic

selected_assistant = st.selectbox("Select Assistant", assistants)
st.session_state.assistant = selected_assistant

col1, col2 = st.columns(2)

# Place buttons side by side
with col1:
    if st.button("save chat history") and st.session_state.authenticated:
        if st.session_state.chat_history_status == "Chat history saved":
            st.success("Chat history auto saved")
        else:
            if st.session_state.chat_history == "":
                st.warning("No Chat History to Save")
            elif save_chat_history(st.session_state.thread_id, 
                      st.session_state.assistant, 
                      st.session_state.initial_prompt, 
                      st.session_state.chat_history):
                st.success("Chat history saved")
            else:
                st.error("Failed to save Chat history")
                if st.session_state.DEBUG:
                    with st.sidebar:
                        st.text("Failed at save Chat history button click"
                                f"Error Log: {aws_error_log}")
                

with col2:
    if st.button("New Session") and st.session_state.authenticated:
        reset_ses_variable = reset_session()
        if reset_ses_variable['status'] != 0:
            st.error("Failed to reset session, please check debug mode")
            if st.session_state.DEBUG:
                with st.sidebar:
                    st.text(f"Failed at New Session button click\nError Log: {reset_ses_variable['message']}")
        else:
            st.success("New session initiating")
            time.sleep(1)  # sleep 1 second
            st.rerun()
    
   
   
        

# Define main layout
analysis_mode_on = st.toggle("Analysis Mode", value=False, key="analysis_mode_toggle", label_visibility="visible")
if analysis_mode_on:
    st.write("Analysis Mode is on")
    st.session_state.analysis_mode = True
else:
    st.session_state.analysis_mode = False

st.title(":blue[My Journal v3]")
st.caption("This is a journaling app that uses :blue[OpenAI]'s GPT-3 to assist you in developing your strengths.")
chat_box = st.container()
st.write("")
hint_box = st.container()
feedback_box = st.empty()
prompt_box = st.empty()
footer = st.container()

# Load credentials from aws secret manager, no debug query parameter, directly raises the error in exception
streamlit_secret = get_credentials()
data_dict = json.loads(streamlit_secret)
streamlit_username = data_dict['streamlit_username']
streamlit_password = data_dict['streamlit_password']

# Define login function
def login():
    username = st.session_state["username"]
    password = st.session_state["password"]
    if username == streamlit_username and password == streamlit_password:
        st.session_state.authenticated = True
        st.session_state.rerun = True  # Set rerun flag to True
        st.success("Logged in successfully!")
    else:
        st.error("Invalid username or password")

# Check for rerun flag and rerun the app
if st.session_state.get('rerun', False):
    st.session_state.rerun = False  # Reset rerun flag
    st.rerun()  # Rerun the app outside the callback
    

# Authentication UI
if not st.session_state.authenticated:
    st.subheader("Login")
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password", on_change=login)
    st.button("Login", on_click=login)
    
# with footer:
#     st.markdown("""
#     <div align=right><small>
#     Page views: <img src="https://www.cutercounter.com/hits.php?id=hvxndaff&nd=5&style=1" border="0" alt="hit counter"><br>
#     Unique visitors: <img src="https://www.cutercounter.com/hits.php?id=hxndkqx&nd=5&style=1" border="0" alt="website counter"><br>
#     GitHub <a href="https://github.com/tipani86/CatGDP"><img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/tipani86/CatGDP?style=social"></a>
#     </small></div>
#     """, unsafe_allow_html=True)


# Load CSS code
st.markdown(get_css(), unsafe_allow_html=True)


# Render chat history so far
with chat_box:
    for line in st.session_state.LOG[1:]:
        # For AI response
        if line.startswith("AI: "):
            contents = line.split("AI: ")[1]
            st.markdown(get_chat_message(contents), unsafe_allow_html=True)
        
        if st.session_state.analysis_mode:
            if line.startswith("Feedback: "):
                #contents = line.split("Feedback: ")[1]
                contents = line
                #st.markdown(get_chat_message(contents, align="right"), unsafe_allow_html=True)
                st.write(contents)

        # For human prompts
        if line.startswith("Human: "):
            contents = line.split("Human: ")[1]
            st.markdown(get_chat_message(contents, align="right"), unsafe_allow_html=True)

#add helpers
with hint_box:
    if st.session_state.authenticated:
            if not st.session_state.main_called_once:
                st.write('*********Hints to get started***********')
                cols = st.columns(4)
                for i, helper in enumerate(helpers):
                    col = cols[i % 4]  # Rotate through the 4 columns
                    with col:
                        if st.button(helper):
                            add_helper_text(helper)
                        
with feedback_box:
    if st.session_state.authenticated and st.session_state.main_called_once:
        if st.button("feedback") and not st.session_state.feedback_provided:
            Feedback()
        elif st.session_state.feedback_provided and st.button("edit your feedback"):
            Feedback()

# Define an input box for human prompts
with prompt_box:
    # If authenticated, show the initial prompt
    if st.session_state.authenticated:
        if not st.session_state.main_called_once:
            human_prompt = st.text_area("You: ", value=st.session_state.input_text, height=150) 
            ## BUGALERT i was earlier assigning the key of text_area above as also the session_state = input_text. This was creating a bug where session state was not geting pdated immediately on run click
        else:
            human_prompt =  st.text_input("You: ", value="", key=f"text_input_{len(st.session_state.LOG)}")

if st.session_state.authenticated:
    run_button = st.button("Send", key=f"send_button_{len(st.session_state.LOG)}",type='primary')

if st.session_state.main_called_once:
    hint_box.empty()

# Update the session state with user input from the text area
        #st.session_state.input_text = human_prompt

# Gate the subsequent chatbot response to only when the user has entered a prompt
if st.session_state.authenticated:
    if(run_button) and len(human_prompt) > 0:
        st.session_state.feedback_provided = False
        run_res = asyncio.run(main(human_prompt, st.session_state.assistant))
        #update chat history and rerun the app
        auto_save_chat_history(run_res, st.session_state.assistant, INITIAL_PROMPT,False,human_prompt)
        #note that INITIAL_PROMPT is the a dummy value, its passed to the auto_save_chat_history function to check if the user has entered a prompt or not
        #if the user has entered a prompt, the auto_save_chat_history function will call save_chat_history function with session state log which has user prompt

        

    if st.session_state.main_called_once:
        if(len(human_prompt) > 0):
            st.session_state.feedback_provided = False
            run_res = asyncio.run(main(human_prompt, st.session_state.assistant))
            #update chat history and rerun the app
            auto_save_chat_history(run_res, st.session_state.assistant, INITIAL_PROMPT,True, human_prompt)
            #note that INITIAL_PROMPT is the a dummy value, its passed to the auto_save_chat_history function to check if the user has entered a prompt or not
            # #if the user has entered a prompt, the auto_save_chat_history function will call save_chat_history function with session state log which has user prompt