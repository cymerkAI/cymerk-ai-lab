import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from logs.audit_logger import log_event
from approval_store import (
    initialize_database,
    save_approval_request,
    get_approval_request,
    update_approval_status,
    list_pending_approvals
)

# ============================================================
# PROJECT CONFIGURATION
# ============================================================

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

# Initialize the persistent approval database when this module
# is imported.
initialize_database()


# ============================================================
# RAG SEARCH
# ============================================================

def cosine_similarity(
    vector_a,
    vector_b,
):
    """
    Calculate cosine similarity between two vectors.
    """

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
        return 0.0

    return dot_product / (
        magnitude_a * magnitude_b
    )


def load_embeddings():
    """
    Load stored document embeddings.
    """

    if not EMBEDDINGS_PATH.exists():
        raise FileNotFoundError(
            f"Embeddings file not found: {EMBEDDINGS_PATH}"
        )

    return json.loads(
        EMBEDDINGS_PATH.read_text(
            encoding="utf-8"
        )
    )


def search_knowledge(
    query: str,
    top_k: int = 2,
    min_score: float = 0.55,
):
    """
    Search the Cymerk knowledge base using
    semantic similarity.
    """

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
# CRM MODELS
# ============================================================

class CRMLead(BaseModel):
    """
    Validated CRM lead model.
    """

    name: str = Field(min_length=1)
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    lead_score: int = Field(
        ge=0,
        le=100,
    )


