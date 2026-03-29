import json
from utils import load_schemes, format_scheme_cards
from eligibility import check_eligibility


# ---------------------------
# SIMPLE USER EXTRACTION
# ---------------------------
def extract_user_details(text):

    text = text.lower()

    user = {
        "age": None,
        "gender": None,
        "annualIncome": None,
        "occupation": [],
        "state": "",
    }

    # occupation
    if "farmer" in text:
        user["occupation"].append("farmer")
    if "student" in text:
        user["occupation"].append("student")

    # gender
    if "female" in text:
        user["gender"] = "female"
    if "male" in text:
        user["gender"] = "male"

    # state
    states = ["maharashtra", "karnataka", "rajasthan", "up", "gujarat"]
    for s in states:
        if s in text:
            user["state"] = s

    # income
    import re
    match = re.search(r'\d+', text)
    if match:
        user["annualIncome"] = int(match.group())

    return user


# ─────────────────────────────────────────────
# MAIN FUNCTION
# ---------------------------
def process_query(user_input, history=[]):

    text = user_input.lower()
    schemes_data = load_schemes()

    # ---------------------------
    # GREETING
    # ---------------------------
    if text in ["hi", "hello", "hey"]:
        return {
            "text": "Hello 👋 Tell me about yourself (e.g. farmer from Maharashtra earning 2 lakh)",
            "schemes": []
        }

    # ---------------------------
    # DIRECT SCHEME SEARCH
    # ---------------------------
    matched = []
    for s in schemes_data["schemes"]:
        name = s["scheme_name"].lower()
        short_name = s.get("short_name", "").lower()

        # Strict full name or short name match (No word-split matching)
        if name in text or (short_name and short_name in text):
            matched.append(s)

    if matched:
        return {
            "text": "Here is the scheme you explicitly asked about:",
            "schemes": format_scheme_cards(matched)
        }

    # ---------------------------
    # EXTRACT USER DATA
    # ---------------------------
    user_data = extract_user_details(text)

    # ---------------------------
    # FILTER LOGIC
    # ---------------------------
    scored = []

    for s in schemes_data["schemes"]:
        score = 0
        full = s
        eligibility = full.get("eligibility", {})

        # 1. STRICT OCCUPATION FILTERING
        scheme_occupations = [o.lower() for o in eligibility.get("occupation", [])]
        user_occupations = user_data["occupation"]
        
        if scheme_occupations and user_occupations:
            match_found = False
            for u_occ in user_occupations:
                for s_occ in scheme_occupations:
                    if u_occ in s_occ or s_occ in u_occ:
                        match_found = True
                        break
            if not match_found:
                continue  # STRICT REJECT: Occupation mismatch!
            
            score += 5
        elif user_occupations and not scheme_occupations:
            # Scheme is generic, lower bonus
            score += 1

        # 2. STRICT GENDER FILTERING
        elig_gender = eligibility.get("gender", "any").lower()
        user_gender = user_data.get("gender")
        if user_gender:
            if elig_gender != "any" and elig_gender != "all" and elig_gender != user_gender:
                continue  # STRICT REJECT: Gender mismatch!
            elif elig_gender == user_gender:
                score += 5

        # 3. STATE MATCH
        user_state = str(user_data.get("state") or "").lower()
        scheme_state = str(full.get("applicable_state") or "").lower()
        if user_state:
            if scheme_state != "all" and scheme_state != user_state:
                continue  # STRICT REJECT: State mismatch!
            elif scheme_state == user_state:
                score += 3
            else:
                score += 1

        # 4. KEYWORD INTENT
        cat = full.get("category", "").lower()
        tags = " ".join(full.get("tags") or []).lower()
        
        # Comprehensive keyword triggers
        if any(w in text for w in ["scholarship", "study", "education"]):
            if "education" in cat or "scholarship" in tags or "student" in tags:
                score += 5
                
        if any(w in text for w in ["loan", "fund", "money", "business"]):
            if "business" in cat or "loan" in tags or "funding" in tags:
                score += 5
                
        if any(w in text for w in ["pension", "retirement"]):
            if "pension" in cat:
                score += 5
                
        if any(w in text for w in ["farmer", "agriculture", "kisan"]):
            if "agriculture" in cat or "farmer" in tags:
                score += 5
                
        if any(w in text for w in ["health", "medical", "hospital", "insurance"]):
            if "health" in cat or "medical" in tags or "insurance" in tags:
                score += 5
                
        if any(w in text for w in ["house", "home", "housing"]):
            if "housing" in cat:
                score += 5

        if score > 0:
            scored.append((score, s))

    # sort
    scored.sort(reverse=True, key=lambda x: x[0])

    # Dynamic check for specifics
    has_specifics = bool(
        user_data["occupation"] or user_data["gender"] or user_data["state"] or
        any(w in text for w in ["scholarship", "loan", "pension", "health", "fund", "house", "medical", "insurance", "student", "farmer"])
    )

    # Filter generic low-score weak matches if user gave specifics
    if has_specifics:
        top = [s for score, s in scored if score >= 3][:5]
    else:
        top = [s for _, s in scored[:5]]

    if not top:
        return {
            "text": "No relevant schemes found. Try giving more details.",
            "schemes": []
        }

    return {
        "text": "Here are relevant schemes for you:",
        "schemes": format_scheme_cards(top)
    }