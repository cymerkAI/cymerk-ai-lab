import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from crm_tools import create_crm_lead


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError("OPENAI_API_KEY was not found.")

client = OpenAI(api_key=api_key)


tools = [
    {
        "type": "function",
        "name": "create_crm_lead",
        "description": "Create a new lead record in the CRM.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Full name of the lead",
                },
                "title": {
                    "type": "string",
                    "description": "Job title of the lead",
                },
                "company": {
                    "type": "string",
                    "description": "Company name",
                },
                "lead_score": {
                    "type": "integer",
                    "description": "Lead score from 0 to 100",
                },
            },
            "required": [
                "name",
                "title",
                "company",
                "lead_score",
            ],
            "additionalProperties": False,
        },
    }
]


lead_information = """
John Smith
CEO
ABC Manufacturing
Boston
Interested in AI automation and process optimization.
"""


response = client.responses.create(
    model="gpt-5-mini",
    instructions=(
        "You are a B2B lead qualification agent. "
        "Analyze the lead information. "
        "If appropriate, call the create_crm_lead tool."
    ),
    input=lead_information,
    tools=tools,
)


tool_call = None

for item in response.output:
    if item.type == "function_call":
        tool_call = item
        break


if tool_call is None:
    print("\nNo tool call was requested.")
    print(response.output_text)
    raise SystemExit


print("\nAI REQUESTED TOOL:")
print(tool_call.name)


arguments = json.loads(tool_call.arguments)

print("\nTOOL ARGUMENTS:")
print(arguments)


result = create_crm_lead(
    name=arguments["name"],
    title=arguments["title"],
    company=arguments["company"],
    lead_score=arguments["lead_score"],
)


print("\nTOOL RESULT:")
print(result)


tool_result = {
    "type": "function_call_output",
    "call_id": tool_call.call_id,
    "output": json.dumps(result),
}


final_response = client.responses.create(
    model="gpt-5-mini",
    previous_response_id=response.id,
    instructions=(
        "You are a B2B lead qualification agent. "
        "Explain the CRM operation result clearly and concisely."
    ),
    input=[tool_result],
)


print("\nFINAL AI RESPONSE:")
print(final_response.output_text)