class CRMApprovalRequest(BaseModel):
    """
    Represents a pending human approval request.
    """

    approval_id: str
    action: str
    lead: CRMLead
    status: str = "pending"
    created_at: str
    resolved_at: Optional[str] = None


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def utc_timestamp() -> str:
    """
    Return the current UTC timestamp.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


def _lead_to_dict(lead: CRMLead) -> dict:
    """
    Convert a CRMLead model to a serializable dictionary.
    """

    return lead.model_dump()


# ============================================================
# CRM VALIDATION
# ============================================================

def validate_lead(
    name: str,
    title: str,
    company: str,
    lead_score: int,
) -> Tuple[bool, Any]:
    """
    Validate CRM lead data.

    Returns:
        (True, CRMLead) when valid
        (False, validation_error) when invalid
    """

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
# REQUEST HUMAN APPROVAL
# ============================================================

def request_crm_approval(
    name: str,
    title: str,
    company: str,
    lead_score: int,
):
    """
    Validate a CRM lead and create a pending
    human approval request.

    IMPORTANT:
    This function does NOT create the CRM record.
    """

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
    # CREATE APPROVAL REQUEST
    # --------------------------------------------------------

    approval_id = str(uuid.uuid4())

    created_at = utc_timestamp()

    approval_request = CRMApprovalRequest(
        approval_id=approval_id,
        action="create_crm_lead",
        lead=lead,
        status="pending",
        created_at=created_at,
    )

    # --------------------------------------------------------
    # PERSIST APPROVAL REQUEST
    # --------------------------------------------------------

    save_approval_request(
        approval_id=approval_id,
        action="create_crm_lead",
        status="pending",
        lead=lead.model_dump(),
        created_at=created_at,
    )

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    log_event(
        event_type="approval_requested",
        status="pending",
        details={
            "approval_id": approval_id,
            "action": "create_crm_lead",
            "company": lead.company,
            "lead_score": lead.lead_score,
        },
    )

    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("CYMERK HUMAN APPROVAL REQUIRED")
    print("=" * 60)

    print(
        f"Approval ID: {approval_id}"
    )
    print(
        f"Name:        {lead.name}"
    )
    print(
        f"Title:       {lead.title}"
    )
    print(
        f"Company:     {lead.company}"
    )
    print(
        f"Lead score:  {lead.lead_score}"
    )

    print("=" * 60)

    return {
        "success": True,
        "status": "pending_approval",
        "approval_id": approval_id,
        "action": "create_crm_lead",
        "lead": lead.model_dump(),
        "message": (
            "Human approval is required before "
            "the CRM lead can be created."
        ),
    }


# ============================================================
# APPROVE CRM LEAD
# ============================================================

def approve_crm_lead(
    approval_id: str,
):
    """
    Approve a pending CRM lead creation request.

    This function performs the actual CRM action
    only after approval.
    """

    approval_data = get_approval_request(
        approval_id
    )

    # --------------------------------------------------------
    # APPROVAL NOT FOUND
    # --------------------------------------------------------

    if approval_data is None:
        return {
            "success": False,
            "status": "not_found",
            "error": (
                f"Approval request '{approval_id}' "
                "was not found."
            ),
        }

    # --------------------------------------------------------
    # PREVENT DUPLICATE APPROVAL
    # --------------------------------------------------------

    if approval_data["status"] != "pending":
        return {
            "success": False,
            "status": "already_resolved",
            "error": (
                "Approval request is already "
                f"{approval_data['status']}."
            ),
        }

    # --------------------------------------------------------
    # REBUILD VALIDATED LEAD
    # --------------------------------------------------------

    try:
        lead = CRMLead(
            **approval_data["lead"]
        )

    except ValidationError as error:
        log_event(
            event_type="crm_validation",
            status="failed",
            details={
                "approval_id": approval_id,
                "reason": "stored_lead_invalid",
            },
        )

        return {
            "success": False,
            "status": "validation_failed",
            "error": str(error),
        }

    # --------------------------------------------------------
    # UPDATE APPROVAL STATE
    # --------------------------------------------------------

    resolved_at = utc_timestamp()

    update_approval_status(
        approval_id=approval_id,
        status="approved",
        resolved_at=resolved_at,
    )

    # --------------------------------------------------------
    # AUDIT APPROVAL
    # --------------------------------------------------------

    log_event(
        event_type="approval_granted",
        status="approved",
        details={
            "approval_id": approval_id,
            "action": "create_crm_lead",
            "company": lead.company,
        },
    )

    # --------------------------------------------------------
    # CREATE CRM RECORD
    # --------------------------------------------------------

    crm_record = {
        "name": lead.name,
        "title": lead.title,
        "company": lead.company,
        "lead_score": lead.lead_score,
        "status": "New",
    }

    print("\nCRM TOOL EXECUTED")
    print("-----------------")
    print(
        f"Created lead: {lead.name}"
    )
    print(
        f"Company: {lead.company}"
    )
    print(
        f"Lead score: {lead.lead_score}"
    )
    print(
        f"Status: {crm_record['status']}"
    )

    # --------------------------------------------------------
    # AUDIT CRM CREATION
    # --------------------------------------------------------

    log_event(
        event_type="crm_created",
        status="success",
        details={
            "approval_id": approval_id,
            "action": "create_crm_lead",
            "company": lead.company,
            "lead_score": lead.lead_score,
        },
    )

    return {
        "success": True,
        "status": "created",
        "approval_id": approval_id,
        "record": crm_record,
    }


# ============================================================
# REJECT CRM LEAD
# ============================================================

def reject_crm_lead(
    approval_id: str,
):
    """
    Reject a pending CRM lead creation request.

    No CRM record is created.
    """

    approval_data = get_approval_request(
        approval_id
    )

    # --------------------------------------------------------
    # APPROVAL NOT FOUND
    # --------------------------------------------------------

    if approval_data is None:
        return {
            "success": False,
            "status": "not_found",
            "error": (
                f"Approval request '{approval_id}' "
                "was not found."
            ),
        }

    # --------------------------------------------------------
    # PREVENT DUPLICATE RESOLUTION
    # --------------------------------------------------------

    if approval_data["status"] != "pending":
        return {
            "success": False,
            "status": "already_resolved",
            "error": (
                "Approval request is already "
                f"{approval_data['status']}."
            ),
        }

    # --------------------------------------------------------
    # REBUILD LEAD
    # --------------------------------------------------------

    try:
        lead = CRMLead(
            **approval_data["lead"]
        )

    except ValidationError:
        lead = None

    # --------------------------------------------------------
    # UPDATE STATE
    # --------------------------------------------------------

    resolved_at = utc_timestamp()

    update_approval_status(
        approval_id=approval_id,
        status="rejected",
        resolved_at=resolved_at,
    )

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    log_event(
        event_type="approval_rejected",
        status="rejected",
        details={
            "approval_id": approval_id,
            "action": "create_crm_lead",
            "company": (
                lead.company
                if lead is not None
                else approval_data["lead"].get("company")
            ),
        },
    )

    print("\nCRM ACTION REJECTED")

    return {
        "success": False,
        "status": "rejected",
        "approval_id": approval_id,
        "message": (
            "Human approval was not granted. "
            "No CRM record was created."
        ),
    }


# ============================================================
# CREATE LEAD
# ============================================================

def create_lead(
    name: str,
    title: str,
    company: str,
    lead_score: int,
    require_approval: bool = True,
    approval_id: Optional[str] = None,
):
    """
    Main CRM tool entry point.

    Behavior:

    require_approval=True
        -> Creates a pending approval request.
        -> Does NOT create the CRM record.

    require_approval=False
        -> Creates the CRM record immediately.

    approval_id provided
        -> Approves and executes an existing request.
    """

    # --------------------------------------------------------
    # EXISTING APPROVAL
    # --------------------------------------------------------

    if approval_id is not None:
        return approve_crm_lead(
            approval_id
        )

    # --------------------------------------------------------
    # REQUIRE HUMAN APPROVAL
    # --------------------------------------------------------

    if require_approval:
        return request_crm_approval(
            name=name,
            title=title,
            company=company,
            lead_score=lead_score,
        )

    # --------------------------------------------------------
    # DIRECT EXECUTION
    # --------------------------------------------------------
    #
    # This path should normally only be used by an
    # explicitly authorized internal process.
    # --------------------------------------------------------

    valid, result = validate_lead(
        name=name,
        title=title,
        company=company,
        lead_score=lead_score,
    )

    if not valid:
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

    crm_record = {
        "name": lead.name,
        "title": lead.title,
        "company": lead.company,
        "lead_score": lead.lead_score,
        "status": "New",
    }

    print("\nCRM TOOL EXECUTED")
    print("-----------------")
    print(
        f"Created lead: {lead.name}"
    )
    print(
        f"Company: {lead.company}"
    )
    print(
        f"Lead score: {lead.lead_score}"
    )
    print(
        f"Status: {crm_record['status']}"
    )

    log_event(
        event_type="crm_created",
        status="success",
        details={
            "action": "create_crm_lead",
            "company": lead.company,
            "lead_score": lead.lead_score,
            "approval_bypassed": True,
        },
    )

    return {
        "success": True,
        "status": "created",
        "record": crm_record,
    }


# ============================================================
# GET APPROVAL STATUS
# ============================================================

def get_approval_status(
    approval_id: str,
):
    """
    Retrieve the current status of an approval request.
    """

    approval_data = get_approval_request(
        approval_id
    )

    if approval_data is None:
        return {
            "success": False,
            "status": "not_found",
            "error": (
                f"Approval request '{approval_id}' "
                "was not found."
            ),
        }

    return {
        "success": True,
        "status": approval_data["status"],
        "approval_id": approval_data["approval_id"],
        "action": approval_data["action"],
        "lead": approval_data["lead"],
        "created_at": approval_data["created_at"],
        "resolved_at": approval_data.get(
            "resolved_at"
        ),
    }


# ============================================================
# LIST PENDING APPROVALS
# ============================================================

def list_pending_approvals():
    """
    Return all currently pending approval requests.
    """

    requests = list_pending_approvals()

    return {
        "success": True,
        "count": len(requests),
        "requests": requests,
    }


# ============================================================
# MANUAL TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("CYMERK AGENT TOOLS")
    print("=" * 60)

    # --------------------------------------------------------
    # STEP 1: REQUEST APPROVAL
    # --------------------------------------------------------

    result = create_lead(
        name="John Smith",
        title="CEO",
        company="ABC Manufacturing",
        lead_score=90,
    )

    print("\nAPPROVAL REQUEST RESULT")
    print("-----------------------")
    print(
        json.dumps(
            result,
            indent=2,
        )
    )

    # --------------------------------------------------------
    # STEP 2: SHOW PENDING APPROVALS
    # --------------------------------------------------------

    pending = list_pending_approvals()

    print("\nPENDING APPROVALS")
    print("-----------------")
    print(
        json.dumps(
            pending,
            indent=2,
        )
    )