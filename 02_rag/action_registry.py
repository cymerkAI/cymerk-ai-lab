from dataclasses import dataclass
from typing import Dict, Optional


# ============================================================
# ACTION DEFINITION
# ============================================================

@dataclass(frozen=True)
class ActionDefinition:
    """
    Defines a consequential action available to the
    Cymerk AI Lab.

    This registry contains policy metadata only.

    It does NOT:
        - execute actions
        - create CRM records
        - grant approval
        - reject approval
        - bypass human approval
    """

    name: str
    description: str
    risk_level: str
    requires_human_approval: bool


# ============================================================
# ACTION REGISTRY
# ============================================================

ACTION_REGISTRY: Dict[str, ActionDefinition] = {
    "create_crm_lead": ActionDefinition(
        name="create_crm_lead",
        description=(
            "Create a new CRM lead record."
        ),
        risk_level="medium",
        requires_human_approval=True,
    ),
}


# ============================================================
# REGISTRY LOOKUP
# ============================================================

def get_action(
    action_name: str,
) -> Optional[ActionDefinition]:
    """
    Return the registered action definition.

    Returns:
        ActionDefinition when the action is registered.
        None when the action is not registered.
    """

    return ACTION_REGISTRY.get(
        action_name
    )


# ============================================================
# ACTION REGISTRATION CHECK
# ============================================================

def is_registered_action(
    action_name: str,
) -> bool:
    """
    Return True when the action exists in the registry.
    """

    return action_name in ACTION_REGISTRY


# ============================================================
# HUMAN APPROVAL REQUIREMENT
# ============================================================

def requires_human_approval(
    action_name: str,
) -> bool:
    """
    Return whether a registered action requires
    human approval.

    Security behavior:

    Unknown actions are treated conservatively and
    require human approval.
    """

    action = get_action(
        action_name
    )

    if action is None:
        return True

    return action.requires_human_approval