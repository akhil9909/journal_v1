import openai
import os
import streamlit as st
import base64
from cached_functions import get_local_img, ROOT_DIR
import logging
import html
from awsfunc import save_chat_history, aws_error_log, get_promptops_entries,get_openai_api_key, fetch_static_prompts_from_DB
import time
from openai import OpenAI
import sys
from collections import defaultdict
import json
import re

if '/workspaces/journal_v1/src/pages' not in sys.path:
    sys.path.append('/workspaces/journal_v1/src/pages')

client = OpenAI(api_key=get_openai_api_key())

# Configure logging
error_log = []

def log_error(message):
    error_log.append(message)
    logging.error(message)

#fetch static prompts and update session state
def fetch_static_prompts():
    static_prompts = fetch_static_prompts_from_DB()
    for prompt in static_prompts:
        title = prompt['title']
        description = prompt['description']
        if title == "generate_image_prompt_text":
            st.session_state.generate_image_prompt_text = description
        if title == "summarize_before_image_prompt_text":
            st.session_state.summarize_before_image_prompt_text = description
        if title == "structure_assistant_instructions":
            st.session_state.structure_assistant_instructions = description
        if title == "add_notes_assistant_instructions":
            st.session_state.add_notes_assistant_instructions = description
        st.write("------------------------------------------------")
    return

# Function to add user  message and run assistant
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

def auto_save_chat_history(run_res, selected_assistant,INITIAL_PROMPT,Boolean_Flag_to_Update_Chat_History,human_prompt):
    if run_res['status'] == 0 and not st.session_state.DEBUG:
            
            #######
            # I have removed the below code, as i am saving chat history in dynamoDB from log variable instead of the get_chat_history() function from openAI
            #######
            # chat_history_dict = get_chat_history()
            
            # if chat_history_dict['status'] == 0:
            #     chat_history = chat_history_dict['message']
            #     formatted_chat_history = ""
            #     for message in chat_history:
            #         if message.role == "user":
            #             formatted_chat_history += f"**You:** {message.content[0].text.value}\n" 
            #             if st.session_state.initial_prompt == INITIAL_PROMPT:
            #                 st.session_state.initial_prompt = message.content[0].text.value
            #         elif message.role == "assistant":
            #             formatted_chat_history += f"**Assistant:** {message.content[0].text.value}\n"
            #     st.session_state.chat_history = formatted_chat_history
            #     if save_chat_history(st.session_state.thread_id, 
            #                     selected_assistant, 
            #                     st.session_state.initial_prompt, 
            #                     st.session_state.chat_history,
            #                     Boolean_Flag_to_Update_Chat_History):
            #         st.session_state.chat_history_status = "Chat history saved"
            #     else:
            #         st.session_state.chat_history_status = "Chat history NOT saved"
            #         st.error("Failed to save Chat history, use debug mode to see more details")
            #         #add debug code, show aws_error_log variable here
            # else:
            #     st.error("Failed to save chat history, use debug mode to see more details")
            #     #add debug code, use chat_history_dict['message'] to show error message
            #     #Failed to get Chat history from openAI code in auto save module
            
            #######
            # the logic of this code below is basically to preserve the first human prompt in conversation as initial prompt, and NOT update it in dynamodb
            if st.session_state.initial_prompt == INITIAL_PROMPT:
                st.session_state.initial_prompt = human_prompt

            if save_chat_history(st.session_state.thread_id, 
                            selected_assistant, 
                            st.session_state.initial_prompt,
                            st.session_state.LOG,
                            Boolean_Flag_to_Update_Chat_History):
                st.session_state.chat_history_status = "Chat history saved"
            else:
                st.session_state.chat_history_status = "Chat history NOT saved"
                st.error("Failed to save Chat history, use debug mode to see more details")
                #add debug code, show aws_error_log variable here
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

