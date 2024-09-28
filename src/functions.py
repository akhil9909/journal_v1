import openai
import os
import streamlit as st
import base64
from cached_functions import get_local_img, ROOT_DIR
import logging
import html



# Configure logging
error_log = []

def log_error(message):
    error_log.append(message)
    logging.error(message)

# Function to add user message and run assistant
async def run_assistant(prompt, assistant_id) -> dict:
    res = {'status': 0, 'message': "Success"}
    try:
        openai.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )
    except Exception as e:
        log_error(f"Error in openai.beta.threads.messages.create: {e}")
        res['status'] = 1
        res['message'] = f"An error occurred: {e}\n\nError Log:\n{''.join(error_log)}"
        return res
    
    try:
        run = openai.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assistant_id
        )
    except Exception as e:
        log_error(f"Error in openai.beta.threads.runs.create: {e}")
        res['status'] = 1
        res['message'] = f"An error occurred: {e}\n\nError Log:\n{''.join(error_log)}"
        return res
    
    try:
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
            if run_status.status == "completed":
                messages = openai.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )
                res['message'] = messages.data[0].content[0].text.value
                return res
            elif run_status.status == "failed":
                res['status'] = 1
                res['message'] = "Assistant run failed. Please try again."
                return res
    except Exception as e:
        log_error(f"Error in openai.beta.threads.runs.retrieve: {e}")
        res['status'] = 1
        res['message'] = f"An error occurred in retrieving thread runs: {e}\n\nError Log:\n{''.join(error_log)}"
        return res

# Function to get chat history
def get_chat_history() -> dict:
    res = {'status': 0, 'message': "Success"}
    try:
        messages = openai.beta.threads.messages.list(
            thread_id=st.session_state.thread_id
        )
        res['message'] = messages.data
        return res
    except Exception as e:
        log_error(f"Error in openai.beta.threads.messages.list: {e}")
        res['status'] = 1
        res['message'] = f"An error occurred in retrieving messages of thread from openai: {e}\n\nError Log:\n{''.join(error_log)}"
        return res
    
# Function to format chat message
def get_chat_message(
    contents: str = "",
    align: str = "left"
) -> str:
    # Sanitize the content to escape any HTML-like characters from user input
    contents = html.escape(contents).strip()  # Strip any newlines or excessive whitespace
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