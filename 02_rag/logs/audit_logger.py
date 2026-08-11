import json
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

LOG_FILE = (
    PROJECT_ROOT
    / "02_rag"
    / "logs"
    / "agent_audit.jsonl"
)


def log_event(
    event_type,
    status,
    details=None,
):
    """
    Write one structured audit event.

    Events are stored as JSON Lines so each
    event can be processed independently.
    """

    event = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "event_type": event_type,
        "status": status,
        "details": details or {},
    }

    LOG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with LOG_FILE.open(
        "a",
        encoding="utf-8",
    ) as file:

        file.write(
            json.dumps(event)
            + "\n"
        )


if __name__ == "__main__":

    log_event(
        event_type="test_event",
        status="success",
        details={
            "message": "Audit logger initialized."
        },
    )

    print(
        f"Audit event written to:\n{LOG_FILE}"
    )