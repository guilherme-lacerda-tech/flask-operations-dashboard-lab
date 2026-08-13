# ADR 0001: Flask and SQLite for a Local Dashboard Lab

## Status

Accepted

## Context

The portfolio already includes FastAPI backend projects. This project needed to demonstrate a browser-facing operations dashboard without adding infrastructure, authentication complexity or external services.

## Decision

Use Flask for the application factory and route layer, SQLite for deterministic local state and plain CSS/JavaScript for the dashboard.

## Consequences

- The app starts quickly and is easy to inspect in a browser.
- Tests can create isolated temporary databases.
- The project demonstrates UI/API integration without pretending to be a full production SaaS.
- Future deployment would require authentication, environment configuration and a production database decision.

