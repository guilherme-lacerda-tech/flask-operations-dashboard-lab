# API Examples

Start the app:

```bash
flask --app flask_operations_dashboard_lab.app:create_app run
```

## Health

```bash
curl -i http://127.0.0.1:5000/health
```

Expected response:

```http
HTTP/1.1 200 OK
content-type: application/json

{"incidents":12,"status":"ok"}
```

## Summary

```bash
curl -i http://127.0.0.1:5000/api/summary
```

Expected shape:

```http
HTTP/1.1 200 OK
content-type: application/json

{
  "open_total": 10,
  "breached_total": 5,
  "queues": [],
  "sla_trend": []
}
```

## Resolve An Incident

```bash
curl -i -X POST http://127.0.0.1:5000/api/incidents/1/transition \
  -H "content-type: application/json" \
  -d '{"status":"resolved"}'
```

Expected shape:

```http
HTTP/1.1 200 OK
content-type: application/json

{
  "incident": {
    "id": 1,
    "status": "resolved"
  }
}
```

