import streamlit as st
import openai
import os
import json
from functions import run_assistant, get_chat_history
from awsfunc import save_chat_history, get_openai_api_key
import base64
import asyncio

# Get OpenAI API key from environment variable
#openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = get_openai_api_key()


# Initialize thread
if "thread_id" not in st.session_state:
    thread = openai.beta.threads.create()
    st.session_state.thread_id = thread.id

#initialize root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INITIAL_PROMPT = "User prompt empty"


### FUNCTION DEFINITIONS ###


@st.cache_data(show_spinner=False)
def get_local_img(file_path: str) -> str:
    # Load a byte image and return its base64 encoded string
    return base64.b64encode(open(file_path, "rb").read()).decode("utf-8")


@st.cache_data(show_spinner=False)
def get_favicon(file_path: str):
    # Load a byte image and return its favicon
    return Image.open(file_path)


@st.cache_data(show_spinner=False)
def get_css() -> str:
    # Read CSS code from style.css file
    with open(os.path.join(ROOT_DIR, "src", "style.css"), "r") as f:
        return f"<style>{f.read()}</style>"


def get_chat_message(
    contents: str = "",
    align: str = "left"
) -> str:
    # Formats the message in an chat fashion (user right, reply left)
    div_class = "AI-line"
    color = "rgb(240, 242, 246)"
    file_path = os.path.join(ROOT_DIR, "src", "assets", "AI_icon.png")
    src = f"data:image/gif;base64,{get_local_img(file_path)}"
    if align == "right":
        div_class = "human-line"
        color = "rgb(165, 239, 127)"
        if "USER" in st.session_state:
            src = st.session_state.USER.avatar_url
        else:
            file_path = os.path.join(ROOT_DIR, "src", "assets", "user_icon.png")
            src = f"data:image/gif;base64,{get_local_img(file_path)}"
    icon_code = f"<img class='chat-icon' src='{src}' width=32 height=32 alt='avatar'>"
    formatted_contents = f"""
    <div class="{div_class}">
        {icon_code}
        <div class="chat-bubble" style="background: {color};">
        &#8203;{contents}
        </div>
    </div>
    """
    return formatted_contents

#main function starts here

async def main(human_prompt: str) -> dict:
    res = {'status': 0, 'message': "Success"}
    try:

        # Strip the prompt of any potentially harmful html/js injections
        human_prompt = human_prompt.replace("<", "&lt;").replace(">", "&gt;")

        # Update both chat log and the model memory
        st.session_state.LOG.append(f"Human: {human_prompt}")
        st.session_state.MEMORY.append({'role': "user", 'content': human_prompt})

        # Clear the input box after human_prompt is used
        prompt_box.empty()

        with chat_box:
            # Write the latest human message first
            line = st.session_state.LOG[-1]
            contents = line.split("Human: ")[1]
            st.markdown(get_chat_message(contents, align="right"), unsafe_allow_html=True)

            reply_box = st.empty()
            # try unremoving this and see what visual thing it makes
            reply_box.markdown(get_chat_message(), unsafe_allow_html=True)

            # # This is one of those small three-dot animations to indicate the bot is "writing"
            # writing_animation = st.empty()
            # file_path = os.path.join(ROOT_DIR, "src", "assets", "loading.gif")
            # writing_animation.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;<img src='data:image/gif;base64,{get_local_img(file_path)}' width=30 height=10>", unsafe_allow_html=True)

            chatbot_response = await run_assistant(human_prompt, selected_assistant)

            reply_box.markdown(get_chat_message(chatbot_response), unsafe_allow_html=True)

            # Clear the writing animation
            #writing_animation.empty()

            # Update the chat log and the model memory
            st.session_state.LOG.append(f"AI: {chatbot_response}")
            st.session_state.MEMORY.append({'role': "assistant", 'content': chatbot_response})

            res = {'status': 0, 'message': "Success"}

    except:
        res = {'status': 1, 'message': "Failure"}
        return res
    return res # work on it, later add debugging functionality to add details to response



### MAIN STREAMLIT UI STARTS HERE ###
st.set_page_config(
    page_title="Journal V1 App",
    layout="wide"
)
# Get available assistants (you'll need to implement this)
assistants = ["asst_V1dqbgYTAdUEAWgBYQmBgVyZ", "assistant_2_id"]  # Replace with your logic

selected_assistant = st.selectbox("Select Assistant", assistants)

if "initial_prompt" not in st.session_state:
    st.session_state.initial_prompt = INITIAL_PROMPT;

if "chat_history" not in st.session_state:
    st.session_state.chat_history = ""

col1, col2 = st.columns(2)

# Place buttons side by side
with col1:
    if st.button("save chat history"):
        if st.session_state.thread_id and selected_assistant:
            if st.session_state.chat_history == "":
                st.text("No Chat History to Save")
            elif save_chat_history(st.session_state.thread_id, 
                      selected_assistant, 
                      st.session_state.initial_prompt, 
                      st.session_state.chat_history):
                st.text("Chat history saved")
            else:
                st.text("Failed to save Chat history")
        else:
            st.text("No Thread to Save")

with col2:
    if st.button("New Session"):
        try:
            for key in st.session_state.keys():
                del st.session_state[key]
            prompt_box = st.empty()#... not working
            chat_box = st.empty()#... not working
            #trigger either main function again, or render chat history so far code block
            st.rerun()
        except:
            st.text("new session initiated")
        

# Define main layout
st.title("My Journal")
st.subheader("")
chat_box = st.container()
st.write("")
prompt_box = st.empty()
footer = st.container()

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


# Initialize/maintain a chat log and chat memory in Streamlit's session state
# Log is the actual line by line chat, while memory is limited by model's maximum token context length
if "MEMORY" not in st.session_state:
    st.session_state.MEMORY = [{'role': "system", 'content': INITIAL_PROMPT}]
    st.session_state.LOG = [INITIAL_PROMPT]

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
    human_prompt = st.text_input("You: ", value="", key=f"text_input_{len(st.session_state.LOG)}")


# Gate the subsequent chatbot response to only when the user has entered a prompt
if len(human_prompt) > 0:
    run_res = asyncio.run(main(human_prompt))
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
    if run_res['status'] == 0: #i removed  "if run_res['status'] == 0 and not DEBUG"
        st.rerun()