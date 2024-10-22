import openai
import os
import streamlit as st
import base64
from cached_functions import get_local_img, ROOT_DIR
import logging
import html
from awsfunc import save_chat_history, aws_error_log
import time



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

# Function to auto save chat history

def auto_save_chat_history(run_res, selected_assistant,INITIAL_PROMPT,Boolean_Flag_to_Update_Chat_History):
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
                                st.session_state.chat_history,
                                Boolean_Flag_to_Update_Chat_History):
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
