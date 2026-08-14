import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

LOG_FILE = (
    PROJECT_ROOT
    / "02_rag"
    / "logs"
    / "agent_audit.jsonl"
)


def log_event(
    event_type: str,
    status: str,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
    approval_id: str | None = None,
) -> None:
    """
    Write one structured audit event.

    Events are stored as JSON Lines so each event
    can be processed independently.

    request_id:
        Optional identifier used to correlate events
        belonging to the same agent request.

    approval_id:
        Optional identifier used to correlate events
        belonging to the same human approval workflow.
    """

    event: dict[str, Any] = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "event_type": event_type,
        "status": status,
    }

    if request_id is not None:
        event["request_id"] = request_id

    if approval_id is not None:
        event["approval_id"] = approval_id

    event["details"] = details or {}

    LOG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with LOG_FILE.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                event,
                ensure_ascii=False,
            )
            + "\n"
        )


if __name__ == "__main__":
    log_event(
        event_type="test_event",
        status="success",
        details={
            "message": "Audit logger initialized."
        },
        request_id="test-request-001",
    )

    print(
        f"Audit event written to:\n{LOG_FILE}"
    )