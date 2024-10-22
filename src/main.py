#main function is working after adding selected assistant and adding get_chat_message function
import asyncio
import streamlit as st
from functions import run_assistant, get_chat_history, get_chat_message
from awsfunc import save_chat_history, get_openai_api_key, get_credentials
import os
from cached_functions import get_local_img, ROOT_DIR

#main function starts here

async def main(human_prompt: str, selected_assistant: str) -> dict:
    res = {'status': 0, 'message': "Success"}
    
    prompt_box = st.empty()
    chat_box = st.empty()

    # Strip the prompt of any potentially harmful html/js injections
    check_human_prompt = human_prompt.replace("<", "&lt;").replace(">", "&gt;")
    
    if check_human_prompt != human_prompt:
        st.warning("Your input has been sanitized to prevent XSS attacks.")
        return {'status': 1, 'message': "Input sanitized to prevent XSS attacks."}


    # Update both chat log and the model memory
    st.session_state.LOG.append(f"Human: {human_prompt}")
    st.session_state.MEMORY.append({'role': "user", 'content': human_prompt})
    
    writing_animation = st.empty()
    file_path = os.path.join(ROOT_DIR, "src", "assets", "loading.gif")
    writing_animation.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;<img src='data:image/gif;base64,{get_local_img(file_path)}' width=30 height=10>", unsafe_allow_html=True)

    if selected_assistant == "No Assistant":
        # Clear the writing animation
        writing_animation.empty()
        # Update the chat log and the model memory
        st.session_state.LOG.append(f"AI: No assistant selected to run.")
        st.session_state.MEMORY.append({'role': "assistant", 'content': "No assistant selected to run."})
        st.session_state.main_called_once = True # so that next time the UI display a text_input box instead of text_area
        return {'status': 0, 'message': "Success"}

    chatbot_response_dict = await run_assistant(human_prompt, selected_assistant)

    # Check if the call was successful
    if chatbot_response_dict['status'] == 0:
        chatbot_response = chatbot_response_dict['message']
        msg = "Success"
    else:
        chatbot_response = "error, please use debug mode to see more details"
        msg = f"Error: {chatbot_response_dict['message']}"
        return {'status': 1, 'message': msg}

    # Clear the writing animation
    writing_animation.empty()

    # Update the chat log and the model memory
    st.session_state.LOG.append(f"AI: {chatbot_response}")
    st.session_state.MEMORY.append({'role': "assistant", 'content': chatbot_response})

    res = {'status': chatbot_response_dict['status'], 'message': msg}
    st.session_state.chatbot_response = chatbot_response
    st.session_state.main_called_once = True # so that next time the UI display a text_input box instead of text_area
    #time.sleep(5) # check to see behaviour of rendering user input and bot response before exiting the function
    return res # work on it, later add debugging functionality to add details to response


