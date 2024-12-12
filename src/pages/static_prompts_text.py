import streamlit as st
import time
import sys

if '/workspaces/journal_v1/src/' not in sys.path:
    sys.path.append('/workspaces/journal_v1/src/')

from awsfunc import update_static_prompt_to_DB, fetch_static_prompts_from_DB,aws_error_log
from streamlit_session_states import get_session_states

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if "DEBUG" not in st.session_state:
    st.session_state.DEBUG = False
    
# Get query parameters
try:
    if st.query_params["DEBUG"].lower() == "true":
        st.session_state.DEBUG = True
except KeyError:
    pass

#MOdify the entries added in dev/todo
@st.dialog("Modify Static Prompt")
def modify_static_prompt(title,description):
    st.write("Topic:",title)
    modified_input = st.text_area("Edit the description below, Press Command/Ctrl Enter to Apply",value=description,key='modify_text_area_key')
    if st.button("Save"):
        update_flag = update_static_prompt_to_DB(title,modified_input)
        time.sleep(2)
        if update_flag:
            st.success("Changes saved successfully.")
            time.sleep(2)
            st.rerun()
        else:
            st.error("Failed to save changes. Check Debug for Details.")
            if st.session_state.DEBUG:
                with st.sidebar:
                    st.text("Failed at save static prompts update"
                        f"Error Log: {aws_error_log}")


#fetch the prompts from the database, create a fucntion to fetch the prompts
#add m,pdify button and call dialog box

def fetch_static_prompts():
    static_prompts = fetch_static_prompts_from_DB()
    for prompt in static_prompts:
        title = prompt['title']
        description = prompt['description']
        st.subheader(title)
        st.write(description)
        if st.button("Modify",key=title+"modify"):
            modify_static_prompt(title,description)
        if title == "generate_image_prompt_text":
            st.session_state.generate_image_prompt_text = description
        if title == "summarize_before_image_prompt_text":
            st.session_state.summarize_before_image_prompt_text = description
        st.write("------------------------------------------------")
    return

if st.session_state.authenticated:
    st.title(" Static Prompts Text Page ")
    st.caption(
        "This page is used to manage the static prompts that are used in the code."
        " New prompts will not be created here, but directly in code base and added in database manually."
        )
    st.caption("------------------------------------------------")
    fetch_static_prompts()
else:
    st.write("Please log in to view your Static Prompts Page.")
    st.page_link("./App.py", label="Log in", icon="🔒")

if st.session_state.DEBUG:
    get_session_states()

# https://community.openai.com/t/dalle3-prompt-tips-and-tricks-thread/498040
# # Initial prompt variables
# generate_image_prompt_text = (
#         "Create a visually clear and legible image or flowchart that depicts the relationships between the following topics. "
#         "Ensure that the relationships and descriptions are visible and understandable. Use arrows or visual elements "
#         "to show how the topics are interconnected. Adhere to minimalistic design. The relationships between elements should be easy to read left to right.\n\n"
#     )

# summarize_before_image_prompt_text = (
#                 "Analyze the following topics and infer key elements and relationships. "
#                 "Keep the elements and relationships short, if no other details are given, do not create new details. "
#                 "Return the relationships as a structured format that describes how these topics relate to each other. "
#                 "Do not respond in any other format or any other details."
#             )
