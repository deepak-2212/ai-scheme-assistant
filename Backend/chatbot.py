import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from googletrans import Translator
from eligibility import check_eligibility

# ─────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────

load_dotenv()

client = OpenAI()
translator = Translator()

# Load schemes ONCE
with open("schemes.json", encoding="utf-8") as f:
    SCHEMES_DATA = json.load(f)


# ─────────────────────────────────────────────
# TRANSLATION (SAFE)
# ─────────────────────────────────────────────

def to_english(text):
    try:
        return translator.translate(text, dest="en").text
    except:
        return text


def to_user_lang(text, lang):
    try:
        return translator.translate(text, dest=lang).text
    except:
        return text


# ─────────────────────────────────────────────
# SPEECH TO TEXT (OPTIONAL)
# ─────────────────────────────────────────────

def speech_to_text(audio_file):
    transcript = client.audio.transcriptions.create(
        model="gpt-4o-mini-transcribe",
        file=audio_file
    )
    return transcript.text


# ─────────────────────────────────────────────
# EXTRACT USER DETAILS
# ─────────────────────────────────────────────

def extract_user_details(user_input):

    prompt = f"""
Extract user details and return ONLY JSON:

{{
 "age": 25,
 "gender": "male/female",
 "annualIncome": 100000,
 "occupation": ["farmer/student/other"],
 "state": "state name",
 "residence": "rural/urban",
 "hasLand": true/false,
 "hasBankAccount": true/false,
 "hasRationCard": true/false,
 "rationCardType": "AAY/PHH/APL/other",
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
        user_data = {
            "age": 30,
            "gender": "male",
            "annualIncome": 100000,
            "occupation": ["farmer"],
            "state": "Maharashtra",
            "residence": "rural",
            "hasLand": True,
            "hasBankAccount": True,
            "hasRationCard": True,
            "rationCardType": "PHH",
            "isIncomeTaxpayer": False,
            "isGovtEmployee": False
        }

    # DEFAULT VALUES
    user_data.setdefault("occupation", ["other"])
    user_data.setdefault("hasLand", False)
    user_data.setdefault("hasBankAccount", True)
    user_data.setdefault("hasRationCard", True)
    user_data.setdefault("rationCardType", "PHH")
    user_data.setdefault("residence", "rural")

    user_data.setdefault("isProfessional", False)
    user_data.setdefault("hasOwnHouse", False)
    user_data.setdefault("isEPFOorESICCovered", False)
    user_data.setdefault("numberOfChildren", 1)
    user_data.setdefault("isSecc2011Listed", True)
    user_data.setdefault("isAadhaarLinked", True)
    user_data.setdefault("hasLPGConnection", False)
    user_data.setdefault("receivedGovtFunding", False)
    user_data.setdefault("category", "General")

    return user_data


# ─────────────────────────────────────────────
# FORMAT SCHEMES
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# EXPLAIN SCHEMES
# ─────────────────────────────────────────────

def explain_schemes(user_data, schemes):

    formatted = format_schemes(schemes)

    prompt = f"""
You are a Government Scheme Assistant.

User Profile:
{user_data}

Eligible Schemes:
{formatted}

Explain clearly:
- why user is eligible
- benefits
- documents needed
- steps to apply

Keep it simple.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ─────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────

def process_query(user_input):

    # Detect language
    try:
        lang = translator.detect(user_input).lang
    except:
        lang = "en"

    # Translate
    english = to_english(user_input)

    # Extract user data
    user_data = extract_user_details(english)

    # Check eligibility
    result = check_eligibility(user_data, SCHEMES_DATA)

    schemes = result["eligible"]

    if not schemes:
        return to_user_lang("No matching schemes found for your profile.", lang)

    # Explain
    explanation = explain_schemes(user_data, schemes)

    # Translate back
    return to_user_lang(explanation, lang)