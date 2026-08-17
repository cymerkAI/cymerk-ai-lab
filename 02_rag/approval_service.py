from datetime import datetime, timezone
from typing import Any, Dict

from logs.audit_logger import log_event

from approval_store import (
    initialize_database,
    save_approval_request,
    get_approval_request,
    update_approval_status,
    list_pending_approvals as store_list_pending_approvals,
)


# ============================================================
# CONSTANTS
# ============================================================

ALLOWED_ACTIONS = {
    "create_crm_lead",
}

PENDING_STATUS = "pending"
APPROVED_STATUS = "approved"
REJECTED_STATUS = "rejected"


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

initialize_database()


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _utc_now() -> str:
    """
    Return the current UTC timestamp as an ISO-8601 string.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


def _not_found_response(
    approval_id: str,
) -> Dict[str, Any]:
    """
    Standard response for an unknown approval ID.
    """

    return {
        "success": False,
        "status": "not_found",
        "approval_id": approval_id,
        "error": (
            f"Approval request '{approval_id}' "
            "was not found."
        ),
    }


def _already_resolved_response(
    approval_id: str,
    status: str,
) -> Dict[str, Any]:
    """
    Standard response for an already-resolved approval.
    """

    return {
        "success": False,
        "status": "already_resolved",
        "approval_id": approval_id,
        "error": (
            "Approval request is already "
            f"{status}."
        ),
    }


def _invalid_action_response(
    approval_id: str,
    action: str,
) -> Dict[str, Any]:
    """
    Standard response for an unsupported protected action.
    """

    return {
        "success": False,
        "status": "invalid_action",
        "approval_id": approval_id,
        "error": (
            f"Unsupported approval action: '{action}'."
        ),
    }


# ============================================================
# REQUEST APPROVAL
# ============================================================

def request_approval(
    approval_id: str,
    action: str,
    lead: Dict[str, Any],
    created_at: str,
) -> Dict[str, Any]:
    """
    Create a new pending human approval request.

    This function records the approval request only.

    It does NOT execute the protected action.

    Approval IDs are immutable identifiers. An existing
    approval ID cannot be overwritten.
    """

    # --------------------------------------------------------
    # VALIDATE ACTION
    # --------------------------------------------------------

    if action not in ALLOWED_ACTIONS:

        log_event(
            event_type="approval_requested",
            status="failed",
            approval_id=approval_id,
            details={
                "action": action,
                "company": lead.get("company"),
                "reason": "unsupported_action",
            },
        )

        return _invalid_action_response(
            approval_id=approval_id,
            action=action,
        )

    # --------------------------------------------------------
    # CHECK FOR EXISTING APPROVAL
    # --------------------------------------------------------

    existing = get_approval_request(
        approval_id
    )

    if existing is not None:

        log_event(
            event_type="approval_requested",
            status="failed",
            approval_id=approval_id,
            details={
                "action": action,
                "company": lead.get("company"),
                "reason": "approval_already_exists",
            },
        )

        return {
            "success": False,
            "status": "already_exists",
            "approval_id": approval_id,
            "error": (
                f"Approval request '{approval_id}' "
                "already exists."
            ),
        }

    # --------------------------------------------------------
    # SAVE PENDING APPROVAL
    # --------------------------------------------------------

    try:

        save_approval_request(
            approval_id=approval_id,
            action=action,
            status=PENDING_STATUS,
            lead=lead,
            created_at=created_at,
            resolved_at=None,
        )

    except Exception as error:

        log_event(
            event_type="approval_requested",
            status="failed",
            approval_id=approval_id,
            details={
                "action": action,
                "company": lead.get("company"),
                "reason": "storage_failure",
                "error": str(error),
            },
        )

        return {
            "success": False,
            "status": "storage_failed",
            "approval_id": approval_id,
            "error": (
                "Approval request could not be "
                "stored."
            ),
        }

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    log_event(
        event_type="approval_requested",
        status=PENDING_STATUS,
        approval_id=approval_id,
        details={
            "action": action,
            "company": lead.get("company"),
        },
    )

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
        "success": True,
        "status": PENDING_STATUS,
        "approval_id": approval_id,
        "action": action,
        "lead": lead,
        "created_at": created_at,
        "resolved_at": None,
        "message": (
            "Human approval is required before "
            "this action can be executed."
        ),
    }


# ============================================================
# GET APPROVAL
# ============================================================

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

        log_event(
            event_type="approval_lookup",
            status="failed",
            approval_id=approval_id,
            details={
                "reason": "not_found",
            },
        )

        return _not_found_response(
            approval_id
        )

    # --------------------------------------------------------
    # DEFENSIVE ACTION VALIDATION
    # --------------------------------------------------------

    action = request.get("action")

    if action not in ALLOWED_ACTIONS:

        log_event(
            event_type="approval_lookup",
            status="failed",
            approval_id=approval_id,
            details={
                "reason": "unsupported_action",
                "action": action,
            },
        )

        return _invalid_action_response(
            approval_id=approval_id,
            action=str(action),
        )

    return {
        "success": True,
        **request,
    }


# ============================================================
# LIST PENDING APPROVALS
# ============================================================

def list_pending_requests() -> Dict[str, Any]:
    """
    Return all currently pending approval requests.
    """

    requests = store_list_pending_approvals()

    # --------------------------------------------------------
    # DEFENSIVE FILTERING
    # --------------------------------------------------------

    valid_requests = []

    for request in requests:

        action = request.get("action")
        approval_id = request.get("approval_id")

        if action not in ALLOWED_ACTIONS:

            log_event(
                event_type="approval_list",
                status="failed",
                approval_id=approval_id,
                details={
                    "reason": "unsupported_action",
                    "action": action,
                },
            )

            continue

        valid_requests.append(
            request
        )

    return {
        "success": True,
        "count": len(valid_requests),
        "requests": valid_requests,
    }


# ============================================================
# APPROVE REQUEST
# ============================================================

def approve_request(
    approval_id: str,
) -> Dict[str, Any]:
    """
    Approve a pending request.

    This function changes approval state only.

    It does NOT execute the protected CRM action.

    CRM execution must happen separately through
    execute_approved_crm_lead().
    """

    # --------------------------------------------------------
    # RETRIEVE REQUEST
    # --------------------------------------------------------

    request = get_approval_request(
        approval_id
    )

    if request is None:

        log_event(
            event_type="approval_granted",
            status="failed",
            approval_id=approval_id,
            details={
                "reason": "not_found",
            },
        )

        return _not_found_response(
            approval_id
        )

    # --------------------------------------------------------
    # VALIDATE ACTION
    # --------------------------------------------------------

    action = request.get("action")

    if action not in ALLOWED_ACTIONS:

        log_event(
            event_type="approval_granted",
            status="failed",
            approval_id=approval_id,
            details={
                "action": action,
                "reason": "unsupported_action",
            },
        )

        return _invalid_action_response(
            approval_id=approval_id,
            action=str(action),
        )

    # --------------------------------------------------------
    # CHECK CURRENT STATE
    # --------------------------------------------------------

    current_status = request.get(
        "status"
    )

    if current_status != PENDING_STATUS:

        log_event(
            event_type="approval_granted",
            status="failed",
            approval_id=approval_id,
            details={
                "action": action,
                "company": request["lead"].get(
                    "company"
                ),
                "reason": "already_resolved",
                "current_status": current_status,
            },
        )

        return _already_resolved_response(
            approval_id=approval_id,
            status=str(current_status),
        )

    # --------------------------------------------------------
    # RESOLVE
    # --------------------------------------------------------

    resolved_at = _utc_now()

    updated = update_approval_status(
        approval_id=approval_id,
        status=APPROVED_STATUS,
        resolved_at=resolved_at,
    )

    # --------------------------------------------------------
    # HANDLE RACE / UPDATE FAILURE
    # --------------------------------------------------------

    if not updated:

        current = get_approval_request(
            approval_id
        )

        if current is not None:

            log_event(
                event_type="approval_granted",
                status="failed",
                approval_id=approval_id,
                details={
                    "action": action,
                    "reason": "already_resolved",
                    "current_status": current.get(
                        "status"
                    ),
                },
            )

            return _already_resolved_response(
                approval_id=approval_id,
                status=str(
                    current.get("status")
                ),
            )

        log_event(
            event_type="approval_granted",
            status="failed",
            approval_id=approval_id,
            details={
                "action": action,
                "reason": "update_failed",
            },
        )

        return {
            "success": False,
            "status": "update_failed",
            "approval_id": approval_id,
            "error": (
                "Approval status could not "
                "be updated."
            ),
        }

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    log_event(
        event_type="approval_granted",
        status=APPROVED_STATUS,
        approval_id=approval_id,
        details={
            "action": action,
            "company": request["lead"].get(
                "company"
            ),
        },
    )

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
        "success": True,
        "status": APPROVED_STATUS,
        "approval_id": approval_id,
        "action": action,
        "lead": request["lead"],
        "created_at": request["created_at"],
        "resolved_at": resolved_at,
        "message": (
            "Human approval granted."
        ),
    }


# ============================================================
# REJECT REQUEST
# ============================================================

def reject_request(
    approval_id: str,
) -> Dict[str, Any]:
    """
    Reject a pending request.

    This function changes approval state only.

    No protected action is executed.
    """

    # --------------------------------------------------------
    # RETRIEVE REQUEST
    # --------------------------------------------------------

    request = get_approval_request(
        approval_id
    )

    if request is None:

        log_event(
            event_type="approval_rejected",
            status="failed",
            approval_id=approval_id,
            details={
                "reason": "not_found",
            },
        )

        return _not_found_response(
            approval_id
        )

    # --------------------------------------------------------
    # VALIDATE ACTION
    # --------------------------------------------------------

    action = request.get("action")

    if action not in ALLOWED_ACTIONS:

        log_event(
            event_type="approval_rejected",
            status="failed",
            approval_id=approval_id,
            details={
                "action": action,
                "reason": "unsupported_action",
            },
        )

        return _invalid_action_response(
            approval_id=approval_id,
            action=str(action),
        )

    # --------------------------------------------------------
    # CHECK CURRENT STATE
    # --------------------------------------------------------

    current_status = request.get(
        "status"
    )

    if current_status != PENDING_STATUS:

        log_event(
            event_type="approval_rejected",
            status="failed",
            approval_id=approval_id,
            details={
                "action": action,
                "company": request["lead"].get(
                    "company"
                ),
                "reason": "already_resolved",
                "current_status": current_status,
            },
        )

        return _already_resolved_response(
            approval_id=approval_id,
            status=str(current_status),
        )

    # --------------------------------------------------------
    # RESOLVE
    # --------------------------------------------------------

    resolved_at = _utc_now()

    updated = update_approval_status(
        approval_id=approval_id,
        status=REJECTED_STATUS,
        resolved_at=resolved_at,
    )

    # --------------------------------------------------------
    # HANDLE RACE / UPDATE FAILURE
    # --------------------------------------------------------

    if not updated:

        current = get_approval_request(
            approval_id
        )

        if current is not None:

            log_event(
                event_type="approval_rejected",
                status="failed",
                approval_id=approval_id,
                details={
                    "action": action,
                    "reason": "already_resolved",
                    "current_status": current.get(
                        "status"
                    ),
                },
            )

            return _already_resolved_response(
                approval_id=approval_id,
                status=str(
                    current.get("status")
                ),
            )

        log_event(
            event_type="approval_rejected",
            status="failed",
            approval_id=approval_id,
            details={
                "action": action,
                "reason": "update_failed",
            },
        )

        return {
            "success": False,
            "status": "update_failed",
            "approval_id": approval_id,
            "error": (
                "Approval status could not "
                "be updated."
            ),
        }

    # --------------------------------------------------------
    # AUDIT
    # --------------------------------------------------------

    log_event(
        event_type="approval_rejected",
        status=REJECTED_STATUS,
        approval_id=approval_id,
        details={
            "action": action,
            "company": request["lead"].get(
                "company"
            ),
        },
    )

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
        "success": True,
        "status": REJECTED_STATUS,
        "approval_id": approval_id,
        "action": action,
        "lead": request["lead"],
        "created_at": request["created_at"],
        "resolved_at": resolved_at,
        "message": (
            "Human approval rejected. "
            "No protected action was executed."
        ),
    }