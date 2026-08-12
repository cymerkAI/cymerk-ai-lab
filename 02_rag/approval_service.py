from typing import Any, Dict

from logs.audit_logger import log_event

from approval_store import (
    initialize_database,
    save_approval_request,
    get_approval_request,
    update_approval_status,
    list_pending_approvals as store_list_pending_approvals,
)

def request_approval(
    approval_id: str,
    action: str,
    lead: Dict[str, Any],
    created_at: str,
) -> Dict[str, Any]:
    """
    Create a new pending human approval request.

    This function records the request only.
    It does not execute the protected action.
    """

    save_approval_request(
        approval_id=approval_id,
        action=action,
        status="pending",
        lead=lead,
        created_at=created_at,
        resolved_at=None,
    )

    log_event(
        event_type="approval_requested",
        status="pending",
        details={
            "approval_id": approval_id,
            "action": action,
            "company": lead.get("company"),
        },
    )

    return {
        "success": True,
        "status": "pending",
        "approval_id": approval_id,
        "action": action,
        "lead": lead,
        "message": (
            "Human approval is required before "
            "this action can be executed."
        ),
    }


def get_approval(
    approval_id: str,
) -> Dict[str, Any]:
    """
    Retrieve an approval request by ID.
    """

    request = get_approval_request(
        approval_id
    )

    if request is None:
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
        **request,
    }


def list_pending_requests() -> Dict[str, Any]:
    """
    Return all currently pending approval requests.
    """

    requests = store_list_pending_approvals()

    return {
        "success": True,
        "count": len(requests),
        "requests": requests,
    }


def approve_request(
    approval_id: str,
) -> Dict[str, Any]:
    """
    Approve a pending request.

    This changes approval state only.
    The AI agent must not call this function
    as part of its own decision-making process.
    """

    request = get_approval_request(
        approval_id
    )

    if request is None:
        return {
            "success": False,
            "status": "not_found",
            "error": (
                f"Approval request '{approval_id}' "
                "was not found."
            ),
        }

    if request["status"] != "pending":
        return {
            "success": False,
            "status": "already_resolved",
            "error": (
                f"Approval request is already "
                f"{request['status']}."
            ),
        }

    from datetime import datetime, timezone

    resolved_at = datetime.now(
        timezone.utc
    ).isoformat()

    updated = update_approval_status(
        approval_id=approval_id,
        status="approved",
        resolved_at=resolved_at,
    )

    if not updated:
        return {
            "success": False,
            "status": "update_failed",
            "error": (
                "Approval status could not be updated."
            ),
        }

    log_event(
        event_type="approval_granted",
        status="approved",
        details={
            "approval_id": approval_id,
            "action": request["action"],
            "company": request["lead"].get("company"),
        },
    )

    return {
        "success": True,
        "status": "approved",
        "approval_id": approval_id,
        "action": request["action"],
        "lead": request["lead"],
        "resolved_at": resolved_at,
        "message": "Human approval granted.",
    }


def reject_request(
    approval_id: str,
) -> Dict[str, Any]:
    """
    Reject a pending request.

    No protected action is executed.
    """

    request = get_approval_request(
        approval_id
    )

    if request is None:
        return {
            "success": False,
            "status": "not_found",
            "error": (
                f"Approval request '{approval_id}' "
                "was not found."
            ),
        }

    if request["status"] != "pending":
        return {
            "success": False,
            "status": "already_resolved",
            "error": (
                f"Approval request is already "
                f"{request['status']}."
            ),
        }

    from datetime import datetime, timezone

    resolved_at = datetime.now(
        timezone.utc
    ).isoformat()

    updated = update_approval_status(
        approval_id=approval_id,
        status="rejected",
        resolved_at=resolved_at,
    )

    if not updated:
        return {
            "success": False,
            "status": "update_failed",
            "error": (
                "Approval status could not be updated."
            ),
        }

    log_event(
        event_type="approval_rejected",
        status="rejected",
        details={
            "approval_id": approval_id,
            "action": request["action"],
            "company": request["lead"].get("company"),
        },
    )

    return {
        "success": True,
        "status": "rejected",
        "approval_id": approval_id,
        "action": request["action"],
        "lead": request["lead"],
        "resolved_at": resolved_at,
        "message": (
            "Human approval rejected. "
            "No protected action was executed."
        ),
    }