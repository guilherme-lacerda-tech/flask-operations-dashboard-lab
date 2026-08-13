from flask_operations_dashboard_lab.app import create_app


def test_dashboard_route_renders_shell(tmp_path) -> None:
    app = create_app(tmp_path / "ops.sqlite3")
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Operations Dashboard" in response.data
    assert b"Incident Queue" in response.data


def test_health_and_summary_api(tmp_path) -> None:
    app = create_app(tmp_path / "ops.sqlite3")
    client = app.test_client()

    health = client.get("/health").get_json()
    summary = client.get("/api/summary").get_json()

    assert health == {"incidents": 12, "status": "ok"}
    assert summary["open_total"] == 10


def test_incident_api_filter_and_transition(tmp_path) -> None:
    app = create_app(tmp_path / "ops.sqlite3")
    client = app.test_client()

    incidents = client.get("/api/incidents?status=open").get_json()["incidents"]
    response = client.post(
        f"/api/incidents/{incidents[0]['id']}/transition",
        json={"status": "resolved"},
    )

    assert response.status_code == 200
    assert response.get_json()["incident"]["status"] == "resolved"


def test_transition_api_validates_payload_and_missing_incident(tmp_path) -> None:
    app = create_app(tmp_path / "ops.sqlite3")
    client = app.test_client()

    assert client.post("/api/incidents/1/transition", json={}).status_code == 400
    assert client.post("/api/incidents/1/transition", json={"status": "bad"}).status_code == 400
    assert client.post("/api/incidents/9999/transition", json={"status": "resolved"}).status_code == 404


def test_demo_event_endpoint(tmp_path) -> None:
    app = create_app(tmp_path / "ops.sqlite3")
    client = app.test_client()

    response = client.post("/api/demo-events")

    assert response.status_code == 201
    assert response.get_json()["incident"]["incident_key"].startswith("INC-SYN-")

