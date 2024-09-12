import openai
import os
import streamlit as st

# Function to add user message and run assistant
async def run_assistant(prompt, assistant_id):
    openai.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )
    run = openai.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id
    )
    while True:
        run_status = openai.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )
        if run_status.status == "completed":
            messages = openai.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )
            return messages.data[0].content[0].text.value
        elif run_status.status == "failed":
            return "Assistant run failed. Please try again."
        

# Function to get chat history
def get_chat_history():
    messages = openai.beta.threads.messages.list(
        thread_id=st.session_state.thread_id
    )
    return messages.data