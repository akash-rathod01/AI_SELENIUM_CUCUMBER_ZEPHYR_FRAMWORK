"""Build an interactive HTML dashboard summarising recent automation runs.

The script reads the shared run history (reports/run_history.json) that is
populated by test_runner.py and emits a single-page dashboard with charts,
latest run details, and a lightweight schedule preview. Manual coverage numbers
can optionally be provided via reports/manual_test_metrics.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUN_HISTORY_PATH = REPORTS_DIR / "run_history.json"
MANUAL_METRICS_PATH = REPORTS_DIR / "manual_test_metrics.json"
PLATFORM_METRICS_PATH = REPORTS_DIR / "platform_metrics.json"
OUTPUT_PATH = REPORTS_DIR / "automation_dashboard.html"


@dataclass
class RunSummary:
    run_id: str
    timestamp: str
    project: str
    passed: int
    failed: int
    skipped: int
    duration: float

    @property
    def total(self) -> int:
        return self.passed + self.failed + self.skipped

    def as_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "project": self.project,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "total": self.total,
            "duration": self.duration,
        }


def load_run_history(max_items: int = 8) -> List[RunSummary]:
    if not RUN_HISTORY_PATH.exists():
        return []
    data = json.loads(RUN_HISTORY_PATH.read_text(encoding="utf-8"))
    summaries: List[RunSummary] = []
    for item in data:
        summaries.append(
            RunSummary(
                run_id=str(item.get("run_id", "unknown")),
                timestamp=item.get("timestamp", ""),
                project=item.get("project", "core"),
                passed=int(item.get("passed", 0)),
                failed=int(item.get("failed", 0)),
                skipped=int(item.get("skipped", 0)),
                duration=float(item.get("duration", 0.0)),
            )
        )
    summaries.sort(key=lambda run: run.timestamp, reverse=True)
    return summaries[:max_items]


def load_manual_metrics() -> Dict[str, int]:
    """Return manual coverage metrics or sample defaults."""

    if MANUAL_METRICS_PATH.exists():
        return json.loads(MANUAL_METRICS_PATH.read_text(encoding="utf-8"))
    return {
        "pending": 10,
        "finished": 2,
        "total": 12,
    }


def load_platform_metrics() -> Dict[str, int]:
    """Return platform aggregation for bar charts."""

    if PLATFORM_METRICS_PATH.exists():
        return json.loads(PLATFORM_METRICS_PATH.read_text(encoding="utf-8"))
    return {
        "Windows 11 (Chrome 118)": 3,
        "Android 14 (Pixel 8)": 2,
        "macOS 14 (Safari)": 1,
    }


def _parse_timestamp(timestamp: str) -> datetime:
    if not timestamp:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _timeframe_counts(runs: List[RunSummary]) -> Dict[str, int]:
    now = datetime.now(timezone.utc)
    counters = {"day": 0, "week": 0, "month": 0, "quarter": 0}
    for run in runs:
        ts = _parse_timestamp(run.timestamp)
        delta = now - ts
        if delta <= timedelta(days=1):
            counters["day"] += 1
        if delta <= timedelta(weeks=1):
            counters["week"] += 1
        if delta <= timedelta(days=30):
            counters["month"] += 1
        if delta <= timedelta(days=90):
            counters["quarter"] += 1
    return counters


def build_schedule(days: int = 7) -> List[Dict[str, Any]]:
    today = datetime.now()
    schedule: List[Dict[str, Any]] = []
    for offset in range(days):
        target = today + timedelta(days=offset)
        schedule.append(
            {
                "label": target.strftime("%A"),
                "date": target.strftime("%b %d"),
                "runs": ["Hourly 02" for _ in range(3)],
            }
        )
    return schedule


def assemble_dashboard_payload() -> Dict[str, Any]:
    runs = load_run_history()
    manual_metrics = load_manual_metrics()
    platform_metrics = load_platform_metrics()
    automated = runs[0] if runs else RunSummary("N/A", "", "N/A", 0, 0, 0, 0.0)
    automated_totals = {
        "total": automated.total,
        "passed": automated.passed,
        "failed": automated.failed,
        "skipped": automated.skipped,
    }
    timeframe = _timeframe_counts(runs)
    payload: Dict[str, Any] = {
        "generated_at": datetime.now().isoformat(),
        "latest_run": automated.as_dict(),
        "latest_runs": [run.as_dict() for run in runs],
        "automated_totals": automated_totals,
        "manual_totals": manual_metrics,
        "platform_metrics": platform_metrics,
        "timeframe_counts": timeframe,
        "schedule": build_schedule(),
    }
    return payload


def render_dashboard() -> None:
    payload = assemble_dashboard_payload()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    html = DASHBOARD_TEMPLATE.replace("__DASHBOARD_DATA__", json.dumps(payload, indent=2))
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Dashboard written to {OUTPUT_PATH}")


DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Automation Quality Dashboard</title>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />
  <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap\" rel=\"stylesheet\" />
  <script src=\"https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js\" defer></script>
  <style>
    :root {
      color-scheme: light dark;
      --bg: #f5f5f8;
      --panel: #ffffff;
      --accent: #1f5eff;
      --accent-soft: rgba(31, 94, 255, 0.1);
      --text: #1f2937;
      --muted: #6b7280;
      --border: #e5e7eb;
      font-family: 'Inter', system-ui, sans-serif;
    }
    body {
      margin: 0;
      padding: 32px;
      background: var(--bg);
      color: var(--text);
    }
    h1 {
      font-size: clamp(1.8rem, 2.5vw, 2.4rem);
      margin-bottom: 4px;
    }
    .subhead {
      color: var(--muted);
      margin-bottom: 24px;
    }
    .layout {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 24px;
    }
    .card {
      background: var(--panel);
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
      border: 1px solid var(--border);
    }
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 16px;
      margin: 12px 0 24px;
    }
    .metric {
      padding: 16px;
      border-radius: 14px;
      background: var(--accent-soft);
    }
    .metric h3 {
      margin: 0;
      font-size: 0.9rem;
      color: var(--muted);
      font-weight: 500;
    }
    .metric .value {
      font-size: 1.8rem;
      font-weight: 700;
      margin-top: 8px;
      color: var(--accent);
    }
    .status-list {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 12px;
    }
    .status-list li {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.7);
    }
    .status-list li span:first-child {
      font-weight: 600;
    }
    .progress-track {
      background: var(--border);
      border-radius: 999px;
      overflow: hidden;
      height: 12px;
      margin-top: 8px;
    }
    .progress-bar {
      height: 100%;
      background: var(--accent);
      width: 0;
      transition: width 0.6s ease;
    }
    table.schedule {
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
    }
    table.schedule th, table.schedule td {
      padding: 12px;
      border: 1px solid var(--border);
      text-align: left;
    }
    table.schedule th {
      background: #eef1ff;
    }
    .muted {
      color: var(--muted);
      font-size: 0.85rem;
    }
    .chart-wrap {
      position: relative;
      height: 260px;
    }
  </style>
</head>
<body>
  <header>
    <h1>Automated Functional Testing Dashboard</h1>
    <p class=\"subhead\">Live view of automation KPIs blended with manual execution progress. Last updated <span id=\"generatedAt\"></span>.</p>
  </header>

  <section class=\"metric-grid\" id=\"headlineMetrics\"></section>

  <div class=\"card\" style=\"margin-bottom:24px;\">
    <h2 style=\"margin-bottom:12px;\">Latest pipeline cadence</h2>
    <div class=\"timeframe-tabs\">
      <button data-key=\"day\">Day</button>
      <button data-key=\"week\">Week</button>
      <button data-key=\"month\">Month</button>
      <button data-key=\"quarter\">Quarter</button>
    </div>
    <div id=\"timeframeValue\" class=\"timeframe-value\"></div>
  </div>

  <section class=\"layout\">
    <div class=\"card\">
      <h2>Latest automation run</h2>
      <canvas id=\"latestRunChart\"></canvas>
      <ul class=\"status-list\" id=\"latestRunMeta\"></ul>
    </div>

    <div class=\"card\">
      <h2>Coverage snapshot</h2>
      <div>
        <h3>Automated tests</h3>
        <div class=\"progress-track\"><div class=\"progress-bar\" id=\"autoProgress\"></div></div>
        <p class=\"muted\" id=\"autoCoverageLabel\"></p>
      </div>
      <div style=\"margin-top:24px;\">
        <h3>Manual tests</h3>
        <div class=\"progress-track\"><div class=\"progress-bar\" id=\"manualProgress\" style=\"background:#48a145;\"></div></div>
        <p class=\"muted\" id=\"manualCoverageLabel\"></p>
      </div>
    </div>

    <div class=\"card\">
      <h2>Platform distribution</h2>
      <div class=\"chart-wrap\">
        <canvas id=\"platformChart\"></canvas>
      </div>
    </div>

    <div class=\"card\" style=\"grid-column: 1 / -1;\">
      <h2>Recent runs timeline</h2>
      <div class=\"chart-wrap\">
        <canvas id=\"recentRunsChart\"></canvas>
      </div>
    </div>

    <div class=\"card\" style=\"grid-column: 1 / -1;\">
      <h2>Execution schedule</h2>
      <table class=\"schedule\" id=\"scheduleTable\"></table>
    </div>
  </section>

  <script>
    const data = __DASHBOARD_DATA__;
    const formatNumber = (value) => new Intl.NumberFormat().format(value);

    const metrics = [
      { label: 'Total', value: data.automated_totals.total },
      { label: 'Passed', value: data.automated_totals.passed },
      { label: 'Failed', value: data.automated_totals.failed },
      { label: 'Not Executed', value: data.automated_totals.skipped },
    ];

    document.getElementById('generatedAt').textContent = new Date(data.generated_at).toLocaleString();

    const metricsContainer = document.getElementById('headlineMetrics');
    metrics.forEach(metric => {
      const wrapper = document.createElement('div');
      wrapper.className = 'metric';
      wrapper.innerHTML = `<h3>${metric.label}</h3><div class="value">${formatNumber(metric.value)}</div>`;
      metricsContainer.appendChild(wrapper);
    });

    const timeframeDisplay = document.getElementById('timeframeValue');
    const updateTimeframe = (key) => {
      const value = data.timeframe_counts[key] || 0;
      timeframeDisplay.textContent = `${value} automation runs in the last ${key}`;
      document.querySelectorAll('.timeframe-tabs button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.key === key);
      });
    };
    document.querySelectorAll('.timeframe-tabs button').forEach(btn => {
      btn.addEventListener('click', () => updateTimeframe(btn.dataset.key));
    });
    updateTimeframe('day');

    if (data.latest_runs.length) {
      const latest = data.latest_runs[0];
      const metaList = document.getElementById('latestRunMeta');
      const items = [
        ['Project', latest.project],
        ['Duration', `${latest.duration.toFixed(1)} s`],
        ['Run ID', latest.run_id],
        ['Timestamp', new Date(latest.timestamp || data.generated_at).toLocaleString()],
      ];
      items.forEach(([label, value]) => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${label}</span><span>${value}</span>`;
        metaList.appendChild(li);
      });

      const latestCtx = document.getElementById('latestRunChart');
      new Chart(latestCtx, {
        type: 'doughnut',
        data: {
          labels: ['Passed', 'Failed', 'Skipped'],
          datasets: [{
            data: [latest.passed, latest.failed, latest.skipped],
            backgroundColor: ['#2563eb', '#ef4444', '#f59e0b'],
          }],
        },
        options: {
          plugins: { legend: { position: 'bottom' } },
        },
      });

      const historyCtx = document.getElementById('recentRunsChart');
      const labels = data.latest_runs.map(item => item.project + ' #' + item.run_id);
      new Chart(historyCtx, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label: 'Passed',
              data: data.latest_runs.map(item => item.passed),
              backgroundColor: '#2563eb',
            },
            {
              label: 'Failed',
              data: data.latest_runs.map(item => item.failed),
              backgroundColor: '#ef4444',
            },
            {
              label: 'Skipped',
              data: data.latest_runs.map(item => item.skipped),
              backgroundColor: '#f59e0b',
            },
          ],
        },
        options: {
          responsive: true,
          plugins: { legend: { position: 'bottom' } },
          scales: { x: { stacked: true }, y: { stacked: true } },
        },
      });
    }

    const auto = data.automated_totals;
    const autoProgress = document.getElementById('autoProgress');
    const autoCompleted = auto.passed;
    const autoRatio = auto.total ? Math.round((autoCompleted / auto.total) * 100) : 0;
    autoProgress.style.width = `${autoRatio}%`;
    document.getElementById('autoCoverageLabel').textContent = `Finished ${autoCompleted} of ${auto.total} scenarios (${autoRatio}%)`;

    const manual = data.manual_totals;
    const manualProgress = document.getElementById('manualProgress');
    const manualCompleted = manual.finished || 0;
    const manualTotal = manual.total || manualCompleted + (manual.pending || 0);
    const manualRatio = manualTotal ? Math.round((manualCompleted / manualTotal) * 100) : 0;
    manualProgress.style.width = `${manualRatio}%`;
    document.getElementById('manualCoverageLabel').textContent = `Finished ${manualCompleted} of ${manualTotal} planned manual tests (${manualRatio}%)`;

    const platformCtx = document.getElementById('platformChart');
    new Chart(platformCtx, {
      type: 'bar',
      data: {
        labels: Object.keys(data.platform_metrics),
        datasets: [{
          label: 'Executions',
          data: Object.values(data.platform_metrics),
          backgroundColor: '#22c55e',
        }],
      },
      options: {
        indexAxis: 'y',
        plugins: { legend: { display: false } },
        scales: { x: { beginAtZero: true } },
      },
    });

    const scheduleTable = document.getElementById('scheduleTable');
    const headerRow = document.createElement('tr');
    ['Day', 'Date', 'Planned runs'].forEach((title) => {
      const th = document.createElement('th');
      th.textContent = title;
      headerRow.appendChild(th);
    });
    scheduleTable.appendChild(headerRow);

    data.schedule.forEach((entry) => {
      const tr = document.createElement('tr');
      const runs = entry.runs.join(', ');
      tr.innerHTML = `<td>${entry.label}</td><td>${entry.date}</td><td>${runs}</td>`;
      scheduleTable.appendChild(tr);
    });
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    render_dashboard()
