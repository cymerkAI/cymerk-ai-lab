import json
import math
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from logs.audit_logger import log_event


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENV_FILE = (
    PROJECT_ROOT
    / "01_llm_foundations"
    / "01_first_llm_app"
    / ".env"
)

load_dotenv(ENV_FILE)

client = OpenAI()

EMBEDDINGS_PATH = (
    PROJECT_ROOT
    / "02_rag"
    / "retrieval"
    / "embeddings.json"
)


# ============================================================
# RAG SEARCH
# ============================================================

def cosine_similarity(vector_a, vector_b):

    dot_product = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    magnitude_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0

    return dot_product / (
        magnitude_a * magnitude_b
    )


def load_embeddings():

    return json.loads(
        EMBEDDINGS_PATH.read_text(
            encoding="utf-8"
        )
    )


def search_knowledge(
    query,
    top_k=2,
    min_score=0.55,
):

    records = load_embeddings()

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
    )

    query_embedding = response.data[0].embedding

    results = []

    for record in records:

        score = cosine_similarity(
            query_embedding,
            record["embedding"],
        )

        results.append(
            {
                "chunk_id": record["chunk_id"],
                "text": record["text"],
                "score": score,
            }
        )

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    filtered_results = [
        result
        for result in results
        if result["score"] >= min_score
    ]

    final_results = filtered_results[:top_k]

    log_event(
        event_type="knowledge_search",
        status="success",
        details={
            "query": query,
            "results_returned": len(final_results),
        },
    )

    return {
        "success": True,
        "results": final_results,
    }


# ============================================================
# CRM MODEL
# ============================================================

class CRMLead(BaseModel):

    name: str = Field(min_length=1)
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    lead_score: int = Field(
        ge=0,
        le=100,
    )


# ============================================================
# CRM VALIDATION
# ============================================================

def validate_lead(
    name: str,
    title: str,
    company: str,
    lead_score: int,
):

    try:

        lead = CRMLead(
            name=name,
            title=title,
            company=company,
            lead_score=lead_score,
        )

        return True, lead

    except ValidationError as error:

        return False, str(error)


# ============================================================
# CRM LEAD CREATION
# ============================================================

def create_lead(
    name: str,
    title: str,
    company: str,
    lead_score: int,
    require_approval=True,
):

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    valid, result = validate_lead(
        name=name,
        title=title,
        company=company,
        lead_score=lead_score,
    )

    if not valid:

        print("\nCRM VALIDATION FAILED")
        print(result)

        log_event(
            event_type="crm_validation",
            status="failed",
            details={
                "reason": "invalid_lead_data",
                "company": company,
            },
        )

        return {
            "success": False,
            "status": "validation_failed",
            "error": result,
        }

    lead = result

    # --------------------------------------------------------
    # HUMAN APPROVAL
    # --------------------------------------------------------

    if require_approval:

        print("\n")
        print("=" * 50)
        print("CYMERK HUMAN APPROVAL REQUIRED")
        print("=" * 50)

        print(f"Name:       {lead.name}")
        print(f"Title:      {lead.title}")
        print(f"Company:    {lead.company}")
        print(f"Lead score: {lead.lead_score}")

        print("=" * 50)

        log_event(
            event_type="approval_requested",
            status="pending",
            details={
                "action": "create_crm_lead",
                "company": lead.company,
            },
        )

        approval = input(
            "Approve creation of this CRM lead? (y/n): "
        )

        # ----------------------------------------------------
        # REJECTED
        # ----------------------------------------------------

        if approval.lower() != "y":

            print("\nCRM ACTION REJECTED")

            log_event(
                event_type="approval_rejected",
                status="rejected",
                details={
                    "action": "create_crm_lead",
                    "company": lead.company,
                },
            )

            return {
                "success": False,
                "status": "rejected",
                "message": (
                    "Human approval was not granted."
                ),
            }

        # ----------------------------------------------------
        # APPROVED
        # ----------------------------------------------------

        log_event(
            event_type="approval_granted",
            status="approved",
            details={
                "action": "create_crm_lead",
                "company": lead.company,
            },
        )

    # --------------------------------------------------------
    # CRM RECORD
    # --------------------------------------------------------

    crm_record = {
        "name": lead.name,
        "title": lead.title,
        "company": lead.company,
        "lead_score": lead.lead_score,
        "status": "New",
    }

    # --------------------------------------------------------
    # EXECUTE CRM ACTION
    # --------------------------------------------------------

    print("\nCRM TOOL EXECUTED")
    print("-----------------")
    print(f"Created lead: {lead.name}")
    print(f"Company: {lead.company}")
    print(f"Lead score: {lead.lead_score}")
    print(f"Status: {crm_record['status']}")

    log_event(
        event_type="crm_created",
        status="success",
        details={
            "action": "create_crm_lead",
            "company": lead.company,
            "lead_score": lead.lead_score,
        },
    )

    return {
        "success": True,
        "status": "created",
        "record": crm_record,
    }


# ============================================================
# MANUAL TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("CYMERK AGENT TOOLS")
    print("=" * 60)

    result = create_lead(
        name="John Smith",
        title="CEO",
        company="ABC Manufacturing",
        lead_score=90,
    )

    print("\nRESULT")
    print("------")
    print(result)