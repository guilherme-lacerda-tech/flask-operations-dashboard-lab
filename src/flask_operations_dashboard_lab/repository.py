from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

ACTIVE_STATES = ("open", "acknowledged", "escalated")
VALID_STATES = {*ACTIVE_STATES, "resolved"}


SCHEMA = """
CREATE TABLE IF NOT EXISTS incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_key TEXT NOT NULL UNIQUE,
    asset_name TEXT NOT NULL,
    queue TEXT NOT NULL,
    category TEXT NOT NULL,
    severity INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    sla_minutes INTEGER NOT NULL,
    note TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS queue_metrics (
    queue TEXT PRIMARY KEY,
    engineers INTEGER NOT NULL,
    automation_success_rate REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS trend_points (
    slot TEXT PRIMARY KEY,
    opened INTEGER NOT NULL,
    resolved INTEGER NOT NULL,
    breached INTEGER NOT NULL
);
"""


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def connect(path: str | Path) -> sqlite3.Connection:
    database_path = Path(path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(path: str | Path) -> None:
    with connect(path) as connection:
        connection.executescript(SCHEMA)
        incident_count = connection.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        if incident_count == 0:
            seed_synthetic_data(connection)


def seed_synthetic_data(connection: sqlite3.Connection) -> None:
    now = utc_now()
    incidents = [
        ("INC-1001", "North telemetry gateway", "Field Operations", "connectivity", 91, "open", 146, 120, "Heartbeat gap above threshold"),
        ("INC-1002", "Billing sync worker", "Backoffice", "integration", 68, "acknowledged", 62, 90, "Retry volume above baseline"),
        ("INC-1003", "Depot tablet fleet", "Device Support", "device", 74, "escalated", 214, 180, "Firmware rollout needs operator review"),
        ("INC-1004", "Inventory import job", "Backoffice", "data-quality", 46, "resolved", 420, 240, "Synthetic duplicate rows removed"),
        ("INC-1005", "South route monitor", "Field Operations", "connectivity", 82, "open", 35, 90, "Packet loss spike"),
        ("INC-1006", "Notification relay", "Platform", "queue", 57, "acknowledged", 112, 120, "Queue latency rising"),
        ("INC-1007", "Support export task", "Platform", "batch", 63, "open", 189, 180, "Long-running export needs checkpoint review"),
        ("INC-1008", "Warehouse kiosk", "Device Support", "device", 39, "resolved", 288, 180, "Recovered after local cache refresh"),
        ("INC-1009", "Partner API sandbox", "Backoffice", "integration", 88, "open", 171, 120, "Synthetic upstream timeout"),
        ("INC-1010", "Dispatch planner", "Field Operations", "workflow", 52, "acknowledged", 51, 90, "Manual assignment backlog"),
        ("INC-1011", "Data validation queue", "Platform", "data-quality", 77, "escalated", 245, 180, "Schema drift detected in demo payload"),
        ("INC-1012", "Device enrollment lab", "Device Support", "device", 59, "open", 73, 120, "Enrollment retries above target"),
    ]
    for row in incidents:
        created_at = now - timedelta(minutes=row[6])
        connection.execute(
            """
            INSERT INTO incidents (
                incident_key, asset_name, queue, category, severity, status,
                created_at, updated_at, sla_minutes, note
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                created_at.isoformat(),
                now.isoformat(),
                row[7],
                row[8],
            ),
        )

    for queue, engineers, success_rate in [
        ("Backoffice", 4, 0.81),
        ("Device Support", 3, 0.74),
        ("Field Operations", 5, 0.78),
        ("Platform", 4, 0.86),
    ]:
        connection.execute(
            "INSERT INTO queue_metrics (queue, engineers, automation_success_rate) VALUES (?, ?, ?)",
            (queue, engineers, success_rate),
        )

    for index, opened in enumerate([7, 9, 8, 11, 10, 14, 12, 15]):
        connection.execute(
            "INSERT INTO trend_points (slot, opened, resolved, breached) VALUES (?, ?, ?, ?)",
            (f"T-{7 - index}", opened, max(2, opened - 4), index % 4 + 1),
        )


class OperationsRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def health(self) -> dict[str, str | int]:
        with connect(self.path) as connection:
            count = connection.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        return {"status": "ok", "incidents": count}

    def list_incidents(self, *, status: str = "active", queue: str | None = None) -> list[dict]:
        query = "SELECT * FROM incidents"
        clauses: list[str] = []
        params: list[str] = []
        if status == "active":
            clauses.append("status IN ('open', 'acknowledged', 'escalated')")
        elif status != "all":
            clauses.append("status = ?")
            params.append(status)
        if queue:
            clauses.append("queue = ?")
            params.append(queue)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY severity DESC, created_at ASC"

        now = utc_now()
        with connect(self.path) as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._incident_payload(row, now) for row in rows]

    def summary(self) -> dict:
        active_incidents = self.list_incidents(status="active")
        all_incidents = self.list_incidents(status="all")
        breached = [incident for incident in active_incidents if incident["sla_state"] == "breached"]
        avg_age = round(
            sum(incident["age_minutes"] for incident in active_incidents) / max(len(active_incidents), 1),
            1,
        )

        with connect(self.path) as connection:
            queues = connection.execute(
                """
                SELECT
                    qm.queue,
                    qm.engineers,
                    qm.automation_success_rate,
                    COUNT(i.id) AS active_count,
                    AVG(i.severity) AS avg_severity
                FROM queue_metrics qm
                LEFT JOIN incidents i
                    ON i.queue = qm.queue
                    AND i.status IN ('open', 'acknowledged', 'escalated')
                GROUP BY qm.queue, qm.engineers, qm.automation_success_rate
                ORDER BY active_count DESC, qm.queue ASC
                """
            ).fetchall()
            trend = connection.execute(
                "SELECT slot, opened, resolved, breached FROM trend_points ORDER BY slot ASC"
            ).fetchall()

        status_counts = {
            state: sum(1 for incident in all_incidents if incident["status"] == state)
            for state in sorted(VALID_STATES)
        }
        oldest_pending_minutes = max(
            (incident["age_minutes"] for incident in active_incidents),
            default=0,
        )
        last_failures = [
            {
                "incident_key": incident["incident_key"],
                "queue": incident["queue"],
                "severity": incident["severity"],
                "sla_state": incident["sla_state"],
                "age_minutes": incident["age_minutes"],
            }
            for incident in sorted(
                active_incidents,
                key=lambda item: (item["sla_state"] != "breached", -item["severity"], item["created_at"]),
            )[:3]
        ]
        temporal_history = [
            {
                **dict(row),
                "net_change": row["opened"] - row["resolved"],
            }
            for row in trend
        ]
        recovery_status = (
            "attention_required"
            if breached
            else "recovering"
            if status_counts.get("resolved", 0)
            else "stable"
        )
        return {
            "open_total": len(active_incidents),
            "queue_backlog": len(active_incidents),
            "oldest_pending_minutes": oldest_pending_minutes,
            "recovery_status": recovery_status,
            "last_failures": last_failures,
            "breached_total": len(breached),
            "average_age_minutes": avg_age,
            "automation_success_rate": round(
                sum(row["automation_success_rate"] for row in queues) / max(len(queues), 1),
                2,
            ),
            "status_counts": status_counts,
            "queues": [
                {
                    "queue": row["queue"],
                    "engineers": row["engineers"],
                    "automation_success_rate": row["automation_success_rate"],
                    "active_count": row["active_count"],
                    "avg_severity": round(row["avg_severity"] or 0, 1),
                }
                for row in queues
            ],
            "sla_trend": [dict(row) for row in trend],
            "temporal_history": temporal_history,
        }

    def transition_incident(self, incident_id: int, status: str) -> dict:
        if status not in VALID_STATES:
            raise ValueError(f"invalid status {status!r}")
        now = utc_now().isoformat()
        with connect(self.path) as connection:
            cursor = connection.execute(
                "UPDATE incidents SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, incident_id),
            )
            if cursor.rowcount == 0:
                raise KeyError(f"incident {incident_id} not found")
            row = connection.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
        return self._incident_payload(row, utc_now())

    def ingest_demo_event(self) -> dict:
        now = utc_now()
        key = f"INC-SYN-{uuid4().hex[:8].upper()}"
        with connect(self.path) as connection:
            connection.execute(
                """
                INSERT INTO incidents (
                    incident_key, asset_name, queue, category, severity, status,
                    created_at, updated_at, sla_minutes, note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key,
                    "Synthetic intake gateway",
                    "Platform",
                    "demo-event",
                    66,
                    "open",
                    now.isoformat(),
                    now.isoformat(),
                    120,
                    "Generated from public demo endpoint",
                ),
            )
            row = connection.execute("SELECT * FROM incidents WHERE incident_key = ?", (key,)).fetchone()
        return self._incident_payload(row, now)

    @staticmethod
    def _incident_payload(row: sqlite3.Row, now: datetime) -> dict:
        created_at = datetime.fromisoformat(row["created_at"])
        age_minutes = int((now - created_at).total_seconds() // 60)
        is_active = row["status"] in ACTIVE_STATES
        breached = is_active and age_minutes > row["sla_minutes"]
        return {
            "id": row["id"],
            "incident_key": row["incident_key"],
            "asset_name": row["asset_name"],
            "queue": row["queue"],
            "category": row["category"],
            "severity": row["severity"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "sla_minutes": row["sla_minutes"],
            "age_minutes": age_minutes,
            "sla_state": "breached" if breached else "inside",
            "note": row["note"],
        }

