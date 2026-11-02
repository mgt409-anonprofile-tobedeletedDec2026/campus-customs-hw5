"""Campus Customs backend: FastAPI routes for the React dashboard.

Start from the backend/ folder:
    uvicorn main:app --reload --port 8000

* Every shop fact and every change goes through the campus-customs MCP server.
* Only David Wallace, logged in, can approve or decline payments or reset the
  database. These routes are the only callers of the human_* MCP tools; the
  agents can never reach them.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import Client

import agents
import audit
import auth
from config import AUDIT_PATH, HUMAN_APPROVER, OPENAI_MODEL
from models import AGENT_TITLES, DecisionBody, LoginBody

app = FastAPI(title="Campus Customs Multi-Agent Operations", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# One agent run at a time keeps the board, the cash and the audit trail simple.
_run: dict[str, Any] = {"task": None, "ticket_id": None, "run_id": None, "started_utc": None, "result": None}


async def mcp(tool: str, **args: Any) -> Any:
    """Call one tool on the campus-customs MCP server."""
    async with Client(agents.MCP_SERVER) as client:
        result = await client.call_tool(tool, args)
    return result.structured_content if result.data is None else result.data


def _require_david(authorization: str | None) -> str:
    token = authorization.removeprefix("Bearer ").strip() if authorization else None
    try:
        return auth.check_session(token)
    except auth.LoginError as exc:
        raise HTTPException(exc.status, exc.message) from None


def _run_busy() -> bool:
    return _run["task"] is not None and not _run["task"].done()


# ---------------------------------------------------------------- tickets


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "model": OPENAI_MODEL, "human_approver": HUMAN_APPROVER}


@app.get("/api/tickets")
async def list_tickets() -> dict:
    """All tickets: open or resolved, plus the detailed status and latest update."""
    board = await mcp("get_ticket_board", status="all")
    for t in board["tickets"]:
        t["state"] = "resolved" if t["status"] == "resolved" else "open"
        t["awaiting_david"] = [r for r in t["payment_requests"] if r["status"] == "pending"]
    return board


@app.get("/api/tickets/{ticket_id}")
async def ticket_detail(ticket_id: int) -> dict:
    """One ticket with its linked rows, updates, drafts and payment requests."""
    detail = await mcp("get_ticket", ticket_id=ticket_id)
    if not detail.get("found"):
        raise HTTPException(404, detail.get("message", "Ticket not found."))
    return detail


@app.post("/api/tickets/{ticket_id}/run", status_code=202)
async def run_ticket(ticket_id: int) -> dict:
    """Start Michael and the team on a ticket in the background; returns at once."""
    if not (await mcp("get_ticket", ticket_id=ticket_id)).get("found"):
        raise HTTPException(404, f"No ticket with id {ticket_id}.")
    if _run_busy():
        raise HTTPException(409, f"The team is already working ticket #{_run['ticket_id']}. Try again when it's done.")
    run_id = agents.new_run_id()

    async def work() -> None:
        result = await agents.run_ticket(ticket_id, run_id=run_id)
        _run["result"] = result.model_dump()
        if result.error is None and result.report is not None:
            await _mark_resolved(ticket_id, run_id)

    _run.update(ticket_id=ticket_id, run_id=run_id, result=None,
                started_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                task=asyncio.create_task(work()))
    return {"started": True, "ticket_id": ticket_id, "run_id": run_id,
            "poll": f"/api/events?run_id={run_id}"}


async def _mark_resolved(ticket_id: int, run_id: str) -> None:
    """When the team's run finishes, the ticket is resolved for the team. Any
    payment still waiting is shown separately as "awaiting David"."""
    pending = [r for r in (await mcp("list_payment_requests", status="pending"))["requests"]
               if r["ticket_id"] == ticket_id]
    note = "Team run finished; the agents' work on this ticket is done."
    if pending:
        ids = ", ".join(f"#{r['id']} (${r['amount']:,.2f})" for r in pending)
        note += f" Awaiting David Wallace on payment request {ids}."
    result = await mcp("update_ticket_status", ticket_id=ticket_id, new_status="resolved", agent="boss", note=note)
    audit.record(run_id, ticket_id, None, "ticket_resolved", note=note, result=result)


@app.get("/api/runs/current")
async def current_run() -> dict:
    """Whether the team is working right now, and the last run's result."""
    return {"running": _run_busy(), "ticket_id": _run["ticket_id"], "run_id": _run["run_id"],
            "started_utc": _run["started_utc"], "result": _run["result"]}


# ---------------------------------------------------------------- events


def _event_view(index: int, e: dict) -> dict:
    """Turn one audit entry into a dashboard-friendly event."""
    agent = e.get("agent")
    view = {
        "index": index, "time_utc": e.get("time_utc"), "run_id": e.get("run_id"),
        "ticket_id": e.get("ticket_id"), "agent": agent,
        "character": AGENT_TITLES.get(agent, agent or "System"), "event": e.get("event"),
    }
    ev = e.get("event")
    if ev == "model_text":
        view["said"] = e.get("text")
    elif ev == "agent_end":
        report = e.get("report") or {}
        view["said"] = report.get("summary")
        view["needs_human"] = report.get("needs_human")
        view["human_action"] = report.get("human_action")
    elif ev in ("tool_call", "tool_result", "tool_retry"):
        view["tool"] = e.get("tool")
        view["detail"] = e.get("args") if ev == "tool_call" else e.get("output", e.get("detail"))
    elif ev == "delegation":
        view["to"] = e.get("to")
        view["said"] = e.get("request")
    elif ev == "delegation_result":
        view["from_agent"] = e.get("from_agent")
        view["said"] = (e.get("report") or {}).get("summary")
    else:
        view["detail"] = {k: v for k, v in e.items()
                          if k not in ("time_utc", "run_id", "ticket_id", "agent", "event")}
    return view


