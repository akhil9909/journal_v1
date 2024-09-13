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

            # Step 1: Generate the AI-aided image prompt using ChatGPT API
            # (but we first need to generate the prompt for ChatGPT!)
            
            #write this function to generate prompt response
            #st.session_state.memory is the intial or subsequent prompt to assistant api
            chatbot_response = await run_assistant(human_prompt, selected_assistant)

            #generate reply_text from chatbot response
            #use the content index first thing
            reply_box.markdown(get_chat_message(chatbot_response), unsafe_allow_html=True)

            # Clear the writing animation
            #writing_animation.empty()

            # Update the chat log and the model memory
            st.session_state.LOG.append(f"AI: {chatbot_response}")
            st.session_state.MEMORY.append({'role': "assistant", 'content': chatbot_response})

            res = "success"

    return res # work on it, later add debugging functionality to add details to response

### INITIALIZE AND LOAD ###

# # Initialize page config
# favicon = get_favicon(os.path.join(ROOT_DIR, "src", "assets", "AI_icon.png"))
# st.set_page_config(
#     page_title="CatGDP - Feline whiskerful conversations.",
#     page_icon=favicon,
# )


