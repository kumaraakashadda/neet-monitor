"""Async HTTP fetch with retries + timeout. Returns text or raises."""
from __future__ import annotations

import asyncio
import httpx

from monitor.config import REQUEST_TIMEOUT, MAX_RETRIES, USER_AGENT


class FetchError(Exception):
    pass


async def fetch(url: str) -> tuple[str, str]:
    """Fetch a URL; return (final_url, text_body).

    Retries on network errors up to MAX_RETRIES with backoff.
    Raises FetchError with a short reason on final failure.
    """
    last_err: str = ""
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,*/*"}
    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
        headers=headers,
        verify=False,  # many gov sites have stale certs
    ) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                r = await client.get(url)
                r.raise_for_status()
                # Detect binary/PDF; we only care about HTML here
                ctype = r.headers.get("content-type", "").lower()
                if "pdf" in ctype:
                    return str(r.url), f"[PDF DOCUMENT] {r.url}"
                return str(r.url), r.text
            except httpx.HTTPStatusError as e:
                last_err = f"HTTP {e.response.status_code}"
                # 4xx: don't retry, waste of time
                if 400 <= e.response.status_code < 500:
                    break
            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                last_err = f"connect: {type(e).__name__}"
            except httpx.ReadTimeout:
                last_err = "read timeout"
            except httpx.RemoteProtocolError as e:
                last_err = f"protocol: {e}"
            except Exception as e:  # last-resort catch, keep run going
                last_err = f"{type(e).__name__}: {str(e)[:120]}"
            if attempt < MAX_RETRIES:
                await asyncio.sleep(1.5 * attempt)
    raise FetchError(last_err or "unknown")