@app.get("/api/events")
async def events(after: int = -1, ticket_id: int | None = None, run_id: str | None = None,
                 limit: int = 200, since_reset: bool = False) -> dict:
    """Recent agent events from output/audit_trail.json. Poll with after=<last index>.
    since_reset=true skips everything before the last database reset."""
    entries = json.loads(AUDIT_PATH.read_text(encoding="utf-8")) if AUDIT_PATH.exists() else []
    if since_reset:
        last_reset = max((i for i, e in enumerate(entries) if e.get("event") == "database_reset"), default=-1)
        after = max(after, last_reset)
    picked = [
        _event_view(i, e) for i, e in enumerate(entries)
        if i > after
        and (ticket_id is None or e.get("ticket_id") == ticket_id)
        and (run_id is None or e.get("run_id") == run_id)
    ]
    return {"total": len(entries), "running": _run_busy(), "events": picked[-limit:]}


# ---------------------------------------------------------------- money


@app.get("/api/cash")
async def cash() -> dict:
    """The current checking balance from cash_accounts, plus open bills and pending requests."""
    position = await mcp("get_cash_position")
    checking = next((a for a in position["cash"]["accounts"] if a["name"] == "checking"), None)
    return {"checking_balance": checking["balance"] if checking else None,
            "as_of": checking["date"] if checking else None, "position": position}


@app.get("/api/payment-requests")
async def payment_requests(status: str = "pending") -> dict:
    """Payment requests waiting for David Wallace (or paid/declined/all). Each
    pending one carries Oscar's priority check (rent protection) as `risk`."""
    result = await mcp("list_payment_requests", status=status)
    for r in result["requests"]:
        if r["status"] == "pending":
            r["risk"] = await mcp("assess_payment_request", request_id=r["id"])
    return result


@app.post("/api/login")
async def login(body: LoginBody, request: Request) -> dict:
    """David Wallace logs in with the approver password."""
    client = request.client.host if request.client else "unknown"
    try:
        result = auth.login(body.password, client)
    except auth.LoginError as exc:
        audit.record("human", None, None, "human_login_failed", reason=exc.message)
        raise HTTPException(exc.status, exc.message) from None
    audit.record("human", None, None, "human_login", approver=HUMAN_APPROVER)
    return result


@app.post("/api/logout")
async def logout(authorization: str | None = Header(default=None)) -> dict:
    auth.logout(authorization.removeprefix("Bearer ").strip() if authorization else None)
    return {"logged_out": True}


@app.get("/api/session")
async def session(authorization: str | None = Header(default=None)) -> dict:
    """Is the caller logged in as David Wallace? (Also says if no password is set yet.)"""
    try:
        return {"logged_in": True, "approver": _require_david(authorization)}
    except HTTPException as exc:
        return {"logged_in": False, "message": exc.detail, "password_set": auth.stored_hash() is not None}


@app.post("/api/payment-requests/{request_id}/approve")
async def approve(request_id: int, body: DecisionBody,
                  authorization: str | None = Header(default=None)) -> dict:
    """David Wallace approves a request. The ONLY route that moves cash; it still
    refuses (with Oscar's reason) anything that would make cash negative, and it
    stops on Oscar's rent-protection warning unless acknowledge_risk is true."""
    approver = _require_david(authorization)
    result = await mcp("human_approve_and_pay", request_id=request_id, approver=approver, note=body.reason,
                       acknowledge_risk=body.acknowledge_risk)
    audit.record("human", None, None, "human_decision", decision="approve", request_id=request_id,
                 approver=approver, reason=body.reason, acknowledged_priority_warning=body.acknowledge_risk,
                 result=result)
    if not result.get("paid"):
        raise HTTPException(409, result.get("reason", "Payment refused."))
    return result


@app.post("/api/payment-requests/{request_id}/decline")
async def decline(request_id: int, body: DecisionBody,
                  authorization: str | None = Header(default=None)) -> dict:
    """David Wallace declines a request, with his reason. No money moves."""
    approver = _require_david(authorization)
    result = await mcp("human_decline_payment", request_id=request_id, approver=approver, reason=body.reason)
    audit.record("human", None, None, "human_decision", decision="decline", request_id=request_id,
                 approver=approver, reason=body.reason, result=result)
    if not result.get("declined"):
        raise HTTPException(409, result.get("reason", "Could not decline."))
    return result


# ---------------------------------------------------------------- reset


@app.post("/api/reset")
async def reset(authorization: str | None = Header(default=None)) -> dict:
    """David Wallace resets the working database to the original values.
    The audit trail is kept (it is append-only)."""
    approver = _require_david(authorization)
    if _run_busy():
        raise HTTPException(409, "Wait for the current agent run to finish before resetting.")
    result = await mcp("human_reset_working_database", confirm=True)
    audit.record("human", None, None, "database_reset", approver=approver, result=result)
    _run.update(task=None, ticket_id=None, run_id=None, started_utc=None, result=None)
    return result
