FIELD_QUESTIONS = {
    # user fields
    "user-id":            "What is the user ID? (e.g. 101)",
    "name":               "What is the user's name?",
    "user-pin":           "What PIN should be set for this user?",
    "user-active":        "Should the user be active? Reply 1 for active or 0 for inactive.",
    "vip":                "Is this a VIP user? Reply 1 for yes or 0 for no.",
    "card1":              "What is the card 1 number for this user?",
    "card2":              "What is the card 2 number for this user?",
    "user-group":         "Which user group should this user belong to? (0–999)",
    "validity-date-dd":   "What is the validity day? (1–31)",
    "validity-date-mm":   "What is the validity month? (1–12)",
    "validity-date-yyyy": "What is the validity year? (e.g. 2025)",
    "validity-time-hh":   "What is the validity hour? (0–23)",
    "validity-time-mm":   "What is the validity minute? (0–59)",
    # enroll fields
    "enroll-finger-count": "How many fingers should be enrolled? (1–10)",
    "enroll-palm-count":   "How many palms should be enrolled? (1–2)",
    "enroll-card-count":   "How many cards should be enrolled? (1–5)",
    "enroll-on-device":    "Should enrollment happen on the device? Reply 1 for yes or 0 for no.",
    "enroll-using":        "Should enrollment use a numeric (0) or alphanumeric (1) ID?",
    "enroll-mode":         "Which enroll mode? Reply 0 for single template or 1 for dual template.",
    # access-setting fields
    "week-day":      "Which day of the week? (0 = Sunday, 1 = Monday, … 6 = Saturday)",
    "work-start-hh": "What hour should work start? (0–23, 24-hour format)",
    "work-start-mm": "What minute should work start? (0–59)",
    "work-end-hh":   "What hour should work end? (0–23, 24-hour format)",
    "work-end-mm":   "What minute should work end? (0–59)",
    # door config fields
    "pdid":               "What is the door ID?",
    "door-name":          "What should the door be named?",
    "door-type":          "What is the door type?",
    "communication-type": "What communication type should be used?",
    "ip-address":         "What is the IP address for this door?",
    "mac-address":        "What is the MAC address for this door?",
}

# Groups of fields that naturally belong together in one question
_GROUPED_QUESTIONS = {
    frozenset(["work-start-hh", "work-start-mm"]): "What time should work start? (e.g. 9:00 or 9 AM)",
    frozenset(["work-end-hh", "work-end-mm"]):     "What time should work end? (e.g. 18:00 or 6 PM)",
    frozenset(["validity-date-dd", "validity-date-mm", "validity-date-yyyy"]): "What is the validity date? (DD MM YYYY)",
}


def generate_question(missing_fields: list) -> str:
    remaining = list(missing_fields)
    questions = []

    # Try grouped questions first
    for field_set, question in _GROUPED_QUESTIONS.items():
        if field_set.issubset(set(remaining)):
            questions.append(question)
            remaining = [f for f in remaining if f not in field_set]

    # Individual questions for the rest
    for f in remaining:
        questions.append(FIELD_QUESTIONS.get(f, f"Please provide: {f}"))

    return "  \n".join(questions)
