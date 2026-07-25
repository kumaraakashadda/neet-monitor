"""Main orchestrator: read CSV, scan all sites in parallel, diff, alert."""
from __future__ import annotations

import asyncio
import csv
from datetime import datetime, timezone
from typing import Any

from monitor import config, dashboard, notifier, storage
from monitor.differ import diff_snapshots, dedupe_key
from monitor.extractor import extract
from monitor.fetcher import FetchError, fetch


def load_sites() -> list[dict[str, str]]:
    with config.WEBSITES_CSV.open(encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if row.get("url")]


async def process_site(sem: asyncio.Semaphore, site: dict) -> dict:
    """Fetch, extract, diff, record. Returns per-site result summary."""
    url = site["url"].strip()
    name = site["name"].strip()
    priority = (site.get("priority") or "LOW").strip().upper()
    result: dict[str, Any] = {
        "url": url, "name": name, "priority": priority,
        "ok": False, "changes": [], "error": None,
    }

    async with sem:
        try:
            _final_url, body = await fetch(url)
        except FetchError as e:
            storage.record_fail(url, name, str(e))
            result["error"] = str(e)
            return result

    try:
        new_snap = extract(url, body)
    except Exception as e:
        storage.record_fail(url, name, f"extract: {e}")
        result["error"] = f"extract: {e}"
        return result

    old_snap = storage.load_snapshot(url)
    changes = diff_snapshots(old_snap, new_snap)

    # Save current snapshot regardless (so next run has baseline)
    storage.save_snapshot(url, new_snap)
    storage.record_ok(url, name)
    result["ok"] = True

    # Filter out duplicates we've already alerted on
    fresh_changes = []
    for ch in changes:
        key = dedupe_key(url, ch["type"], ch["detail"])
        if storage.already_alerted(key):
            continue
        fresh_changes.append(ch)
        storage.mark_alerted(key)
        storage.record_change(url, name, priority, ch["type"], ch["summary"],
                              {"detail": ch["detail"]})

    result["changes"] = fresh_changes
    return result


async def maybe_send_digest() -> None:
    """Once per day at DIGEST_HOUR_UTC, drain the queue and email."""
    now = datetime.now(timezone.utc)
    if now.hour != config.DIGEST_HOUR_UTC:
        return
    # Only in the first half of the hour to avoid double-sends
    if now.minute >= 30:
        return
    items = storage.drain_digest()
    if items:
        await notifier.send_digest_email(items)


async def run() -> None:
    sites = load_sites()
    run_id = storage.start_run()
    print(f"[run {run_id}] scanning {len(sites)} sites")

    sem = asyncio.Semaphore(config.CONCURRENCY)
    tasks = [asyncio.create_task(process_site(sem, s)) for s in sites]
    results = await asyncio.gather(*tasks)

    ok = sum(1 for r in results if r["ok"])
    failed = len(results) - ok
    changed = sum(1 for r in results if r["changes"])

    # Route changes: HIGH → instant Telegram, MEDIUM/LOW → digest queue
    instant_tasks = []
    for r in results:
        if not r["changes"]:
            continue
        if r["priority"] == "HIGH":
            instant_tasks.append(
                notifier.send_instant_alert(r["name"], r["url"], r["changes"])
            )
        else:
            for ch in r["changes"]:
                storage.queue_for_digest(
                    r["url"], r["name"], r["priority"], ch["type"], ch["summary"]
                )

    if instant_tasks:
        await notifier.bulk_send(instant_tasks)

    await maybe_send_digest()

    storage.finish_run(run_id, len(sites), ok, failed, changed)

    # Health check: notify if many sites failing
    from monitor.storage import health_report
    hr = health_report()
    failing = hr["failing_sites"]
    if len(failing) >= 5:
        await notifier.send_health_alert(failing)

    dashboard.render()
    print(f"[run {run_id}] done — ok={ok} failed={failed} changes={changed}")


if __name__ == "__main__":
    asyncio.run(run())
