import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = (
    PROJECT_ROOT
    / "02_rag"
    / "data"
    / "cymerk_approvals.db"
)


def _connect():
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DB_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    with _connect() as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS approval_requests (
                approval_id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                lead_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                resolved_at TEXT
            )
            """
        )

        connection.commit()


def save_approval_request(
    approval_id: str,
    action: str,
    status: str,
    lead: Dict[str, Any],
    created_at: str,
    resolved_at: Optional[str] = None,
):
    initialize_database()

    with _connect() as connection:

        connection.execute(
            """
            INSERT INTO approval_requests (
                approval_id,
                action,
                status,
                lead_json,
                created_at,
                resolved_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                approval_id,
                action,
                status,
                json.dumps(lead),
                created_at,
                resolved_at,
            ),
        )

        connection.commit()


def get_approval_request(
    approval_id: str,
) -> Optional[Dict[str, Any]]:
    initialize_database()

    with _connect() as connection:

        row = connection.execute(
            """
            SELECT
                approval_id,
                action,
                status,
                lead_json,
                created_at,
                resolved_at
            FROM approval_requests
            WHERE approval_id = ?
            """,
            (approval_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "approval_id": row["approval_id"],
        "action": row["action"],
        "status": row["status"],
        "lead": json.loads(row["lead_json"]),
        "created_at": row["created_at"],
        "resolved_at": row["resolved_at"],
    }


def update_approval_status(
    approval_id: str,
    status: str,
    resolved_at: Optional[str],
):
    initialize_database()

    with _connect() as connection:

        cursor = connection.execute(
            """
            UPDATE approval_requests
            SET
                status = ?,
                resolved_at = ?
            WHERE approval_id = ?
            """,
            (
                status,
                resolved_at,
                approval_id,
            ),
        )

        connection.commit()

    return cursor.rowcount > 0


def list_pending_approvals() -> List[Dict[str, Any]]:
    initialize_database()

    with _connect() as connection:

        rows = connection.execute(
            """
            SELECT
                approval_id,
                action,
                status,
                lead_json,
                created_at,
                resolved_at
            FROM approval_requests
            WHERE status = 'pending'
            ORDER BY created_at ASC
            """
        ).fetchall()

    return [
        {
            "approval_id": row["approval_id"],
            "action": row["action"],
            "status": row["status"],
            "lead": json.loads(row["lead_json"]),
            "created_at": row["created_at"],
            "resolved_at": row["resolved_at"],
        }
        for row in rows
    ]