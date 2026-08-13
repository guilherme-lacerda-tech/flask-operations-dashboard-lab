# Flask Operations Dashboard Lab

[![CI](https://github.com/guilherme-lacerda-tech/flask-operations-dashboard-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/guilherme-lacerda-tech/flask-operations-dashboard-lab/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A compact Flask dashboard for synthetic support operations. It combines a SQLite-backed incident repository, JSON endpoints, state transitions, SLA calculations and a usable browser UI with no external services.

## What It Demonstrates

- Flask application factory with testable routes.
- SQLite repository with deterministic synthetic seed data.
- SLA breach calculations and queue summaries.
- JSON APIs for dashboard state and incident transitions.
- Browser UI with KPI tiles, queue workload bars, SLA trend and incident table.
- CI with Ruff and pytest coverage gate.

## Run Locally

```bash
python -m pip install -e ".[dev]"
flask --app flask_operations_dashboard_lab.app:create_app run
```

Open `http://127.0.0.1:5000`.

CLI summary:

```bash
flask-ops-dashboard-demo
```

## API

```http
GET /health
GET /api/summary
GET /api/incidents?status=active
POST /api/incidents/1/transition
POST /api/demo-events
```

Transition payload:

```json
{
  "status": "resolved"
}
```

## Validation

```bash
python -m ruff check .
python -m pytest --cov --cov-report=term-missing -q
```

The coverage gate is set to 86%.

## Security

This project uses fictional queues, assets and incidents. It does not include real tickets, customers, devices, private URLs, credentials, logs or production screenshots.

