"""Alert channels: Telegram for instant, Email for digest + health."""
from __future__ import annotations

import asyncio
from email.message import EmailMessage
from typing import Iterable

import aiosmtplib
import httpx

from monitor import config


def _tg_enabled() -> bool:
    return bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID)


def _email_enabled() -> bool:
    return bool(config.SMTP_HOST and config.SMTP_USER and config.EMAIL_TO)


async def send_telegram(text: str) -> None:
    if not _tg_enabled():
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    # Telegram limit is 4096 chars
    chunks = [text[i:i + 3800] for i in range(0, len(text), 3800)] or [text]
    async with httpx.AsyncClient(timeout=15) as client:
        for chunk in chunks:
            try:
                r = await client.post(url, json={
                    "chat_id": config.TELEGRAM_CHAT_ID,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                })
                r.raise_for_status()
            except Exception as e:
                print(f"[telegram] send failed: {e}")


async def send_email(subject: str, body_text: str, body_html: str | None = None) -> None:
    if not _email_enabled():
        return
    msg = EmailMessage()
    msg["From"] = config.EMAIL_FROM
    msg["To"] = config.EMAIL_TO
    msg["Subject"] = subject
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")
    try:
        await aiosmtplib.send(
            msg,
            hostname=config.SMTP_HOST,
            port=config.SMTP_PORT,
            username=config.SMTP_USER,
            password=config.SMTP_PASSWORD,
            start_tls=True,
        )
    except Exception as e:
        print(f"[email] send failed: {e}")


# ------------- High-level helpers -------------
def format_instant_html(site_name: str, url: str, changes: list[dict]) -> str:
    lines = [f"<b>🔔 {site_name}</b>", f"<a href=\"{url}\">{url}</a>", ""]
    for c in changes[:10]:
        lines.append(f"• [{c['type']}] {c['summary']}")
    if len(changes) > 10:
        lines.append(f"…and {len(changes) - 10} more")
    return "\n".join(lines)


async def send_instant_alert(site_name: str, url: str, changes: list[dict]) -> None:
    text = format_instant_html(site_name, url, changes)
    # Telegram-first for instants
    await send_telegram(text)


def format_digest(items: list[dict]) -> tuple[str, str]:
    """Return (plain, html) for digest email."""
    by_site: dict[str, list[dict]] = {}
    for it in items:
        by_site.setdefault(it["name"], []).append(it)

    plain_lines = [f"NEET Counselling Digest — {len(items)} updates across {len(by_site)} sites", ""]
    html_lines = ["<h2>NEET Counselling Digest</h2>",
                  f"<p><b>{len(items)}</b> updates across <b>{len(by_site)}</b> sites.</p>"]

    for name, group in by_site.items():
        url = group[0].get("url", "")
        plain_lines.append(f"--- {name} ({url}) ---")
        html_lines.append(f"<h3>{name}</h3><p><a href='{url}'>{url}</a></p><ul>")
        for it in group:
            plain_lines.append(f"  [{it['change_type']}] {it['summary']}")
            html_lines.append(f"<li><b>{it['change_type']}</b>: {it['summary']}</li>")
        plain_lines.append("")
        html_lines.append("</ul>")

    return "\n".join(plain_lines), "\n".join(html_lines)


async def send_digest_email(items: list[dict]) -> None:
    if not items:
        return
    plain, html = format_digest(items)
    subject = f"NEET Digest: {len(items)} updates"
    await send_email(subject, plain, html)


async def send_health_alert(failing_sites: list[dict]) -> None:
    if not failing_sites:
        return
    lines = [f"⚠️ {len(failing_sites)} sites failing 3+ runs in a row:", ""]
    for s in failing_sites[:20]:
        lines.append(f"• {s['name']} — {s.get('last_error','?')}")
    text = "\n".join(lines)
    await send_telegram(text)


async def bulk_send(coros: Iterable) -> None:
    """Run a bunch of send coroutines concurrently, swallowing errors."""
    results = await asyncio.gather(*coros, return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            print(f"[notifier] error: {r}")
