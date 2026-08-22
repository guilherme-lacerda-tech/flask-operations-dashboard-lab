import pytest

from flask_operations_dashboard_lab.repository import OperationsRepository, initialize_database


def test_repository_seeds_summary(tmp_path) -> None:
    database = tmp_path / "ops.sqlite3"
    initialize_database(database)
    repository = OperationsRepository(database)

    summary = repository.summary()

    assert summary["open_total"] == 10
    assert summary["breached_total"] >= 3
    assert summary["status_counts"]["resolved"] == 2
    assert summary["queue_backlog"] == summary["open_total"]
    assert summary["oldest_pending_minutes"] >= 200
    assert summary["recovery_status"] == "attention_required"
    assert len(summary["last_failures"]) == 3
    assert len(summary["queues"]) == 4
    assert len(summary["sla_trend"]) == 8
    assert len(summary["temporal_history"]) == 8
    assert "net_change" in summary["temporal_history"][0]


def test_repository_filters_and_transitions_incidents(tmp_path) -> None:
    database = tmp_path / "ops.sqlite3"
    initialize_database(database)
    repository = OperationsRepository(database)

    open_incidents = repository.list_incidents(status="open")
    transitioned = repository.transition_incident(open_incidents[0]["id"], "resolved")

    assert transitioned["status"] == "resolved"
    assert repository.list_incidents(status="resolved")


def test_repository_rejects_invalid_transition(tmp_path) -> None:
    database = tmp_path / "ops.sqlite3"
    initialize_database(database)
    repository = OperationsRepository(database)
    incident = repository.list_incidents(status="active")[0]

    with pytest.raises(ValueError):
        repository.transition_incident(incident["id"], "waiting-on-magic")


def test_repository_raises_for_missing_incident(tmp_path) -> None:
    database = tmp_path / "ops.sqlite3"
    initialize_database(database)
    repository = OperationsRepository(database)

    with pytest.raises(KeyError):
        repository.transition_incident(9999, "resolved")


def test_repository_ingests_demo_event(tmp_path) -> None:
    database = tmp_path / "ops.sqlite3"
    initialize_database(database)
    repository = OperationsRepository(database)

    incident = repository.ingest_demo_event()

    assert incident["incident_key"].startswith("INC-SYN-")
    assert incident["status"] == "open"
    assert repository.summary()["open_total"] == 11

