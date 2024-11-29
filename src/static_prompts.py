import streamlit as st
import time
from awsfunc import update_static_prompt_to_DB


# Initial prompt variables
generate_image_prompt_text = (
        "Create a visually clear and legible image or flowchart that depicts the relationships between the following topics. "
        "Ensure that the relationships and descriptions are visible and understandable. Use arrows or visual elements "
        "to show how the topics are interconnected. Adhere to minimalistic design. The relationships between elements should be easy to read left to right.\n\n"
    )

summarize_before_image_prompt_text = (
                "Analyze the following topics and infer key elements and relationships. "
                "Keep the elements and relationships short, if no other details are given, do not create new details. "
                "Return the relationships as a structured format that describes how these topics relate to each other. "
                "Do not respond in any other format or any other details."
            )

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
            st.error("Failed to save changes.")


#fetch the prompts from the database, create a fucntion to fetch the prompts
#add m,pdify button and call dialog box