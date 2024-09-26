#main function is working after adding selected assistant and adding get_chat_message function
import asyncio
import streamlit as st
from functions import run_assistant, get_chat_history, get_chat_message
from awsfunc import save_chat_history, get_openai_api_key, get_credentials
#main function starts here

async def main(human_prompt: str, selected_assistant: str) -> dict:
    res = {'status': 0, 'message': "Success"}
    #try:
    # Define prompt_box and chat_box
    prompt_box = st.empty()
    chat_box = st.empty()

    # Strip the prompt of any potentially harmful html/js injections
    #human_prompt = human_prompt.replace("<", "&lt;").replace(">", "&gt;")

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

    # except:
    #     res = {'status': 1, 'message': msg}
    #     return res
    return res # work on it, later add debugging functionality to add details to response


