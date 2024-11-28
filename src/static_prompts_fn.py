#imgae prompt
def generate_image_prompt(relationships_text):
    prompt = (
        "Create a visually clear and legible image or flowchart that depicts the relationships between the following topics. "
        "Ensure that the relationships and descriptions are visible and understandable. Use arrows or visual elements "
        "to show how the topics are interconnected. Adhere to minimilastic design. The relationships between elements should be easy to read left to right%\n\n"
        f"Relationships: {relationships_text}\n\n"
    )
    return prompt