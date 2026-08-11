import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


class LeadAnalysis(BaseModel):
    name: str
    title: str
    company: str
    location: str
    interest: str
    lead_score: int
    qualified: bool


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY was not found.")

client = OpenAI(api_key=api_key)


lead_information = """
John Smith
CEO
ABC Manufacturing
Boston
Interested in AI automation and process optimization.
"""


response = client.responses.parse(
    model="gpt-5-mini",
    input=[
        {
            "role": "system",
            "content": (
                "You are a B2B lead qualification analyst. "
                "Analyze the provided lead information. "
                "Do not invent information that is not provided."
            ),
        },
        {
            "role": "user",
            "content": lead_information,
        },
    ],
    text_format=LeadAnalysis,
)


lead = response.output_parsed

print("\nCYMERK LEAD ANALYSIS\n")
print(f"Name: {lead.name}")
print(f"Title: {lead.title}")
print(f"Company: {lead.company}")
print(f"Location: {lead.location}")
print(f"Interest: {lead.interest}")
print(f"Lead Score: {lead.lead_score}")
print(f"Qualified: {lead.qualified}")