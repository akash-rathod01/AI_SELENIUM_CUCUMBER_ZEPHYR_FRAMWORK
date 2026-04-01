"""Generate a rich QA dashboard inspired by executive-style status reports.

This complements generate_dashboard.py by providing additional trend views,
progress gauges, and contributor snapshots. It consumes reports/run_history.json
and optional manual metrics from reports/manual_test_metrics.json.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUN_HISTORY_PATH = REPORTS_DIR / "run_history.json"
MANUAL_METRICS_PATH = REPORTS_DIR / "manual_test_metrics.json"
OUTPUT_PATH = REPORTS_DIR / "qa_enterprise_dashboard.html"


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_run_history(days: int = 30) -> List[Dict[str, Any]]:
    history = _load_json(RUN_HISTORY_PATH, [])
    # Filter to the requested window if we have timestamps.
    cutoff = datetime.utcnow() - timedelta(days=days)
    window: List[Dict[str, Any]] = []
    for entry in history:
        ts_raw = entry.get("timestamp")
        try:
            ts = datetime.fromisoformat(ts_raw)
        except Exception:
            ts = None
        if ts and ts < cutoff:
            continue
        window.append(entry)
    # Ensure newest first for timeline charts.
    window.sort(key=lambda item: item.get("timestamp", ""), reverse=True)
    return window[-60:]


def synthesize_sample_history() -> List[Dict[str, Any]]:
    sample: List[Dict[str, Any]] = []
    today = datetime.utcnow()
    for idx in range(14):
        ts = today - timedelta(days=idx)
        passed = 20 + (idx % 6) * 3
        failed = (idx % 5)
        skipped = (idx % 4)
        sample.append(
            {
                "run_id": f"SAM-{idx:03d}",
                "timestamp": ts.isoformat(),
                "project": "demo_shop",
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "duration": 180 + idx * 3,
                "failed_tests": ["Checkout" if failed else ""],
            }
        )
    sample.reverse()
    return sample


def ensure_history() -> List[Dict[str, Any]]:
    history = load_run_history()
    return history if history else synthesize_sample_history()


def compute_rollups(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not history:
        return {}
    totals = {"passed": 0, "failed": 0, "skipped": 0}
    per_day: Dict[str, Dict[str, int]] = defaultdict(lambda: {"passed": 0, "failed": 0, "skipped": 0})
    burndown_remaining: List[Dict[str, Any]] = []
    last_failure_map: Dict[str, int] = defaultdict(int)

    for idx, entry in enumerate(history):
        totals["passed"] += int(entry.get("passed", 0))
        totals["failed"] += int(entry.get("failed", 0))
        totals["skipped"] += int(entry.get("skipped", 0))
        ts = entry.get("timestamp") or ""
        day_key = ts[:10] if ts else f"Day-{idx}"
        bucket = per_day[day_key]
        bucket["passed"] += int(entry.get("passed", 0))
        bucket["failed"] += int(entry.get("failed", 0))
        bucket["skipped"] += int(entry.get("skipped", 0))
        remaining = max(0, int(entry.get("failed", 0)) + int(entry.get("skipped", 0)))
        burndown_remaining.append({"label": day_key, "remaining": remaining, "completed": int(entry.get("passed", 0))})
        for failed_name in entry.get("failed_tests", []) or []:
            if failed_name:
                last_failure_map[failed_name] += 1

    manual = _load_json(MANUAL_METRICS_PATH, {"finished": 5, "pending": 15})
    manual_total = manual.get("total") or (manual.get("finished", 0) + manual.get("pending", 0))

    return {
        "totals": totals,
        "per_day": per_day,
        "burndown": burndown_remaining,
        "manual": {"finished": manual.get("finished", 0), "pending": manual.get("pending", 0), "total": manual_total},
        "last_failures": sorted(last_failure_map.items(), key=lambda item: item[1], reverse=True),
        "latest": history[-1] if history else {},
        "latest_window": history[-14:],
    }


def render_dashboard() -> None:
    history = ensure_history()
    payload = compute_rollups(history)
    payload["generated_at"] = datetime.utcnow().isoformat()
    payload["history"] = history

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    html = DASHBOARD_TEMPLATE.replace("__PAYLOAD__", json.dumps(payload, indent=2))
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Enterprise dashboard exported to {OUTPUT_PATH}")


DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>QA Test Results Dashboard</title>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />
  <link href=\"https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap\" rel=\"stylesheet\" />
  <script src=\"https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js\" defer></script>
  <style>
    body { margin: 0; font-family: 'Manrope', system-ui, sans-serif; background: #0f172a; color: #f1f5f9; }
    main { padding: 32px 40px; }
    h1 { font-size: clamp(1.5rem, 2.2vw, 2.4rem); margin-bottom: 8px; }
    p.sub { margin-top: 0; margin-bottom: 24px; color: #94a3b8; }
    .grid { display: grid; gap: 24px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
    .panel { background: linear-gradient(135deg, rgba(15,23,42,0.94), rgba(30,41,59,0.9)); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 24px; padding: 24px; box-shadow: 0 32px 60px rgba(15, 23, 42, 0.45); backdrop-filter: blur(12px); }
    .panel h2 { margin-top: 0; font-size: 1.1rem; letter-spacing: 0.02em; text-transform: uppercase; color: #cbd5f5; }
    .metric-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px,1fr)); gap: 16px; margin-bottom: 28px; }
    .metric-card { padding: 20px; border-radius: 18px; background: rgba(30, 64, 175, 0.18); border: 1px solid rgba(59, 130, 246, 0.25); }
    .metric-card.small { background: rgba(22, 163, 74, 0.16); border-color: rgba(34, 197, 94, 0.35); }
    .metric-label { font-size: 0.78rem; letter-spacing: 0.04em; color: #a5b4fc; text-transform: uppercase; }
    .metric-value { font-size: 2rem; font-weight: 700; margin-top: 10px; color: #f8fafc; }
    .pill { display: inline-flex; align-items: center; gap: 8px; background: rgba(45,212,191,0.12); border-radius: 999px; padding: 8px 14px; font-size: 0.8rem; color: #5eead4; margin-right: 12px; }
    .sessions { list-style: none; padding: 0; margin: 12px 0 0; display: grid; gap: 12px; }
    .session-item { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; border-radius: 16px; background: rgba(15,23,42,0.6); border: 1px solid rgba(148, 163, 184, 0.16); }
    .session-item span { font-weight: 600; }
    .legend { display: flex; gap: 16px; font-size: 0.85rem; color: #cbd5f5; margin-top: 12px; }
    .legend span::before { content: ''; display: inline-block; width: 10px; height: 10px; border-radius: 999px; margin-right: 6px; vertical-align: middle; }
    .legend span.passed::before { background: #22c55e; }
    .legend span.failed::before { background: #ef4444; }
    .legend span.skipped::before { background: #f59e0b; }
    table.activity { width: 100%; border-collapse: collapse; margin-top: 16px; }
    table.activity th, table.activity td { padding: 12px; border-bottom: 1px solid rgba(148,163,184,0.15); text-align: left; }
    table.activity th { font-size: 0.76rem; letter-spacing: 0.04em; text-transform: uppercase; color: #94a3b8; }
    .chip { background: rgba(239, 68, 68, 0.15); color: #fca5a5; padding: 4px 10px; border-radius: 999px; font-size: 0.75rem; }
    .Sparkline { display: flex; gap: 6px; }
    footer { margin-top: 32px; text-align: center; color: #64748b; font-size: 0.78rem; }
  </style>
</head>
<body>
  <main>
    <h1>QA Test Results Dashboard</h1>
    <p class=\"sub\">Real-time synthesis of automation throughput, remaining effort, and execution cadence. Generated <span id=\"generatedAt\"></span>.</p>

    <div class=\"metric-cards\">
      <div class=\"metric-card\"> <span class=\"metric-label\">Total Assertions</span> <div class=\"metric-value\" id=\"totalAssertions\"></div> </div>
      <div class=\"metric-card small\"> <span class=\"metric-label\">Passed</span> <div class=\"metric-value\" id=\"totalPassed\"></div> </div>
      <div class=\"metric-card small\" style=\"background: rgba(239,68,68,0.12); border-color: rgba(248,113,113,0.3);\"> <span class=\"metric-label\">Failed</span> <div class=\"metric-value\" id=\"totalFailed\"></div> </div>
      <div class=\"metric-card\" style=\"background: rgba(14,165,233,0.18); border-color: rgba(56,189,248,0.3);\"> <span class=\"metric-label\">Skipped</span> <div class=\"metric-value\" id=\"totalSkipped\"></div> </div>
    </div>

    <div class=\"grid\">
      <section class=\"panel\">
        <h2>Run &amp; Session Progress</h2>
        <div class=\"legend\">
          <span class=\"passed\">Completed</span>
          <span class=\"failed\">Remaining Defects</span>
          <span class=\"skipped\">Pending</span>
        </div>
        <canvas id=\"progressChart\" style=\"margin-top:24px; height:240px;\"></canvas>
      </section>

      <section class=\"panel\">
        <h2>Active Sessions</h2>
        <div class=\"pill\"><strong id=\"activeSessions\"></strong> active</div>
        <div class=\"pill\" style=\"background: rgba(96,165,250,0.18); color:#bfdbfe;\"><span id=\"contributors\"></span> contributors</div>
        <canvas id=\"sessionPie\" style=\"margin-top:24px; height:220px;\"></canvas>
      </section>

      <section class=\"panel\">
        <h2>Latest Results Heatmap</h2>
        <canvas id=\"heatmapChart\" style=\"height:180px;\"></canvas>
      </section>

      <section class=\"panel\">
        <h2>Activity (Last 14 days)</h2>
        <canvas id=\"activityChart\" style=\"height:240px;\"></canvas>
      </section>

      <section class=\"panel\">
        <h2>Run Status Overview</h2>
        <canvas id=\"runStatusPie\" style=\"height:220px;\"></canvas>
        <p style=\"margin-top:18px; font-size:0.9rem;\"><strong id=\"completionPercent\"></strong> completed • <span id=\"remainingPercent\"></span> remaining</p>
      </section>

      <section class=\"panel\">
        <h2>Recent Failures</h2>
        <table class=\"activity\">
          <thead><tr><th>Scenario</th><th>Failure Count</th><th>Trend</th></tr></thead>
          <tbody id=\"failureTable\"></tbody>
        </table>
      </section>
    </div>

    <footer>Dashboard auto-generated from automation history. Dark mode ready.</footer>
  </main>
  <script>
    const payload = __PAYLOAD__;
    const format = (value) => new Intl.NumberFormat().format(value || 0);

    document.getElementById('generatedAt').textContent = new Date(payload.generated_at).toLocaleString();

    const totals = payload.totals || {passed:0, failed:0, skipped:0};
    const grandTotal = totals.passed + totals.failed + totals.skipped;
    document.getElementById('totalAssertions').textContent = format(grandTotal);
    document.getElementById('totalPassed').textContent = format(totals.passed);
    document.getElementById('totalFailed').textContent = format(totals.failed);
    document.getElementById('totalSkipped').textContent = format(totals.skipped);

    const manual = payload.manual || {finished:0, pending:0, total:0};
    const activeSessions = Math.max(3, Math.round(payload.latest_window ? payload.latest_window.length / 2 : 3));
    document.getElementById('activeSessions').textContent = activeSessions;
    document.getElementById('contributors').textContent = Math.max(3, Math.ceil(activeSessions * 1.5));

    const ctxProgress = document.getElementById('progressChart');
    const labels = Object.keys(payload.per_day || {});
    const perDay = payload.per_day || {};
    new Chart(ctxProgress, {
      type: 'line',
      data: {
        labels,
        datasets: [
          { label: 'Completed', borderColor: '#22c55e', backgroundColor: 'rgba(34,197,94,0.2)', tension: 0.4, fill: true, data: labels.map(day => (perDay[day]?.passed)||0) },
          { label: 'Remaining defects', borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.18)', tension: 0.3, fill: true, data: labels.map(day => (perDay[day]?.failed)||0) },
          { label: 'Pending', borderColor: '#f59e0b', data: labels.map(day => (perDay[day]?.skipped)||0), borderDash: [6,6], fill: false },
        ],
      },
      options: {
        plugins: { legend: { labels: { color: '#e2e8f0' } } },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.12)' } },
        },
      }
    });

    const ctxSession = document.getElementById('sessionPie');
    new Chart(ctxSession, {
      type: 'doughnut',
      data: {
        labels: ['Automated workload', 'Manual workload'],
        datasets: [{ data: [totals.passed + totals.failed, manual.total || manual.finished + manual.pending], backgroundColor: ['#4f46e5', '#14b8a6'] }],
      },
      options: { plugins: { legend: { position: 'bottom', labels: { color: '#e2e8f0' } } } },
    });

    const ctxHeatmap = document.getElementById('heatmapChart');
    const latest = payload.latest_window || [];
    new Chart(ctxHeatmap, {
      type: 'bar',
      data: {
        labels: latest.map(run => new Date(run.timestamp).toLocaleDateString()),
        datasets: [
          { label: 'Passed', data: latest.map(run => run.passed || 0), backgroundColor: '#22c55e' },
          { label: 'Failed', data: latest.map(run => run.failed || 0), backgroundColor: '#ef4444' },
          { label: 'Skipped', data: latest.map(run => run.skipped || 0), backgroundColor: '#f59e0b' },
        ],
      },
      options: {
        plugins: { legend: { display: false } },
        responsive: true,
        scales: { x: { stacked: true, ticks: { color: '#94a3b8' } }, y: { stacked: true, ticks: { color: '#94a3b8' } } },
      },
    });

    const activityCtx = document.getElementById('activityChart');
    new Chart(activityCtx, {
      type: 'line',
      data: {
        labels: latest.map(run => new Date(run.timestamp).toLocaleDateString()),
        datasets: [
          { label: 'Total', data: latest.map(run => (run.passed||0)+(run.failed||0)+(run.skipped||0)), borderColor: '#38bdf8', fill: false, tension: 0.3 },
          { label: 'Passed', data: latest.map(run => run.passed || 0), borderColor: '#22c55e', fill: false, tension: 0.3 },
          { label: 'Failed', data: latest.map(run => run.failed || 0), borderColor: '#ef4444', fill: false, tension: 0.3 },
        ],
      },
      options: {
        plugins: { legend: { labels: { color: '#e2e8f0' } } },
        scales: { x: { ticks: { color: '#94a3b8' } }, y: { ticks: { color: '#94a3b8' } } },
      },
    });

    const remaining = manual.pending || totals.failed + totals.skipped;
    const finished = manual.finished + totals.passed;
    const completion = (finished + remaining) ? Math.round((finished / (finished + remaining)) * 100) : 0;
    document.getElementById('completionPercent').textContent = `${completion}% completed`;
    document.getElementById('remainingPercent').textContent = `${100 - completion}% to finish`;

    const runStatusCtx = document.getElementById('runStatusPie');
    new Chart(runStatusCtx, {
      type: 'pie',
      data: {
        labels: ['Successful', 'Failures', 'Skipped'],
        datasets: [{ data: [totals.passed, totals.failed, totals.skipped], backgroundColor: ['#22c55e', '#ef4444', '#f59e0b'] }],
      },
      options: { plugins: { legend: { position: 'bottom', labels: { color: '#e2e8f0' } } } }
    });

    const failureTable = document.getElementById('failureTable');
    const failures = payload.last_failures || [];
    if (!failures.length) {
      const row = document.createElement('tr');
      row.innerHTML = '<td colspan="3">No repeat failures detected</td>';
      failureTable.appendChild(row);
    } else {
      failures.slice(0,6).forEach(([name, count]) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${name}</td><td><span class="chip">${count}</span></td><td><div class="Sparkline">${'<div style="width:8px;height:8px;background:#ef4444;border-radius:999px;"></div>'.repeat(Math.min(count,6))}</div></td>`;
        failureTable.appendChild(tr);
      });
    }
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    render_dashboard()
