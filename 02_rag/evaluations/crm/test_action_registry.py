import sys
from pathlib import Path

import pytest


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORTS
# ============================================================

from action_registry import (
    ACTION_REGISTRY,
    ActionDefinition,
    get_action,
    is_registered_action,
    requires_human_approval,
)


# ============================================================
# REGISTRY EXISTENCE
# ============================================================

def test_action_registry_exists():
    """
    The Cymerk action registry must exist and contain
    registered actions.
    """

    assert isinstance(
        ACTION_REGISTRY,
        dict,
    )

    assert len(
        ACTION_REGISTRY
    ) > 0


# ============================================================
# CRM LEAD ACTION
# ============================================================

def test_create_crm_lead_is_registered():
    """
    CRM lead creation must be explicitly registered.
    """

    assert is_registered_action(
        "create_crm_lead"
    ) is True


def test_create_crm_lead_definition():
    """
    The CRM lead action must expose the expected
    governance metadata.
    """

    action = get_action(
        "create_crm_lead"
    )

    assert action is not None

    assert isinstance(
        action,
        ActionDefinition,
    )

    assert action.name == "create_crm_lead"

    assert action.risk_level == "medium"

    assert action.requires_human_approval is True


# ============================================================
# APPROVAL REQUIREMENT
# ============================================================

def test_create_crm_lead_requires_human_approval():
    """
    CRM lead creation must require human approval.
    """

    assert requires_human_approval(
        "create_crm_lead"
    ) is True


# ============================================================
# UNKNOWN ACTIONS
# ============================================================

def test_unknown_action_is_not_registered():
    """
    Unknown actions must not appear as registered actions.
    """

    assert is_registered_action(
        "unknown_action"
    ) is False


def test_unknown_action_returns_none():
    """
    Looking up an unknown action must return None.
    """

    assert get_action(
        "unknown_action"
    ) is None


def test_unknown_action_requires_approval():
    """
    Unknown actions must fail conservatively.

    An unknown action must never be treated as a
    low-risk action that can bypass human approval.
    """

    assert requires_human_approval(
        "unknown_action"
    ) is True


# ============================================================
# IMMUTABILITY
# ============================================================

def test_action_definition_is_immutable():
    """
    Action definitions must be immutable.

    This prevents runtime code from silently changing
    governance metadata after registration.
    """

    action = get_action(
        "create_crm_lead"
    )

    assert action is not None

    with pytest.raises(
        Exception
    ):
        action.requires_human_approval = False