import os

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get API key securely
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY was not found.")

# Create OpenAI client
client = OpenAI(api_key=api_key)

# Send our first request to an AI model
response = client.responses.create(
    model="gpt-5-mini",
    input="Explain what an AI agent is in simple terms."
)

# Print the model's response
print("\nCYMERK AI RESPONSE:\n")
print(response.output_text)