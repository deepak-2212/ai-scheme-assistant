import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from googletrans import Translator

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
translator = Translator()


# ---------------------------
# Translate
# ---------------------------
def to_english(text):
    return translator.translate(text, dest="en").text

def to_user_lang(text, lang):
    return translator.translate(text, dest=lang).text

# ---------------------------
# Speech to Text
# ---------------------------
def speech_to_text(audio_file):

    transcript = client.audio.transcriptions.create(
        model="gpt-4o-mini-transcribe",
        file=audio_file
    )

    return transcript.text

# ---------------------------
# Extract User Details
# ---------------------------
def extract_user_details(user_input):

    prompt = f"""
Extract:
- occupation (student/farmer/other)
- gender (male/female)
- income (number only)

Return ONLY JSON:
{{
 "occupation": "",
 "gender": "",
 "income": 0
}}

Input: {user_input}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content.strip()

    return json.loads(text)


# ---------------------------
# Format Schemes (IMPORTANT)
# ---------------------------
def format_schemes(schemes):

    formatted = []

    for s in schemes:
        formatted.append({
            "name": s["scheme_name"],
            "benefit": s["benefits"]["summary"],
            "documents": s["documents_required"],
            "apply": s["application"]["apply_url"]
        })

    return formatted


# ---------------------------
# Explain Schemes
# ---------------------------
def explain_schemes(user_data, schemes):

    formatted = format_schemes(schemes)

    prompt = f"""
You are a Government Scheme Assistant.

User:
{user_data}

Schemes:
{formatted}

Explain each scheme simply.

Include:
- why eligible
- benefits
- documents
- how to apply
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ---------------------------
# MAIN FUNCTION
# ---------------------------
def process_query(user_input, find_schemes):

    # detect language
    lang = translator.detect(user_input).lang

    # translate
    english = to_english(user_input)

    # extract
    user_data = extract_user_details(english)

    # match schemes
    schemes = find_schemes(
        user_data["income"],
        user_data["gender"],
        user_data["occupation"]
    )

    if not schemes:
        return "No matching schemes found."

    # explain
    explanation = explain_schemes(user_data, schemes)

    # translate back
    final = to_user_lang(explanation, lang)

    return final