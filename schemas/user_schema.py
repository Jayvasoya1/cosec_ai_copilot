USER_SCHEMA = {
    "group": "users",

    "actions": {
        "set": {
            "required": ["user-id", "name"],
            "optional": [
                "user-active",
                "vip",
                "user-pin",
                "card1",
                "user-group"
            ]
        },

        "delete": {
            "required": ["user-id"],
            "optional": []
        }
    }
}