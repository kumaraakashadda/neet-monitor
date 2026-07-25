"""Compare old vs new snapshots. Produce meaningful, keyword-gated changes."""
from __future__ import annotations

import hashlib
from typing import Iterable

from monitor.config import ALERT_KEYWORDS


def _has_keyword(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in ALERT_KEYWORDS)


def _sig(items: Iterable[str]) -> set[str]:
    return {s.strip().lower() for s in items if s and s.strip()}


def dedupe_key(url: str, change_type: str, detail: str) -> str:
    raw = f"{url}||{change_type}||{detail.strip().lower()}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def diff_snapshots(old: dict | None, new: dict) -> list[dict]:
    """Return a list of change dicts: {type, detail, summary}.

    First-time-ever snapshots are NOT alerts (would flood inbox).
    Cosmetic changes (only whitespace / noise) yield no changes.
    Only changes containing at least one ALERT_KEYWORD are surfaced.
    """
    if old is None:
        return []  # baseline pass

    changes: list[dict] = []

    # 1) New notice links
    old_notices = _sig(old.get("notice_links", []))
    new_notices = _sig(new.get("notice_links", []))
    for link in new_notices - old_notices:
        if _has_keyword(link):
            changes.append({
                "type": "notice_added",
                "detail": link,
                "summary": f"New notice link: {link}",
            })
    for link in old_notices - new_notices:
        if _has_keyword(link):
            changes.append({
                "type": "notice_removed",
                "detail": link,
                "summary": f"Notice link removed: {link}",
            })

    # 2) New PDFs
    old_pdfs = _sig(old.get("pdf_links", []))
    new_pdfs = _sig(new.get("pdf_links", []))
    for pdf in new_pdfs - old_pdfs:
        # PDFs always alert regardless of keyword — new PDFs on gov sites
        # are almost always meaningful notifications.
        changes.append({
            "type": "pdf_added",
            "detail": pdf,
            "summary": f"New PDF: {pdf}",
        })
    for pdf in old_pdfs - new_pdfs:
        changes.append({
            "type": "pdf_removed",
            "detail": pdf,
            "summary": f"PDF removed: {pdf}",
        })

    # 3) Notice text blocks — line-level diff, keyword-gated
    old_texts = _sig(old.get("notice_texts", []))
    new_texts = _sig(new.get("notice_texts", []))
    for txt in new_texts - old_texts:
        if _has_keyword(txt):
            snippet = txt[:280] + ("…" if len(txt) > 280 else "")
            changes.append({
                "type": "notice_text_added",
                "detail": snippet,
                "summary": f"New content: {snippet}",
            })

    # 4) Headings changed
    old_h = _sig(old.get("headings", []))
    new_h = _sig(new.get("headings", []))
    for h in new_h - old_h:
        if _has_keyword(h):
            changes.append({
                "type": "heading_added",
                "detail": h,
                "summary": f"New heading: {h}",
            })

    # 5) Title change
    if (old.get("title") or "").strip().lower() != (new.get("title") or "").strip().lower():
        if _has_keyword(new.get("title", "")):
            changes.append({
                "type": "title_changed",
                "detail": new.get("title", ""),
                "summary": f"Page title changed: {new.get('title','')}",
            })

    return changes
