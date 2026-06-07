import os
from dotenv import load_dotenv

# Try loading from .env.bridge as standard
load_dotenv(".env.bridge")
# Try loading from .env.gemini.local just in case
load_dotenv(".env.gemini.local")

key = os.getenv("MISTRAL_API_KEY")
if key:
    print(f"Key found: {key[:5]}...{key[-5:]}")
else:
    print("Key NOT found in environment.")
