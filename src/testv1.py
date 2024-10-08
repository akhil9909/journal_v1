import streamlit as st

# Define your helpers
helpers = [
    "Start with a summary", 
    "Outline key challenges", 
    "Highlight recent achievements", 
    "Mention stakeholder feedback", 
    "Describe team goals", 
    "Include project milestones", 
    "Talk about upcoming risks", 
    "Share new learnings", 
    "Highlight collaboration", 
    "List action items"
]

# Initialize session state for text area
if "input_text" not in st.session_state:
    st.session_state.input_text = ""


# Function to add helper text to the textarea
def add_helper_text(helper):
    st.session_state.input_text += " " + helper
# Display chips as buttons
st.markdown('<h4>Select a pointer to guide your writing:</h4>', unsafe_allow_html=True)
for helper in helpers:
    if st.button(helper):
        add_helper_text(helper)

# Text area for user input - controlled by session_state
st.text_area("Your Input", value=st.session_state.input_text, key="input_text", height=200)
if st.button("run Input"):
    st.write(st.session_state.input_text)