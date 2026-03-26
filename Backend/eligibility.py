import json

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def normalize(value):
    return (value or "").lower().strip()


def check_occupation(user_occupations, scheme_occupations):
    if not scheme_occupations:
        return True

    user_norm = [normalize(o) for o in (user_occupations or [])]

    for so in scheme_occupations:
        so_norm = normalize(so)
        for uo in user_norm:
            if so_norm in uo or uo in so_norm:
                return True
    return False


def check_state(user_state, scheme_state):
    if not scheme_state or normalize(scheme_state) == "all":
        return True
    return normalize(user_state) == normalize(scheme_state)


def check_age(user_age, min_age, max_age):
    if min_age is not None and user_age < min_age:
        return False
    if max_age is not None and user_age > max_age:
        return False
    return True


def check_gender(user_gender, scheme_gender):
    if not scheme_gender or normalize(scheme_gender) == "any":
        return True
    return normalize(user_gender) == normalize(scheme_gender)


def check_income(user_income, limit):
    if limit is None:
        return True
    return user_income <= limit


def check_residence(user_res, scheme_res):
    if not scheme_res or normalize(scheme_res) == "any":
        return True

    s = normalize(scheme_res)
    u = normalize(user_res)

    if "rural" in s and u == "rural":
        return True
    if "urban" in s and u == "urban":
        return True

    return False


# ─────────────────────────────────────────────
# EXCLUSION LOGIC
# ─────────────────────────────────────────────

def check_exclusions(user, exclusions):
    triggered = []

    for excl in exclusions or []:
        key = normalize(excl)

        if key == "income taxpayers" and user.get("isIncomeTaxpayer"):
            triggered.append(excl)

        elif key == "government employees" and user.get("isGovtEmployee"):
            triggered.append(excl)

        elif "professionals" in key and user.get("isProfessional"):
            triggered.append(excl)

        elif "pucca house" in key and user.get("hasOwnHouse"):
            triggered.append(excl)

        elif "received investment" in key and user.get("receivedGovtFunding"):
            triggered.append(excl)

        elif "epfo or esic" in key and user.get("isEPFOorESICCovered"):
            triggered.append(excl)

        elif "lpg connection" in key and user.get("hasLPGConnection"):
            triggered.append(excl)

        elif "more than 2 children" in key and user.get("numberOfChildren", 0) > 2:
            triggered.append(excl)

    return triggered


# ─────────────────────────────────────────────
# CUSTOM SCHEME RULES
# ─────────────────────────────────────────────

def custom_checks(user, scheme_id, notes):

    if scheme_id == "SCH-AGR-001":
        if not user.get("hasLand"):
            notes.append("Land ownership required.")
            return False
        return check_occupation(user.get("occupation"), ["farmer"])

    if scheme_id == "SCH-HLT-001":
        if not user.get("isSecc2011Listed"):
            notes.append("Must be listed in SECC 2011.")
            return False
        return True

    if scheme_id == "SCH-HSG-001":
        if user.get("hasOwnHouse"):
            notes.append("Must not own a pucca house.")
            return False
        if normalize(user.get("residence")) != "urban":
            notes.append("Only for urban residents.")
            return False
        return True

    if scheme_id == "SCH-EDU-001":
        if not check_occupation(user.get("occupation"), ["student"]):
            notes.append("Must be a student.")
            return False
        return True

    if scheme_id == "SCH-PEN-001":
        if user.get("isIncomeTaxpayer"):
            notes.append("Income taxpayers excluded.")
            return False
        return True

    if scheme_id == "SCH-ENR-001":
        if normalize(user.get("gender")) != "female":
            notes.append("Only for women.")
            return False
        if user.get("hasLPGConnection"):
            notes.append("Already has LPG connection.")
            return False
        return True

    return True


# ─────────────────────────────────────────────
# MAIN CHECK FUNCTION (SINGLE SCHEME)
# ─────────────────────────────────────────────

def check_scheme_eligibility(user, scheme):

    e = scheme["eligibility"]
    notes = []
    passed = True

    # STATE
    if not check_state(user.get("state"), scheme.get("applicable_state")):
        return {
            "status": "ineligible",
            "scheme_name": scheme["scheme_name"],
            "reasons": ["Not applicable for your state"]
        }

    # AGE
    if not check_age(user.get("age"), e.get("min_age"), e.get("max_age")):
        notes.append("Age criteria not satisfied")
        passed = False

    # GENDER
    if not check_gender(user.get("gender"), e.get("gender")):
        notes.append("Gender criteria not satisfied")
        passed = False

    # INCOME
    if not check_income(user.get("annualIncome"), e.get("annual_income_limit")):
        notes.append("Income exceeds limit")
        passed = False

    # RESIDENCE
    if not check_residence(user.get("residence"), e.get("residence")):
        notes.append("Residence criteria not satisfied")
        passed = False

    # LAND
    if e.get("land_required") and not user.get("hasLand"):
        notes.append("Land ownership required")
        passed = False

    # BANK
    if e.get("bank_account_required") and not user.get("hasBankAccount"):
        notes.append("Bank account required")
        passed = False

    # EXCLUSIONS
    exclusions = check_exclusions(user, e.get("exclusions"))
    if exclusions:
        notes.extend(exclusions)
        passed = False

    # CUSTOM CHECK
    if not custom_checks(user, scheme["scheme_id"], notes):
        passed = False

    return {
        "status": "eligible" if passed else "ineligible",
        "scheme_name": scheme["scheme_name"],
        "benefits": scheme["benefits"]["summary"],
        "reasons": notes,
        "apply_url": scheme["application"]["apply_url"]
    }


# ─────────────────────────────────────────────
# MAIN ENGINE (ALL SCHEMES)
# ─────────────────────────────────────────────

def check_eligibility(user, schemes_data):

    eligible = []
    ineligible = []

    for scheme in schemes_data["schemes"]:
        result = check_scheme_eligibility(user, scheme)

        if result["status"] == "eligible":
            eligible.append(result)
        else:
            ineligible.append(result)

    return {
        "eligible": eligible,
        "ineligible": ineligible,
        "summary": {
            "total": len(schemes_data["schemes"]),
            "eligible": len(eligible),
            "ineligible": len(ineligible)
        }
    }