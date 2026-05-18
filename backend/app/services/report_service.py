"""
HTML Report Service — generates enterprise-grade bug and test execution reports.
Uses Jinja2 templates rendered to static HTML files served by FastAPI.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, DictLoader

from app.config import settings


BUG_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QAgent Bug Report — {{ run.run_id }}</title>
<style>
  :root {
    --primary: #6366f1; --bg: #0f172a; --card: #1e293b;
    --border: #334155; --text: #e2e8f0; --muted: #94a3b8;
    --red: #ef4444; --yellow: #f59e0b; --green: #22c55e; --blue: #3b82f6;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'Inter', system-ui, sans-serif; padding: 2rem; }
  h1 { font-size: 1.8rem; font-weight: 700; margin-bottom: .5rem; }
  .meta { color: var(--muted); font-size: .875rem; margin-bottom: 2rem; }
  .summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem; }
  .stat-card { background: var(--card); border: 1px solid var(--border); border-radius: .75rem; padding: 1.25rem; }
  .stat-card .label { color: var(--muted); font-size: .75rem; text-transform: uppercase; letter-spacing: .05em; }
  .stat-card .value { font-size: 2rem; font-weight: 700; margin-top: .25rem; }
  .value.passed { color: var(--green); } .value.failed { color: var(--red); }
  .value.total { color: var(--primary); } .value.bugs { color: var(--yellow); }
  .section-title { font-size: 1.1rem; font-weight: 600; margin: 2rem 0 1rem; border-bottom: 1px solid var(--border); padding-bottom: .5rem; }
  .bug-card { background: var(--card); border: 1px solid var(--border); border-radius: .75rem; padding: 1.5rem; margin-bottom: 1rem; }
  .bug-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; }
  .bug-id { color: var(--muted); font-size: .875rem; }
  .badge { display: inline-block; padding: .2rem .6rem; border-radius: 9999px; font-size: .75rem; font-weight: 600; }
  .badge.critical { background: #7f1d1d; color: #fca5a5; }
  .badge.high { background: #7c2d12; color: #fdba74; }
  .badge.medium { background: #713f12; color: #fde68a; }
  .badge.low { background: #1c3a1c; color: #86efac; }
  .badge.open { background: #1e1b4b; color: #a5b4fc; }
  .badge.fixed { background: #14532d; color: #86efac; }
  .detail-row { display: grid; grid-template-columns: 140px 1fr; gap: .5rem; margin-bottom: .5rem; font-size: .875rem; }
  .detail-label { color: var(--muted); }
  .steps-list { list-style: none; }
  .steps-list li { display: flex; gap: .75rem; margin-bottom: .5rem; font-size: .875rem; }
  .step-num { background: var(--border); border-radius: .25rem; padding: .1rem .4rem; font-size: .7rem; flex-shrink: 0; }
  .fix-box { background: #0c4a0c; border: 1px solid #166534; border-radius: .5rem; padding: 1rem; margin-top: 1rem; font-size: .875rem; }
  .fix-box .fix-title { color: #86efac; font-weight: 600; margin-bottom: .5rem; }
  .screenshots { display: flex; gap: .5rem; flex-wrap: wrap; margin-top: .75rem; }
  .screenshots img { height: 120px; border-radius: .5rem; border: 1px solid var(--border); cursor: pointer; }
  footer { margin-top: 3rem; color: var(--muted); font-size: .75rem; text-align: center; }
</style>
</head>
<body>

<h1>QAgent — Test Execution Report</h1>
<p class="meta">Project: {{ project_name }} &nbsp;|&nbsp; Run: {{ run.run_id }} &nbsp;|&nbsp; Environment: {{ run.environment }} &nbsp;|&nbsp; Generated: {{ generated_at }}</p>

<div class="summary-grid">
  <div class="stat-card"><div class="label">Total Cases</div><div class="value total">{{ run.total_cases }}</div></div>
  <div class="stat-card"><div class="label">Passed</div><div class="value passed">{{ run.passed }}</div></div>
  <div class="stat-card"><div class="label">Failed</div><div class="value failed">{{ run.failed }}</div></div>
  <div class="stat-card"><div class="label">Bugs Found</div><div class="value bugs">{{ bugs | length }}</div></div>
</div>

{% if bugs %}
<h2 class="section-title">Bug Reports ({{ bugs | length }})</h2>
{% for bug in bugs %}
<div class="bug-card">
  <div class="bug-header">
    <div>
      <span class="bug-id">{{ bug.bug_id }}</span>
      <h3 style="margin-top:.25rem">{{ bug.title }}</h3>
    </div>
    <div style="display:flex;gap:.5rem">
      <span class="badge {{ bug.severity }}">{{ bug.severity | upper }}</span>
      <span class="badge {{ bug.status }}">{{ bug.status | upper }}</span>
    </div>
  </div>

  <div class="detail-row"><span class="detail-label">Description</span><span>{{ bug.description }}</span></div>
  <div class="detail-row"><span class="detail-label">Environment</span><span>{{ bug.environment or 'N/A' }}</span></div>
  <div class="detail-row"><span class="detail-label">Expected</span><span>{{ bug.expected_result }}</span></div>
  <div class="detail-row"><span class="detail-label">Actual</span><span style="color:#f87171">{{ bug.actual_result }}</span></div>

  {% if bug.steps_to_reproduce %}
  <div style="margin-top:.75rem">
    <div class="detail-label" style="margin-bottom:.5rem">Steps to Reproduce</div>
    <ol class="steps-list">
      {% for step in bug.steps_to_reproduce %}
      <li><span class="step-num">{{ loop.index }}</span>{{ step }}</li>
      {% endfor %}
    </ol>
  </div>
  {% endif %}

  {% if bug.root_cause %}
  <div class="detail-row" style="margin-top:.75rem"><span class="detail-label">Root Cause</span><span>{{ bug.root_cause }}</span></div>
  {% endif %}

  {% if bug.suggested_fix %}
  <div class="fix-box">
    <div class="fix-title">Suggested Fix</div>
    {{ bug.suggested_fix }}
  </div>
  {% endif %}

  {% if bug.screenshots %}
  <div class="screenshots">
    {% for ss in bug.screenshots %}
    <img src="{{ ss }}" alt="screenshot" loading="lazy">
    {% endfor %}
  </div>
  {% endif %}
</div>
{% endfor %}
{% endif %}

<footer>Generated by QAgent AI Platform &nbsp;|&nbsp; {{ generated_at }}</footer>
</body>
</html>
"""

