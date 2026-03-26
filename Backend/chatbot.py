import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from googletrans import Translator
from eligibility import check_eligibility   # ✅ NEW

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
# Extract User Details (UPDATED)
# ---------------------------
def extract_user_details(user_input):

    prompt = f"""
Extract user information and return JSON:

{{
 "age": 25,
 "gender": "male/female",
 "annualIncome": 100000,
 "occupation": ["farmer/student/other"],
 "state": "state name",
 "residence": "rural/urban",
 "hasLand": true/false,
 "hasBankAccount": true/false,
 "isIncomeTaxpayer": false,
 "isGovtEmployee": false
}}

Input: {user_input}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    text = response.choices[0].message.content.strip()

    try:
        user_data = json.loads(text)
    except:
        # fallback (VERY IMPORTANT)
        user_data = {
            "age": 30,
            "gender": "male",
            "annualIncome": 100000,
            "occupation": ["farmer"],
            "state": "Maharashtra",
            "residence": "rural",
            "hasLand": True,
            "hasBankAccount": True,
            "isIncomeTaxpayer": False,
            "isGovtEmployee": False
        }

    # ensure defaults (avoid crashes)
    user_data.setdefault("occupation", ["other"])
    user_data.setdefault("hasLand", False)
    user_data.setdefault("hasBankAccount", True)
    user_data.setdefault("residence", "rural")

    return user_data


# ---------------------------
# Format Schemes
# ---------------------------
def format_schemes(schemes):

    formatted = []

    for s in schemes:
        formatted.append({
            "name": s["scheme_name"],
            "benefit": s["benefits"],
            "apply": s["apply_url"],
            "reasons": s["reasons"]
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

Eligible Schemes:
{formatted}

Explain each scheme simply.

Include:
- why eligible
- benefits
- reasons
- how to apply
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ---------------------------
# MAIN FUNCTION (UPDATED)
# ---------------------------
def process_query(user_input):

    # detect language
    lang = translator.detect(user_input).lang

    # translate
    english = to_english(user_input)

    # extract full user profile
    user_data = extract_user_details(english)

    # load schemes
    with open("schemes.json", encoding="utf-8") as f:
        schemes_data = json.load(f)

    # use advanced eligibility engine
    result = check_eligibility(user_data, schemes_data)

    schemes = result["eligible"]

    if not schemes:
        return "No matching schemes found."

    # explain
    explanation = explain_schemes(user_data, schemes)

    # translate back
    final = to_user_lang(explanation, lang)

    return final