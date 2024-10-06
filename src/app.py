import streamlit as st
import openai
import os
import json
from functions import run_assistant, get_chat_history, get_chat_message
from awsfunc import save_chat_history, get_openai_api_key, get_credentials,aws_error_log
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

if "button_length" not in st.session_state:
    st.session_state.button_length = 0

    

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
    st.session_state.button_length = 0
    try:
        thread = openai.beta.threads.create()
        st.session_state.thread_id = thread.id
    except Exception as e:
        res['status'] = 1
        res['message'] = f"An error occurred in creating thread in reset session: {e}"
        return res
    return res
    
# Function to add helper text to the textarea
# def add_helper_text(helper):
#     st.session_state.button_length = len(helper)
#     st.session_state.input_text = helper
    


### MAIN STREAMLIT UI STARTS HERE ###
st.set_page_config(
    page_title="Journal V3 App",
    layout="wide"
)

# Debug area
if st.session_state.DEBUG:
    with st.sidebar:
        st.subheader("Debug area")
        st.write(f"Thread ID: {st.session_state.thread_id}")
        st.write(f"Initial Prompt: {st.session_state.initial_prompt}")
        st.write(f"Chat History: {st.session_state.chat_history}")
        st.write(f"Chat History Status: {st.session_state.chat_history_status}")
        st.write(f"Memory: {st.session_state.MEMORY}")
        st.write(f"Input Text: {st.session_state.input_text}")
        st.write(f"Button Length: {st.session_state.button_length}")
        st.write(f"main_called_once: {st.session_state.main_called_once}")
        st.write(f"Log: {st.session_state.LOG}")
        st.write(f"Debug mode: {st.session_state.DEBUG}")
        st.write(f"Authenticated: {st.session_state.authenticated}")
        st.write(f"Username: {st.session_state.get('username', 'Not set')}")
        st.write(f"Rerun: {st.session_state.get('rerun', False)}")  # Check if rerun flag is set
        st.write(f"AWS error log: {aws_error_log}")

# Get available assistants (you'll need to implement this)
assistants = ["asst_V1dqbgYTAdUEAWgBYQmBgVyZ", "No Assistant"]  # Replace with your logic

selected_assistant = st.selectbox("Select Assistant", assistants)

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
                      selected_assistant, 
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
st.title("My Journal v3")
st.write("This is a journaling app that uses OpenAI's GPT-3 to assist you in developing your strengths.")
chat_box = st.container()
st.write("")
hint_box = st.container()
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
                            st.session_state.button_length = len(helper)
                            st.session_state.input_text = helper
                        



# Define an input box for human prompts
with prompt_box:
    # If authenticated, show the initial prompt
    if st.session_state.authenticated:
        if not st.session_state.main_called_once:
            human_prompt = st.text_area("You: ", value=st.session_state.input_text, key="input_text", height=150)
        else:
            human_prompt =  st.text_input("You: ", value="", key=f"text_input_{len(st.session_state.LOG)}")
            

if st.session_state.authenticated:
    run_button = st.button("Send", key=f"send_button_{len(st.session_state.LOG)}")

if st.session_state.main_called_once:
    hint_box.empty()


# Gate the subsequent chatbot response to only when the user has entered a prompt
if st.session_state.authenticated:
    if (len(human_prompt) > st.session_state.button_length or run_button): #[pass empty input text why? and len(human_prompt) > st.session_state.button_length #this will have a bug that if a user deadclicks the send button on empty (or helped button clicked but no details enter), the main function will be called
        run_res = asyncio.run(main(human_prompt, selected_assistant))

        #[placeholder 1] if the main function runs successfully, update the chat history before rerunning the app (to show the response in next iteration)
        if run_res['status'] == 0 and not st.session_state.DEBUG: 
            
            chat_history_dict = get_chat_history()
            
            if chat_history_dict['status'] == 0:
                chat_history = chat_history_dict['message']
                formatted_chat_history = ""
                for message in chat_history:
                    if message.role == "user":
                        formatted_chat_history += f"**You:** {message.content[0].text.value}\n" 
                        if st.session_state.initial_prompt == INITIAL_PROMPT:
                            st.session_state.initial_prompt = message.content[0].text.value
                    elif message.role == "assistant":
                        formatted_chat_history += f"**Assistant:** {message.content[0].text.value}\n"
                st.session_state.chat_history = formatted_chat_history
                if save_chat_history(st.session_state.thread_id, 
                                selected_assistant, 
                                st.session_state.initial_prompt, 
                                st.session_state.chat_history):
                    st.session_state.chat_history_status = "Chat history saved"
                else:
                    st.session_state.chat_history_status = "Chat history NOT saved"
                    st.error("Failed to save Chat history, use debug mode to see more details")
                    #add debug code, show aws_error_log variable here
            else:
                st.error("Failed to save chat history, use debug mode to see more details")
                #add debug code, use chat_history_dict['message'] to show error message
                #Failed to get Chat history from openAI code in auto save module

            st.rerun()
        else:
            if run_res['status'] != 0:
                st.error("Failed to run main function")
                if st.session_state.DEBUG:
                    with st.sidebar:
                        st.text("Failed at main function run"
                                f"Error Log: {run_res['message']}")
            else:
                st.error("Debug mode is on, please remove ?DEBUG=true from url")
                
                #chat history is not auto saved via code in debug mode, so addding a dummy message to chat history so it can be saved by click of chat history button
                #to recreate the behaviour of auto chat histoy save, add code snippet belonging to [placeholder 1] here
                st.session_state.chat_history = "dummy message"
                
                # Sleep for 2 seconds
                time.sleep(2)
                st.rerun()
