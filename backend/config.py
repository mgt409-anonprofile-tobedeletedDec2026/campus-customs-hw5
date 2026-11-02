"""Settings for the Campus Customs agent team. The model name lives here only."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
ROOT = BACKEND_DIR.parent
load_dotenv(ROOT / ".env")

# The only model allowed in this homework. OPENAI_MODEL in .env must match it.
REQUIRED_MODEL = "gpt-6-luna"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", REQUIRED_MODEL).strip()
if OPENAI_MODEL != REQUIRED_MODEL:
    raise RuntimeError(
        f"OPENAI_MODEL is {OPENAI_MODEL!r}, but this project may only use {REQUIRED_MODEL!r}."
    )

PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
HUMAN_APPROVER = os.getenv("HUMAN_APPROVER", "David Wallace")

PROMPTS_DIR = BACKEND_DIR / "prompts"
MCP_SERVER_FILE = ROOT / "mcp_server" / "server.py"
ORIGINAL_DB = ROOT / "data" / "campus_customs.db"
WORKING_DB = ROOT / "data" / "campus_customs_new.db"
AUDIT_PATH = ROOT / "output" / "audit_trail.json"

# Token guardrails (see output/harness.md, Safety section).
MAX_MODEL_REQUESTS_PER_TICKET = 40    # every agent on one ticket shares this budget
MAX_MODEL_REQUESTS_PER_AGENT_RUN = 8  # one agent's turn, including its tool calls
MAX_TOKENS_PER_TICKET = 200_000
MAX_DELEGATION_DEPTH = 3              # Boss -> A -> B -> C, no deeper
MAX_CALLS_PER_PAIR = 2                # e.g. Boss may ask Inventory at most twice per ticket
AUDIT_TEXT_LIMIT = 4000               # long tool outputs are trimmed in the audit file


def portkey_api_key() -> str:
    key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is missing. Add it to hw5/.env (never commit it).")
    return key
