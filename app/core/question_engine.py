FIELD_QUESTIONS = {
    # user fields
    "user-id":            "Please provide the user ID",
    "name":               "Please provide the user name",
    "user-pin":           "Please provide the user PIN",
    "user-active":        "Is the user active? (0 = inactive, 1 = active)",
    "vip":                "Is this a VIP user? (0 = no, 1 = yes)",
    "card1":              "Please provide card 1 number",
    "card2":              "Please provide card 2 number",
    "user-group":         "Please provide the user group (0–999)",
    "validity-date-dd":   "Please provide the validity day (1–31)",
    "validity-date-mm":   "Please provide the validity month (1–12)",
    "validity-date-yyyy": "Please provide the validity year (2000–2099)",
    "validity-time-hh":   "Please provide the validity hour (0–23)",
    "validity-time-mm":   "Please provide the validity minute (0–59)",
    # enroll fields
    "enroll-finger-count": "How many fingers to enrol? (1–10)",
    "enroll-palm-count":   "How many palms to enrol? (1–2)",
    "enroll-card-count":   "How many cards to enrol? (1–5)",
    "enroll-on-device":    "Enrol on device? (0 = no, 1 = yes)",
    "enroll-using":        "Enrol using numeric (0) or alphanumeric (1) ID?",
    "enroll-mode":         "Enrol mode: single template (0) or dual template (1)?",
    # access-setting fields
    "week-day":      "Which day of the week? (0 = Sunday … 6 = Saturday)",
    "work-start-hh": "Work start hour? (0–23)",
    "work-start-mm": "Work start minute? (0–59)",
    "work-end-hh":   "Work end hour? (0–23)",
    "work-end-mm":   "Work end minute? (0–59)",
}


def generate_question(missing_fields: list) -> str:
    msgs = [FIELD_QUESTIONS.get(f, f"Please provide {f}") for f in missing_fields]
    return " | ".join(msgs)
