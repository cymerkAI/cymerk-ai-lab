import json
import sys
from pathlib import Path

from openai import OpenAI

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# CYMERK TOOLS
# ============================================================

from agent_tools import (
    search_knowledge,
    create_lead,
)


from permissions import check_tool_permission


# ============================================================
# OPENAI CLIENT
# ============================================================

client = OpenAI()


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOLS = [
    {
        "type": "function",
        "name": "search_knowledge",
        "description": (
            "Search the Cymerk company knowledge base. "
            "Use this for questions about Cymerk services, "
            "security, human approval, implementation "
            "approach, client use cases, policies, "
            "and company information."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Question or topic to search "
                        "in the Cymerk knowledge base."
                    ),
                }
            },
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "create_lead",
        "description": (
            "Create a new CRM lead. "
            "This action requires human approval. "
            "The tool creates an approval request first "
            "and does not create the CRM record until "
            "approval is granted and the approved action "
            "is executed separately."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                },
                "title": {
                    "type": "string",
                },
                "company": {
                    "type": "string",
                },
                "lead_score": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                },
            },
            "required": [
                "name",
                "title",
                "company",
                "lead_score",
            ],
        },
    },
]


# ============================================================
# AGENT INSTRUCTIONS
# ============================================================

AGENT_INSTRUCTIONS = (
    "You are the Cymerk AI agent. "

    "For questions about Cymerk company information, "
    "always use the search_knowledge tool before answering. "

    "The Cymerk knowledge base is authoritative. "

    "Never invent company information. "

    "Never use public web search. "

    "If the knowledge base has no relevant information, "
    "say that the information is not available in the "
    "Cymerk knowledge base. "

    "When relevant information is returned, answer "
    "the original question directly using that information. "

    "For implementation approach questions, use the "
    "Implementation Approach section and provide "
    "the eight stages. "

    "For client use-case questions, use the "
    "Typical Client Use Cases section. "

    "For human approval questions, use the "
    "Human Approval section. "

    "For security questions, use the Security section "
    "and specifically identify the least-privilege principle. "

    "Use create_lead only when the user explicitly "
    "asks to create a CRM lead. "

    "CRM creation requires human approval. "

    "When create_lead is called, explain that the CRM "
    "lead is pending human approval and that the "
    "approval request must be resolved before execution. "

    "Do not claim that a CRM record was created merely "
    "because an approval request was created. "

    "Do not expose raw JSON or tool calls."
)


# ============================================================
# KNOWLEDGE SEARCH TOOL
# ============================================================

def search_knowledge_tool(query):
    """
    Search the Cymerk knowledge base.

    Common Cymerk questions are normalized to improve
    retrieval reliability.
    """

    normalized_query = query.lower().strip()

    # --------------------------------------------------------
    # SECURITY
    # --------------------------------------------------------

    if (
        "security" in normalized_query
        or "secure" in normalized_query
        or "privacy" in normalized_query
        or "least privilege" in normalized_query
        or "least-privilege" in normalized_query
        or "confidential" in normalized_query
        or "authorization" in normalized_query
        or "security principle" in normalized_query
    ):
        query = (
            "Cymerk security principle "
            "least privilege "
            "least-privilege "
            "tools data authorization "
            "confidential information"
        )

    # --------------------------------------------------------
    # IMPLEMENTATION APPROACH
    # --------------------------------------------------------

    elif (
        "implementation" in normalized_query
        or "implement" in normalized_query
        or "deployment approach" in normalized_query
    ):
        query = (
            "Cymerk implementation approach "
            "AI projects stages"
        )

    # --------------------------------------------------------
    # CLIENT USE CASES
    # --------------------------------------------------------

    elif (
        "use case" in normalized_query
        or "use cases" in normalized_query
        or "client examples" in normalized_query
    ):
        query = (
            "Cymerk typical client use cases "
            "lead qualification CRM automation "
            "customer support document analysis"
        )

    # --------------------------------------------------------
    # HUMAN APPROVAL
    # --------------------------------------------------------

    elif (
        "human approval" in normalized_query
        or "approval" in normalized_query
    ):
        query = (
            "Cymerk human approval high-impact actions "
            "financial transactions customer record changes "
            "external communications"
        )

    # --------------------------------------------------------
    # EXECUTE SEARCH
    # --------------------------------------------------------

    result = search_knowledge(query)

    # --------------------------------------------------------
    # EMPTY RESULT
    # --------------------------------------------------------

    if not result.get("results"):
        return json.dumps(
            {
                "success": True,
                "results": [],
                "message": (
                    "No relevant information was found "
                    "in the Cymerk knowledge base."
                ),
            },
            indent=2,
        )

    # --------------------------------------------------------
    # RETURN RESULTS
    # --------------------------------------------------------

    return json.dumps(
        result,
        indent=2,
    )


# ============================================================
# CRM TOOL
# ============================================================

def create_lead_tool(
    name,
    title,
    company,
    lead_score,
):
    """
    Create a CRM lead approval request.

    Validation, approval creation, and audit logging
    are handled by agent_tools.create_lead().

    This function does not directly create the CRM record.
    """

    result = create_lead(
        name=name,
        title=title,
        company=company,
        lead_score=lead_score,
    )

    return json.dumps(
        result,
        indent=2,
    )


