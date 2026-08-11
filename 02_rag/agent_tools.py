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
# CRM MODEL
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


# ============================================================
# CRM APPROVAL MODEL
# ============================================================

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
# IN-MEMORY APPROVAL STORE
# ============================================================
#
# This is intentionally simple for the current prototype.
#
# Later this should be replaced with:
#
#     PostgreSQL / Redis / CRM database
#
# so approval requests survive application restarts.
# ============================================================

APPROVAL_REQUESTS: Dict[str, CRMApprovalRequest] = {}


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

    It only creates an approval request.
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
    # CREATE APPROVAL REQUEST
    # --------------------------------------------------------

    approval_id = str(
        uuid.uuid4()
    )

    approval_request = CRMApprovalRequest(
        approval_id=approval_id,
        action="create_crm_lead",
        lead=lead,
        status="pending",
        created_at=utc_timestamp(),
    )

    APPROVAL_REQUESTS[
        approval_id
    ] = approval_request

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

    approval_request = APPROVAL_REQUESTS.get(
        approval_id
    )

    # --------------------------------------------------------
    # APPROVAL NOT FOUND
    # --------------------------------------------------------

    if approval_request is None:

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

    if approval_request.status != "pending":

        return {
            "success": False,
            "status": "already_resolved",
            "error": (
                f"Approval request is already "
                f"{approval_request.status}."
            ),
        }

    # --------------------------------------------------------
    # UPDATE APPROVAL STATE
    # --------------------------------------------------------

    approval_request.status = "approved"
    approval_request.resolved_at = utc_timestamp()

    APPROVAL_REQUESTS[
        approval_id
    ] = approval_request

    # --------------------------------------------------------
    # AUDIT APPROVAL
    # --------------------------------------------------------

    log_event(
        event_type="approval_granted",
        status="approved",
        details={
            "approval_id": approval_id,
            "action": "create_crm_lead",
            "company": approval_request.lead.company,
        },
    )

    # --------------------------------------------------------
    # CREATE CRM RECORD
    # --------------------------------------------------------

    lead = approval_request.lead

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

    approval_request = APPROVAL_REQUESTS.get(
        approval_id
    )

    # --------------------------------------------------------
    # APPROVAL NOT FOUND
    # --------------------------------------------------------

    if approval_request is None:

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

    if approval_request.status != "pending":

        return {
            "success": False,
            "status": "already_resolved",
            "error": (
                f"Approval request is already "
                f"{approval_request.status}."
            ),
        }

    # --------------------------------------------------------
    # UPDATE STATE
    # --------------------------------------------------------

    approval_request.status = "rejected"
    approval_request.resolved_at = utc_timestamp()

    APPROVAL_REQUESTS[
        approval_id
    ] = approval_request

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    log_event(
        event_type="approval_rejected",
        status="rejected",
        details={
            "approval_id": approval_id,
            "action": "create_crm_lead",
            "company": approval_request.lead.company,
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

    approval_request = APPROVAL_REQUESTS.get(
        approval_id
    )

    if approval_request is None:

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
        "status": approval_request.status,
        "approval_id": approval_request.approval_id,
        "action": approval_request.action,
        "lead": approval_request.lead.model_dump(),
        "created_at": approval_request.created_at,
        "resolved_at": approval_request.resolved_at,
    }


# ============================================================
# LIST PENDING APPROVALS
# ============================================================

def list_pending_approvals():
    """
    Return all currently pending approval requests.
    """

    pending = []

    for request in APPROVAL_REQUESTS.values():

        if request.status == "pending":

            pending.append(
                {
                    "approval_id": request.approval_id,
                    "action": request.action,
                    "lead": request.lead.model_dump(),
                    "created_at": request.created_at,
                }
            )

    return {
        "success": True,
        "count": len(pending),
        "requests": pending,
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

    # --------------------------------------------------------
    # STEP 3: APPROVE FOR TESTING
    # --------------------------------------------------------
    #
    # In production, this approval would come from
    # an external approval interface, not automatically.
    # --------------------------------------------------------

    if result.get("approval_id"):

        approval_result = approve_crm_lead(
            result["approval_id"]
        )

        print("\nAPPROVAL RESULT")
        print("---------------")
        print(
            json.dumps(
                approval_result,
                indent=2,
            )
        )