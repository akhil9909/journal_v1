import streamlit as st
import openai
import os
import json
from functions import run_assistant, get_chat_history, get_chat_message
from awsfunc import save_chat_history, get_openai_api_key, get_credentials
from cached_functions import get_css
import base64
import asyncio
from main import main  # Import the main function

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




## Helper Functions

def reset_session():
    st.session_state.LOG = [INITIAL_PROMPT]
    st.session_state.chat_history = ""
    st.session_state.chat_history_status = "Chat history NOT saved"
    st.session_state.MEMORY = [{'role': "system", 'content': INITIAL_PROMPT}]
    thread = openai.beta.threads.create()
    st.session_state.thread_id = thread.id
    

### MAIN STREAMLIT UI STARTS HERE ###
st.set_page_config(
    page_title="Journal V2 App",
    layout="wide"
)
# Get available assistants (you'll need to implement this)
assistants = ["asst_V1dqbgYTAdUEAWgBYQmBgVyZ", "assistant_2_id"]  # Replace with your logic

selected_assistant = st.selectbox("Select Assistant", assistants)

col1, col2 = st.columns(2)

# Place buttons side by side
with col1:
    if st.button("save chat history"):
        if st.session_state.chat_history_status == "Chat history saved":
            st.text("Chat history auto saved")
        else:
            if st.session_state.chat_history == "":
                st.text("No Chat History to Save")
            elif save_chat_history(st.session_state.thread_id, 
                      selected_assistant, 
                      st.session_state.initial_prompt, 
                      st.session_state.chat_history):
                st.text("Chat history saved")
            else:
                st.text("Failed to save Chat history")

with col2:
    if st.button("New Session"):
        reset_session()
        st.text("new session initiating")
        st.rerun()
    
   
   
        

# Define main layout
st.title("My Journal v2")
st.subheader("")
chat_box = st.container()
st.write("")
prompt_box = st.empty()
footer = st.container()

# Load credentials from aws secret manager
streamlit_secret = get_credentials()
data_dict = json.loads(streamlit_secret)
streamlit_username = data_dict['streamlit_username']
streamlit_password = data_dict['streamlit_password']


# Authentication UI
if not st.session_state.authenticated:
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        if username == streamlit_username and password == streamlit_password:
            st.session_state.authenticated = True
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password")
        st.rerun()



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


# Define an input box for human prompts
with prompt_box:
    # If authenticated, show the initial prompt
    if st.session_state.authenticated:
        human_prompt = st.text_input("You: ", value="", key=f"text_input_{len(st.session_state.LOG)}")


# Gate the subsequent chatbot response to only when the user has entered a prompt
if st.session_state.authenticated:
    if len(human_prompt) > 0:
        run_res = main(human_prompt, selected_assistant)
        st.text(run_res) #debigging
        chat_history = get_chat_history()
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
            st.text("Failed to save Chat history")
            st.session_state.chat_history_status = "Chat history NOT saved"
        if run_res['status'] == 0: #i removed  "if run_res['status'] == 0 and not DEBUG"
            st.rerun()