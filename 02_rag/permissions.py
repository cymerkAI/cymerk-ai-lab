from logs.audit_logger import log_event


TOOL_PERMISSIONS = {
    "search_knowledge": {
        "allowed": True,
        "requires_approval": False,
    },
    "create_lead": {
        "allowed": True,
        "requires_approval": True,
    },
}


def check_tool_permission(tool_name):
    permission = TOOL_PERMISSIONS.get(tool_name)

    if permission is None:

        log_event(
            event_type="tool_permission",
            status="blocked",
            details={
                "tool": tool_name,
                "reason": "tool_not_registered",
            },
        )

        return {
            "allowed": False,
            "requires_approval": False,
            "reason": "Tool is not authorized.",
        }

    if not permission["allowed"]:

        log_event(
            event_type="tool_permission",
            status="blocked",
            details={
                "tool": tool_name,
                "reason": "tool_disabled",
            },
        )

        return {
            "allowed": False,
            "requires_approval": permission[
                "requires_approval"
            ],
            "reason": "Tool is disabled.",
        }

    log_event(
        event_type="tool_permission",
        status="allowed",
        details={
            "tool": tool_name,
            "requires_approval": permission[
                "requires_approval"
            ],
        },
    )

    return {
        "allowed": True,
        "requires_approval": permission[
            "requires_approval"
        ],
        "reason": "Tool is authorized.",
    }