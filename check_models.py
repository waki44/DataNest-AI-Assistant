import json
from google import genai

with open("config.json", "r") as f:
    key = json.load(f)["GEMINI_API_KEY"]

client = genai.Client(api_key=key)

print("Aapke account par chalne wale models:")
for m in client.models.list():
    if "generateContent" in m.supported_actions:
        print(f"- {m.name}")
        