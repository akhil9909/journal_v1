import streamlit as st
from awsfunc import aws_error_log

def get_session_states():
    with st.sidebar:
        st.subheader("Debug area")
        #from App.py
        st.write(f"Assistant: {st.session_state.get('assistant', 'Not set')}")
        st.write(f"Thread ID: {st.session_state.get('thread_id', 'Not set')}")
        st.write(f"Initial Prompt: {st.session_state.get('initial_prompt', 'Not set')}")
        st.write(f"Chat History: {st.session_state.get('chat_history', 'Not set')}")
        st.write(f"Chat History Status: {st.session_state.get('chat_history_status', 'Not set')}")
        st.write(f"Memory: {st.session_state.get('MEMORY', 'Not set')}")
        st.write(f"Input Text: {st.session_state.get('input_text', 'Not set')}")
        st.write(f"main_called_once: {st.session_state.get('main_called_once', 'Not set')}")
        st.write(f"Log: {st.session_state.get('LOG', 'Not set')}")
        st.write(f"Debug mode: {st.session_state.get('DEBUG', 'Not set')}")
        st.write(f"Authenticated: {st.session_state.get('authenticated', 'Not set')}")
        st.write(f"Username: {st.session_state.get('username', 'Not set')}")
        st.write(f"Rerun: {st.session_state.get('rerun', False)}")  # Check if rerun flag is set
        st.write(f"AWS error log: {aws_error_log}")
        st.write(f"Feedback: {st.session_state.get('feedback', 'Not set')}")
        st.write(f"Other Feedback: {st.session_state.get('other_feedback', 'Not set')}")
        st.write(f"Analysis mode flag: {st.session_state.get('analysis_mode', 'Not set')}")
        #from static_prompts_text.py
        st.write(f"Generate Image Prompt Text: {st.session_state.get('generate_image_prompt_text', 'Not set')}")
        st.write(f"Summarize Before Image Prompt Text: {st.session_state.get('summarize_before_image_prompt_text', 'Not set')}")
        #from learning.py
        st.write(f"Counter: {st.session_state.get('counter', 0)}")
        st.write(f"Learning Component: {st.session_state.get('learning_component', 'Not set')}")
        st.write(f"Boolean_Flag_to_Show_Topic: {st.session_state.get('boolean_flag_to_show_topics', False)}")
        st.write(f"Image URL: {st.session_state.get('image_url', 'Not set')}")
        st.write(f"Image Not Saved: {st.session_state.get('image_not_saved', True)}")
        st.write(f"Learning Component Linked: {st.session_state.get('learning_component_linked', 'Not set')}")
        st.write(f"summarized topics: {st.session_state.get('summarized_topics', 'Not set')}")
        st.write(f"image_prompt_text_for_this_summary: {st.session_state.get('image_prompt_text_for_this_summary', 'Not set')}")
        st.write(f"files_attached to the thread: {st.session_state.get('files_attached', 'Not set')}")
        st.write(f"recent_response_AI: {st.session_state.get('recent_response_AI', 'Not set')}")
        st.write(f"recent_response_human: {st.session_state.get('recent_response_human', 'Not set')}")
        st.write(f"recent_deadclick: {st.session_state.get('recent_deadclick', 'Not set')}")
        st.write(f"dummy_check: {st.session_state.get('dummy_check', 'Not set')}")
        #from my conversations.py
        #no additional session states, but following are loaded in a fucntion here to navigate to App.py
        #those are thread_id, LOG, main_called_once, assistant
        #from prompt_page.py
        st.write(f"PromptOps Assistant: {st.session_state.get('promptops_assistant', 'Not set')}")
        #from user_privacy.py
        st.write(f"User input section variable: {st.session_state.get('section', 'Not set')}")


