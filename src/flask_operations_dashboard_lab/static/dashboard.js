const state = {
  status: "active",
};

async function getJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }
  return response.json();
}

function metric(label, value) {
  return `<div class="metric"><div class="metric-label">${label}</div><div class="metric-value">${value}</div></div>`;
}

function renderMetrics(summary) {
  document.querySelector("#metrics").innerHTML = [
    metric("Active Incidents", summary.open_total),
    metric("SLA Breaches", summary.breached_total),
    metric("Average Age", `${summary.average_age_minutes}m`),
    metric("Automation", `${Math.round(summary.automation_success_rate * 100)}%`),
  ].join("");
  document.querySelector("#automationRate").textContent =
    `${Math.round(summary.automation_success_rate * 100)}% automation success`;
}

function renderQueues(queues) {
  const max = Math.max(...queues.map((queue) => queue.active_count), 1);
  document.querySelector("#queueBars").innerHTML = queues
    .map((queue) => {
      const width = Math.round((queue.active_count / max) * 100);
      return `
        <div class="queue-row">
          <div class="queue-label">
            <strong>${queue.queue}</strong>
            <span>${queue.active_count} active / ${queue.engineers} engineers</span>
          </div>
          <div class="track"><div class="bar" style="width:${width}%"></div></div>
        </div>
      `;
    })
    .join("");
}

function renderTrend(points) {
  const width = 620;
  const height = 200;
  const padding = 24;
  const maxValue = Math.max(...points.flatMap((point) => [point.opened, point.resolved, point.breached]), 1);
  const step = (width - padding * 2) / Math.max(points.length - 1, 1);
  const y = (value) => height - padding - (value / maxValue) * (height - padding * 2);
  const line = (field, color) =>
    points
      .map((point, index) => `${padding + index * step},${y(point[field])}`)
      .join(" ");
  const labels = points
    .map((point, index) => `<text x="${padding + index * step}" y="194" text-anchor="middle">${point.slot}</text>`)
    .join("");

  document.querySelector("#trendChart").innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img">
      <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="#d8dee4" />
      <polyline points="${line("opened", "#245ca6")}" fill="none" stroke="#245ca6" stroke-width="4" stroke-linecap="round" />
      <polyline points="${line("resolved", "#147d52")}" fill="none" stroke="#147d52" stroke-width="4" stroke-linecap="round" />
      <polyline points="${line("breached", "#b42318")}" fill="none" stroke="#b42318" stroke-width="4" stroke-linecap="round" />
      ${labels}
    </svg>
  `;
}

function actionButtons(incident) {
  if (incident.status === "resolved") {
    return "";
  }
  return `
    <button type="button" data-action-state="acknowledged" data-incident-id="${incident.id}">Ack</button>
    <button type="button" data-action-state="escalated" data-incident-id="${incident.id}">Escalate</button>
    <button type="button" data-action-state="resolved" data-incident-id="${incident.id}">Resolve</button>
  `;
}

function renderIncidents(incidents) {
  document.querySelector("#incidentRows").innerHTML = incidents
    .map(
      (incident) => `
        <tr>
          <td class="key">${incident.incident_key}</td>
          <td>${incident.queue}</td>
          <td>${incident.asset_name}</td>
          <td><span class="severity">${incident.severity}</span></td>
          <td>${incident.age_minutes}m</td>
          <td><span class="sla ${incident.sla_state}">${incident.sla_state}</span></td>
          <td class="status">${incident.status}</td>
          <td><div class="row-actions">${actionButtons(incident)}</div></td>
        </tr>
      `
    )
    .join("");
}

async function refresh() {
  const [summary, incidentPayload] = await Promise.all([
    getJson("/api/summary"),
    getJson(`/api/incidents?status=${state.status}`),
  ]);
  renderMetrics(summary);
  renderQueues(summary.queues);
  renderTrend(summary.sla_trend);
  renderIncidents(incidentPayload.incidents);
}

document.addEventListener("click", async (event) => {
  const filterButton = event.target.closest("[data-status-filter]");
  if (filterButton) {
    state.status = filterButton.dataset.statusFilter;
    document.querySelectorAll("[data-status-filter]").forEach((button) => {
      button.classList.toggle("is-active", button === filterButton);
    });
    await refresh();
    return;
  }

  const actionButton = event.target.closest("[data-action-state]");
  if (actionButton) {
    await getJson(`/api/incidents/${actionButton.dataset.incidentId}/transition`, {
      method: "POST",
      body: JSON.stringify({ status: actionButton.dataset.actionState }),
    });
    await refresh();
    return;
  }

  if (event.target.closest("#ingestDemoButton")) {
    await getJson("/api/demo-events", { method: "POST" });
    await refresh();
  }
});

refresh();