def fetch_and_summarize_entries(component):
    fetch_static_prompts()
    entries = get_promptops_entries(component)
    filtered_entries = [
        entry for entry in entries 
        if not entry.get('do_not_stage', False) and entry['title'] != '#'
    ]
    
    # Split the session_state.summarize_before_image_prompt_text into two parts
    before_, after_ = st.session_state.summarize_before_image_prompt_text.split("|")
    
    # Create the about_this variable
    about_this = next(
        (entry['description'] for entry in entries if entry['title'] == '#'), 
        ""
    )
    
    if filtered_entries:
        combined_text = "\n".join(
            f"Title: {entry['title']}, Description: {entry['description']}" 
            for entry in filtered_entries
        )
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Use "gpt-4" if you prefer that model
            messages=[{"role": "user", "content": f"{before_} {about_this} {after_} {combined_text}"}]
        )
        return response.choices[0].message.content.strip()
    else:
        return "No topics to summarize."

def generate_assistant_instructions_prompt(assistant_instructions_text):
    fetch_static_prompts()
    prompt = f"{st.session_state.structure_assistant_instructions} Instructions: {assistant_instructions_text}\n\n"
    return prompt

def generate_add_notes_to_assistant_prompt(notes_text, notes_category,delta):
    fetch_static_prompts()
    #split the text into st.session_state.add_notes_assistant_instructions using | and save it in two variables pre_promot and post_prompt
    pre_prompt, post_prompt = f"{st.session_state.add_notes_assistant_instructions}".split("|")
    prompt = f"{pre_prompt} {notes_category} . {post_prompt} .\n\n[[[Instructions: {notes_text}..]]]\n\n additional {notes_category} are : {delta}\n\n"
    return prompt

# Call OpenAI's DALL-E API to generate an image
def generate_image_from_gpt(prompt):
    response = client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size="1024x1024",
    quality="standard",
    n=1,
    )
    image_url = response.data[0].url
    return image_url
    #return "https://streamlit-prod-bucket.s3.amazonaws.com/dev/Brene%20Brown/572a86b7-5bb4-4280-88a3-ec83bf50f9b4.jpg?AWSAccessKeyId=ASIA6ALM6IM5ZJ7YEKB5&Signature=MZqD9mqMoznZAZr4W9smCMnyqYo%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEKb%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQCVP8xNfevS6twGgCYvXjwL2SK5i3lSx%2B0i8o1PAke55QIhAI1JS0C7eBpM1w7A0ZlWfhWwk3o1M%2F8iKlaYF0yyKOD%2BKrsFCD8QARoMOTYyODM4MDIwOTIzIgwyLY%2FbQqHY765YKpgqmAVA%2BcQ1DrL04sI%2BLMX2WhJc90jkZPr76fD5GlKwM75mpTfKSf0eEXSQPGQprPZ0iJ%2BglncfQ4Xms1wGUcPN2cVJdL7%2FeGqFvA%2B%2BYwJ64h%2Fwd6Q268DfIT7pQyHrax%2Bns2Zcxb7YoYIR6o10vRtM9NAguLa0GigQdIDlfICvCIT1zBy8NJ22QqTyzvprLHH%2BFFDdvIgDlEDpCBzchorR5rru5hyXTm7blTumM9%2Fkt2C4w11jLYILpoNvDCrYttY8tqYwzyPqBjD%2FpvnevjSiuOYOM%2F7ikFeIMUH4qypo59UO3vRWXJwnrMk%2FThNMuEu4R9CH1uQm3PGMs3Wta%2BwqiaopAd85VkWNaZtM8uCAToZg5SXDFxZbY4V5pZmK4Cu6kMxw0USgw%2BrHeGQUGgCAnxJ6IZ8g9Vimv2ZodV0FWFAqH0oF5H9PyObLEn7UBjy29eus%2BMfvwTit7cEHYGiNT8%2FsZ3j57yU453NMtbfkm1cLaVVz5tW%2Fv8%2FBVgbVppo1UPav4giCz2UNh058STQqkaQ4R9ul7B7xrxQ5fjljdEOVvIAXgag1WYTDR3tcSYo463IgpuNOXYvu6XMajiaEdph28dU4LFDa%2F7bEF%2FOxN2ZsSlAWtQn%2Bk0e62BI06hILrNfux5PyFFIt167QUURQ6KOSm%2BTG%2F6W1BeEyd99HonCdPp%2FLlFr4j0iAGJRkz%2BN%2BV2BWctenxd0NKFZNdx0A4YqYJO%2B4z19MzJcBsB8jMFhWfBUYSvYZWJwjtYLqu1Rfu7TP1%2BfWq6Q%2FuqTC1R4a5zZg19z1Hmy42wDSm3J2vELBng8Nbrz2UOk%2FLqAVgKEcfqD7izHRcMuqHbjRbrPwEk%2FuROH%2FDlpOUOUIaYFjp%2F2urfKu98ak2rnuMOvqscAGOrABhmbZi61Si7ITPEJaOKxommD5jcRjsb8zfjn%2Bk0qWwofL9Y%2B0oVwuBe6KlVdf5b1%2BXhcg%2BpvhqA3D6%2FPhYZyu6YCkwBFnAkdjvWCWPgK3NMzfSxNw%2BkWgc48qBvzQY2dDNVT7GUFDUxbkagFOHAicp1Y07Fhvd0UyS3s%2BKK3tZ12uRkhwmya1a84q1%2Bv6OdCUjL1TbdOXr6TsWTubkBJWKCHBhnPjWxcXPP4HJ%2FC%2FpYU%3D&Expires=1745652781"


