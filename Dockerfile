FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN python -m pip install --no-cache-dir -e .

ENV FLASK_APP=flask_operations_dashboard_lab.app:create_app
EXPOSE 5000
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]

