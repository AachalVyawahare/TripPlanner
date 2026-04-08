def clean_text(text):
    if not text:
        return ""

    replacements = ["```json", "```", "**", "###", "##", "*", "---"]

    for token in replacements:
       text = text.replace(token, "")

    return text.strip()
