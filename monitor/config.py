"""Central config: env vars + keyword lists that drive smart filtering."""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
DB_PATH = DATA_DIR / "history.db"
DASHBOARD_PATH = DATA_DIR / "dashboard.html"
WEBSITES_CSV = ROOT / "websites.csv"

SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

# ---- Credentials ----
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_TO = os.getenv("EMAIL_TO", "")

# ---- Tuning ----
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))
CONCURRENCY = int(os.getenv("CONCURRENCY", "15"))
DIGEST_HOUR_UTC = int(os.getenv("DIGEST_HOUR_UTC", "3"))
MAX_RETRIES = 3

# ---- Keyword filter: only these terms trigger real alerts ----
# Case-insensitive substring match. Anything else is logged but not alerted.
ALERT_KEYWORDS = [
    "registration", "register", "counselling", "counseling",
    "choice filling", "choice locking", "seat matrix", "seat allotment",
    "round 1", "round 2", "round 3", "round-1", "round-2", "round-3",
    "mop-up", "mop up", "stray vacancy", "stray",
    "result", "merit list", "rank list", "allotment",
    "schedule", "notice", "notification", "circular",
    "admit card", "answer key", "cutoff", "cut-off", "cut off",
    "important", "urgent", "extended", "postponed", "revised",
    "neet", "nta", "mcc", "aaccc", "nmc", "nbe",
    "pg", "ug", "mds", "bds", "mbbs", "ayush",
    "fee", "documents", "verification", "reporting",
]

# Noise patterns stripped before hashing — dates, view counters, etc.
NOISE_PATTERNS = [
    r"\b(?:last updated|updated on|last modified|visitors?|hits?|views?)\b[:\s]*.*?(?=\n|$)",
    r"\b\d{1,2}[:/-]\d{1,2}[:/-]\d{2,4}\b(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?",
    r"©\s*\d{4}.*?(?=\n|$)",
    r"page views?[:\s]*\d+",
    r"total visitors?[:\s]*\d+",
]

# Sites that require JS rendering — skipped in v1 with a note in dashboard
# (identifier = URL substring match)
JS_HEAVY_HINTS = ["admissions.nic.in", "online-counselling.co.in", "mponline.gov.in"]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