EXECUTION_SUMMARY_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>QAgent Execution Summary — {{ run.run_id }}</title>
<style>
  :root { --bg:#0f172a; --card:#1e293b; --border:#334155; --text:#e2e8f0; --muted:#94a3b8; --primary:#6366f1; }
  body { background:var(--bg); color:var(--text); font-family:system-ui,sans-serif; padding:2rem; }
  table { width:100%; border-collapse:collapse; font-size:.875rem; }
  th { text-align:left; padding:.75rem 1rem; background:var(--card); color:var(--muted); font-size:.75rem; text-transform:uppercase; }
  td { padding:.75rem 1rem; border-bottom:1px solid var(--border); }
  .passed{color:#22c55e} .failed{color:#ef4444} .blocked{color:#f59e0b} .skipped{color:#64748b}
  h1 { margin-bottom:2rem; }
</style>
</head>
<body>
<h1>Execution Summary — {{ run.run_id }}</h1>
<table>
  <thead><tr><th>Test Case</th><th>Type</th><th>Status</th><th>Duration</th><th>Bugs</th></tr></thead>
  <tbody>
  {% for row in execution_rows %}
  <tr>
    <td>{{ row.tc_id }} — {{ row.title }}</td>
    <td>{{ row.test_type }}</td>
    <td class="{{ row.status }}">{{ row.status | upper }}</td>
    <td>{{ row.duration_ms }}ms</td>
    <td>{{ row.bugs }}</td>
  </tr>
  {% endfor %}
  </tbody>
</table>
</body>
</html>
"""


class ReportService:
    def __init__(self):
        self._env = Environment(loader=DictLoader({
            "bug_report.html": BUG_REPORT_TEMPLATE,
            "execution_summary.html": EXECUTION_SUMMARY_TEMPLATE,
        }))
        self._reports_dir = Path(settings.REPORTS_DIR)

    def generate_bug_report(
        self,
        run: Any,
        bugs: list[Any],
        project_name: str,
        execution_rows: list[dict] | None = None,
    ) -> str:
        """Render HTML bug report. Returns file path."""
        tmpl = self._env.get_template("bug_report.html")
        html = tmpl.render(
            run=run,
            bugs=bugs,
            project_name=project_name,
            generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        )
        out_path = self._reports_dir / "runs" / str(run.id) / "bug_report.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        return str(out_path)

    def generate_execution_summary(
        self,
        run: Any,
        execution_rows: list[dict],
    ) -> str:
        tmpl = self._env.get_template("execution_summary.html")
        html = tmpl.render(
            run=run,
            execution_rows=execution_rows,
            generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        )
        out_path = self._reports_dir / "runs" / str(run.id) / "execution_summary.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        return str(out_path)
