#ignore this file
import json
import time
from collections import defaultdict
import streamlit as st
from openai import OpenAI
from functions import get_promptops_entries, fetch_static_prompts
import re
import streamlit as st

# Initialize OpenAI client
#client = OpenAI()

# --- Utilities ---

def clean_json_string(json_str):
    # Remove invalid control characters like newlines and tabs
    return re.sub(r'[\x00-\x1F\x7F]+', '', json_str)

def build_summarization_prompt(before_prompt, about_this, after_prompt, combined_text):
    """Builds the complete summarization prompt from parts."""
    return f"{before_prompt} {about_this} {after_prompt} {combined_text}"

# --- Main Functions ---

def fetch_and_summarize_entries(component):
    """Fetch notes, summarize via function calling, fallback to prompt if needed."""
    fetch_static_prompts()  # Assume this loads prompts into st.session_state
    entries = get_promptops_entries(component)
    
    filtered_entries = [
        entry for entry in entries
        if not entry.get('do_not_stage', False) and entry['title'] != '#'
    ]

    about_this = next(
        (entry['description'] for entry in entries if entry['title'] == '#'),
        ""
    )

    if not filtered_entries:
        return "No topics to summarize."

    combined_text = "\n".join(
        f"Title: {entry['title']}, Description: {entry['description']}"
        for entry in filtered_entries
    )

    before_prompt, after_prompt = st.session_state.summarize_before_image_prompt_text.split("|")
    full_prompt = build_summarization_prompt(before_prompt, about_this, after_prompt, combined_text)

    # Prepare function definition (this is your expected structure)
    functions = [
    {
        "name": "summarize_notes",
        "description": "Cluster notes and return them in structured JSON",
        "parameters": {
            "type": "object",
            "properties": {
                "notes": {   # wrap the array inside an object under 'notes'
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "cluster name": {"type": "string"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                        },
                        "required": ["cluster name", "title", "description"]
                    }
                }
            },
            "required": ["notes"]  # <- important: require the "notes" field
        }
    }
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": full_prompt}],
            functions=functions,
            function_call={"name": "summarize_notes"},
        )

        if response.choices[0].finish_reason == "function_call":
            args = response.choices[0].message.function_call.arguments
            parsed = json.loads(args)
            return json.dumps(parsed)  # Return as string for consistency

    except Exception as e:
        print(f"Function call failed: {e}")
        # Retry once after short delay
        time.sleep(2)
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": full_prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e2:
            print(f"Fallback also failed: {e2}")
            return "Error during summarization."

def generate_image_prompt(json_structure_from_summarize_function):
    """Generate image prompts based on summarized notes."""
    cleaned_json = clean_json_string(json_structure_from_summarize_function)
    st.write(f"Cleaned JSON: {cleaned_json}")
    parsed_data = json.loads(cleaned_json)
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

def get_theme_strings(data):
    """Group notes into themes."""
    clusters = defaultdict(list)

    for item in data:
        cluster = item["cluster name"]
        title = item["title"]
        description = item["description"]
        clusters[cluster].append(f"title: {title}, description: {description}")

    theme_strings = []
    for cluster_name, entries in clusters.items():
        combined_text = f"Theme: {cluster_name}, \n" + " \n".join(entries)
        theme_strings.append(combined_text)

    return theme_strings

def generate_image_from_gpt(prompt):
    """Generate an image from DALL-E based on a prompt."""
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    return image_url