# Function to generate text for each cluster

def get_theme_strings(data):
    clusters = defaultdict(list)
    
    # Group items by cluster name
    for item in data:
        cluster = item["cluster name"]
        title = item["title"]
        description = item["description"]
        clusters[cluster].append(f"title: {title}, description: {description}")
    
    # Create a list of strings, each representing a cluster
    theme_strings = []
    for cluster_name, entries in clusters.items():
        combined_text = f"Theme: {cluster_name}, \n" + " \n".join(entries)
        theme_strings.append(combined_text)
    
    return theme_strings



#imgae prompt
def generate_image_prompt(json_structure_from_summarize_function):
    
    parsed_data = json.loads(re.sub(r'[\x00-\x1F\x7F]+', '', json_structure_from_summarize_function ))
    fetch_static_prompts()
    themes = get_theme_strings(parsed_data)
    
    img_urls = []
    img_alt_texts = []
    
    for theme in themes:
        prompt = f"{st.session_state.generate_image_prompt_text} Concept: {theme}\n"
        img_url = generate_image_from_gpt(prompt)
        img_alt_text = f"Image for {theme}"
        
        img_urls.append(img_url)
        img_alt_texts.append(img_alt_text)
    
    return img_urls, img_alt_texts



def structure_assistant_instructions(assistant_instructions_text):
    prompt = generate_assistant_instructions_prompt(assistant_instructions_text)
    response = client.chat.completions.create(
        model="gpt-4o",  # Use "gpt-4" if you prefer that model
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def preview_add_notes_function(notes_text, notes_category,delta):
    prompt = generate_add_notes_to_assistant_prompt(notes_text, notes_category,delta)
    response = client.chat.completions.create(
        model="gpt-4o",  # Use "gpt-4" if you prefer that model
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

    # Function to call openAI api with the structure assistant instruction prompt
#function to call openAI api with the summarize assistant instruction prompt
#use generate_assistant_instructions_prompt with gpt 4
#remove session state insitaitliation in local function

#archived functions

# def create_infographic(relationships_text):
#     G = nx.DiGraph()  # Directed graph
    
#     # Parse relationships from GPT response
#     relationships = relationships_text.split('\n')
#     for relation in relationships:
#         if '->' in relation:
#             src_dest, description = relation.split(':')
#             src, dest = src_dest.split('->')
#             G.add_edge(src.strip(), dest.strip(), label=description.strip())
    
#     # Plot the graph using matplotlib
#     plt.figure(figsize=(12, 8))  # Increase figure size for more space
#     pos = nx.spring_layout(G, k=0.5)  # Adjust k to control node spacing (higher = more space)
    
#     # Draw the nodes and edges
#     nx.draw(G, pos, with_labels=True, node_size=3000, node_color="lightblue", font_size=12, font_weight="bold", arrows=True)
    
#     # Extract edge labels (relationship descriptions)
#     labels = nx.get_edge_attributes(G, 'label')
    
#     # Increase font size and adjust positioning of edge labels
#     nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, font_color='red', font_size=10, label_pos=0.5, bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.3'))
    
#     # Save the plot to a buffer
#     buf = BytesIO()
#     plt.savefig(buf, format='png', bbox_inches='tight')  # bbox_inches ensures better fitting of the graph
#     buf.seek(0)
    
#     return buf
