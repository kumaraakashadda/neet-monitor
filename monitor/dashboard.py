"""Generate a single-file HTML dashboard summarizing the last run."""
from __future__ import annotations

from datetime import datetime, timezone
from jinja2 import Template

from monitor.config import DASHBOARD_PATH
from monitor.storage import health_report

TEMPLATE = Template("""<!doctype html>
<html><head><meta charset="utf-8"><title>NEET Monitor</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#222}
 h1{margin:0 0 .5rem} .muted{color:#666}
 table{border-collapse:collapse;width:100%;margin:1rem 0}
 th,td{border:1px solid #ddd;padding:.4rem .6rem;text-align:left;font-size:.9rem}
 th{background:#f4f4f4}
 .ok{color:#0a7a2f} .fail{color:#b00020} .high{background:#fff6d5}
 .card{background:#fafafa;border:1px solid #eee;padding:1rem;border-radius:8px;margin:.5rem 0}
</style></head><body>
<h1>NEET Counselling Monitor</h1>
<p class="muted">Generated {{ now }} UTC</p>

<div class="card">
  <b>Last run:</b>
  {% if last_run %}
    started {{ last_run.started_at }} — finished {{ last_run.finished_at }}<br>
    total {{ last_run.total }}, ok {{ last_run.ok }}, failed {{ last_run.failed }},
    changes {{ last_run.changed }}
  {% else %} no runs yet {% endif %}
</div>

<h2>Failing sites ({{ failing|length }})</h2>
{% if failing %}
<table><tr><th>Site</th><th>URL</th><th>Streak</th><th>Last error</th></tr>
{% for s in failing %}
<tr><td>{{ s.name }}</td><td>{{ s.url }}</td>
<td>{{ s.consecutive_failures }}</td><td>{{ s.last_error }}</td></tr>
{% endfor %}
</table>
{% else %}<p class="ok">None 🎉</p>{% endif %}

<h2>Recent changes ({{ recent|length }})</h2>
<table><tr><th>When</th><th>Site</th><th>Priority</th><th>Type</th><th>Summary</th></tr>
{% for c in recent %}
<tr class="{% if c.priority == 'HIGH' %}high{% endif %}">
  <td>{{ c.detected_at }}</td><td>{{ c.name }}</td><td>{{ c.priority }}</td>
  <td>{{ c.change_type }}</td><td>{{ c.summary[:200] }}</td>
</tr>
{% endfor %}
</table>

<h2>All sites</h2>
<table><tr><th>Site</th><th>URL</th><th>Last OK</th><th>Last Fail</th><th>Streak</th></tr>
{% for s in statuses %}
<tr><td>{{ s.name }}</td><td>{{ s.url }}</td>
<td class="ok">{{ s.last_ok_at or '-' }}</td>
<td class="{% if s.consecutive_failures %}fail{% endif %}">{{ s.last_fail_at or '-' }}</td>
<td>{{ s.consecutive_failures or 0 }}</td></tr>
{% endfor %}
</table>
</body></html>""")


def render() -> None:
    r = health_report()
    html = TEMPLATE.render(
        now=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        last_run=r["last_run"],
        failing=r["failing_sites"],
        recent=r["recent_changes"],
        statuses=r["all_statuses"],
    )
    DASHBOARD_PATH.write_text(html, encoding="utf-8")
