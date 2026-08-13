from __future__ import annotations

from pathlib import Path

from flask_operations_dashboard_lab.repository import OperationsRepository, initialize_database


class OperationsService:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        initialize_database(self.database_path)
        self.repository = OperationsRepository(self.database_path)

    def health(self) -> dict:
        return self.repository.health()

    def summary(self) -> dict:
        return self.repository.summary()

    def incidents(self, *, status: str = "active", queue: str | None = None) -> list[dict]:
        return self.repository.list_incidents(status=status, queue=queue)

    def transition(self, incident_id: int, status: str) -> dict:
        return self.repository.transition_incident(incident_id, status)

    def ingest_demo_event(self) -> dict:
        return self.repository.ingest_demo_event()

