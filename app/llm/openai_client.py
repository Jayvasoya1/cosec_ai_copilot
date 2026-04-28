from openai import OpenAI
from app.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are an intent detection engine for a security system.

Return ONLY JSON. No explanation.

Format:
{
  "tasks": [
    {
      "intent": "",
      "parameters": {}
    }
  ]
}

Supported intents:
- add_user (name, user_id)
- delete_user (user_id)
- update_user (user_id, name)

Examples:

Input: Add user Ravi with id 101
Output:
{
  "tasks": [
    {
      "intent": "add_user",
      "parameters": {
        "name": "Ravi",
        "user_id": "101"
      }
    }
  ]
}

Input: Add Ravi and delete user 102
Output:
{
  "tasks": [
    {
      "intent": "add_user",
      "parameters": {
        "name": "Ravi"
      }
    },
    {
      "intent": "delete_user",
      "parameters": {
        "user_id": "102"
      }
    }
  ]
}
"""

def call_llm(user_input: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input}
        ]
    )

    return response.choices[0].message.content