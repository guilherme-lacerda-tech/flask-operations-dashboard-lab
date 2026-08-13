from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request

from flask_operations_dashboard_lab.service import OperationsService


def create_app(database_path: str | Path | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    db_path = Path(database_path) if database_path else Path(app.instance_path) / "operations.sqlite3"
    service = OperationsService(db_path)

    @app.get("/")
    def dashboard():
        return render_template("dashboard.html")

    @app.get("/health")
    def health():
        return jsonify(service.health())

    @app.get("/api/summary")
    def summary():
        return jsonify(service.summary())

    @app.get("/api/incidents")
    def incidents():
        status = request.args.get("status", "active")
        queue = request.args.get("queue")
        return jsonify({"incidents": service.incidents(status=status, queue=queue)})

    @app.post("/api/incidents/<int:incident_id>/transition")
    def transition(incident_id: int):
        payload = request.get_json(silent=True) or {}
        status = payload.get("status")
        if not isinstance(status, str):
            return jsonify({"error": "status is required"}), 400
        try:
            incident = service.transition(incident_id, status)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        except KeyError as exc:
            return jsonify({"error": str(exc)}), 404
        return jsonify({"incident": incident})

    @app.post("/api/demo-events")
    def ingest_demo_event():
        return jsonify({"incident": service.ingest_demo_event()}), 201

    return app


if __name__ == "__main__":
    create_app().run(debug=True)

