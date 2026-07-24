"""Turn raw HTML into a structured 'snapshot' we can diff meaningfully."""
from __future__ import annotations

import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from monitor.config import NOISE_PATTERNS

_NOISE_RE = [re.compile(p, re.IGNORECASE) for p in NOISE_PATTERNS]

# Selectors commonly used for "latest news / notices / notifications" on gov sites
NOTICE_HINT_KEYWORDS = [
    "notic", "notif", "announce", "latest", "update", "news",
    "circular", "important", "recent", "schedule",
]


def strip_noise(text: str) -> str:
    for pat in _NOISE_RE:
        text = pat.sub("", text)
    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _looks_like_notice_container(tag) -> bool:
    """Heuristic: does this element look like a notices/announcements block?"""
    hints = " ".join(
        filter(None, [tag.get("id", ""), " ".join(tag.get("class", []))])
    ).lower()
    return any(k in hints for k in NOTICE_HINT_KEYWORDS)


def extract(base_url: str, html: str) -> dict:
    """Return a normalized snapshot dict."""
    if html.startswith("[PDF DOCUMENT]"):
        return {
            "title": "PDF",
            "pdf_links": [base_url],
            "notice_links": [],
            "headings": [],
            "notice_texts": [],
            "raw_text": html,
        }

    soup = BeautifulSoup(html, "lxml")

    # Kill scripts/styles/nav junk that adds noise
    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()

    title = (soup.title.string or "").strip() if soup.title else ""

    headings = [
        strip_noise(h.get_text(" ", strip=True))
        for h in soup.find_all(["h1", "h2", "h3"])
        if h.get_text(strip=True)
    ][:20]

    # Find notice-like containers and pull their text
    notice_texts: list[str] = []
    for tag in soup.find_all(["div", "section", "ul", "table", "marquee"]):
        if _looks_like_notice_container(tag):
            txt = strip_noise(tag.get_text(" ", strip=True))
            if txt and len(txt) > 20:
                notice_texts.append(txt[:2000])
            if len(notice_texts) >= 10:
                break

    # All links → separate PDF and notice-ish links
    pdf_links: list[str] = []
    notice_links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"].strip())
        label = a.get_text(" ", strip=True).lower()
        if href.lower().endswith(".pdf") or "pdf" in href.lower():
            pdf_links.append(href)
        elif any(k in label for k in NOTICE_HINT_KEYWORDS) or any(
            k in href.lower() for k in NOTICE_HINT_KEYWORDS
        ):
            notice_links.append(href)

    # Dedup while preserving order
    def _dedup(items: list[str]) -> list[str]:
        seen = set()
        out = []
        for x in items:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return {
        "title": title,
        "headings": headings,
        "notice_texts": notice_texts,
        "notice_links": _dedup(notice_links)[:100],
        "pdf_links": _dedup(pdf_links)[:100],
        "raw_text": strip_noise(soup.get_text(" ", strip=True))[:20000],
    }