# ============================================================
# AGENT
# ============================================================

def run_agent(user_message):
    """
    Run the Cymerk RAG + CRM agent.

    The agent follows a tool-execution loop:

        1. Send the user's request to the model.
        2. Detect any requested function calls.
        3. Check permissions.
        4. Execute authorized tools.
        5. Send tool results back to the model.
        6. Repeat until the model returns a final answer.

    CRM approval remains separate from CRM execution.

    create_lead:
        Creates a pending approval request.

    approve_crm_lead:
        Is handled outside this agent tool loop.

    execute_approved_crm_lead:
        Is handled separately after approval.
    """

    # --------------------------------------------------------
    # INITIAL MODEL REQUEST
    # --------------------------------------------------------

    response = client.responses.create(
        model="gpt-5-mini",
        instructions=AGENT_INSTRUCTIONS,
        input=user_message,
        tools=TOOLS,
        tool_choice="required",
    )

    # --------------------------------------------------------
    # SINGLE TOOL EXECUTION LOOP
    # --------------------------------------------------------

    while True:

        # ----------------------------------------------------
        # FIND TOOL CALLS
        # ----------------------------------------------------

        tool_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        # ----------------------------------------------------
        # NO TOOL CALLS = FINAL RESPONSE
        # ----------------------------------------------------

        if not tool_calls:
            return response.output_text

        tool_outputs = []

        # ----------------------------------------------------
        # EXECUTE EACH TOOL CALL
        # ----------------------------------------------------

        for tool_call in tool_calls:

            arguments = json.loads(
                tool_call.arguments
            )

            # ------------------------------------------------
            # PERMISSION CHECK
            # ------------------------------------------------

            permission = check_tool_permission(
                tool_call.name
            )

            if not permission["allowed"]:

                result = json.dumps(
                    {
                        "success": False,
                        "status": "permission_denied",
                        "error": permission["reason"],
                    },
                    indent=2,
                )

            # ------------------------------------------------
            # KNOWLEDGE SEARCH
            # ------------------------------------------------

            elif tool_call.name == "search_knowledge":

                result = search_knowledge_tool(
                    arguments["query"]
                )

            # ------------------------------------------------
            # CRM LEAD REQUEST
            # ------------------------------------------------

            elif tool_call.name == "create_lead":

                result = create_lead_tool(
                    name=arguments["name"],
                    title=arguments["title"],
                    company=arguments["company"],
                    lead_score=arguments["lead_score"],
                )

            # ------------------------------------------------
            # UNKNOWN TOOL
            # ------------------------------------------------

            else:

                result = json.dumps(
                    {
                        "success": False,
                        "status": "unknown_tool",
                        "error": (
                            f"Unknown tool: "
                            f"{tool_call.name}"
                        ),
                    },
                    indent=2,
                )

            # ------------------------------------------------
            # PACKAGE TOOL RESULT
            # ------------------------------------------------

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": result,
                }
            )

        # ----------------------------------------------------
        # SEND TOOL RESULTS BACK TO MODEL
        # ----------------------------------------------------

        response = client.responses.create(
            model="gpt-5-mini",
            instructions=(
                "Answer the user's original question "
                "using the tool results. "

                "The tool results are authoritative. "

                "If the search tool returned an empty "
                "results list, you MUST explicitly state "
                "that the information is not available "
                "in the Cymerk knowledge base. "

                "For example: "
                "\"I couldn't find that information in "
                "the Cymerk knowledge base.\" "

                "Do not answer an empty retrieval result "
                "using general knowledge or assumptions. "

                "If relevant information is present, "
                "answer using only that information. "

                "For a Security question, if the retrieved "
                "Security section states least-privilege, "
                "explain that Cymerk follows the "
                "least-privilege principle: agents should "
                "only have access to the tools and data "
                "required for their assigned tasks. "

                "For an Implementation Approach question, "
                "give the eight stages from the retrieved "
                "Implementation Approach section. "

                "Do not replace those stages with a "
                "generic explanation of implementation. "

                "For CRM lead creation, distinguish clearly "
                "between requesting approval and actually "
                "creating the CRM record. "

                "If create_lead returns "
                "\"pending_approval\", state that human "
                "approval is required before the CRM record "
                "can be created. "

                "Do not claim that a CRM record was created "
                "when the tool only created an approval "
                "request. "

                "Do not perform a public web search. "
                "Do not invent information. "
                "Do not expose raw JSON or tool calls."
            ),
            previous_response_id=response.id,
            input=tool_outputs,
        )


# ============================================================
# COMMAND-LINE INTERFACE
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("CYMERK RAG + CRM AGENT")
    print("=" * 60)

    question = input(
        "\nWhat would you like the Cymerk agent to do? "
    )

    answer = run_agent(question)

    print("\n" + "=" * 60)
    print("FINAL AGENT RESPONSE")
    print("=" * 60)

    print(answer)