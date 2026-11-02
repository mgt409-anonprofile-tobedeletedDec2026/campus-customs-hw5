"""Campus Customs MCP server: the shared toolbox for every agent.

Reads the working copy of the shop database (data/campus_customs_new.db).
The original data/campus_customs.db is the reset button and is never opened.

Three kinds of tools (see ../RULES.md):
  * Read tools open the database read-only.
  * Agent write tools only touch the board: ticket status, draft messages, and
    payment *requests*. None of them moves cash.
  * Human-only tools (prefixed human_) are the only way money leaves. They need
    the named human approver and refuse any payment that would make cash
    negative. The backend never gives these tools to an agent.

Manual test:  python server.py
"""

from __future__ import annotations

import os
import shutil
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP

HERE = Path(__file__).resolve().parent

# The one place the database path is set. Override with CAMPUS_CUSTOMS_DB.
DB_PATH = Path(
    os.environ.get("CAMPUS_CUSTOMS_DB", HERE.parent / "data" / "campus_customs_new.db")
).resolve()
ORIGINAL_DB_NAME = "campus_customs.db"

mcp = FastMCP("campus-customs")

HUMAN_APPROVAL_NOTE = (
    "Agents cannot pay or place orders. Any payment needs a human's approval "
    "on the dashboard."
)


def _connect(write: bool = False) -> sqlite3.Connection:
    """Open the working database (read-only unless write=True). Refuses the original."""
    if DB_PATH.name == ORIGINAL_DB_NAME:
        raise RuntimeError(
            f"Refusing to open {ORIGINAL_DB_NAME}: it is the reset copy. "
            "Point CAMPUS_CUSTOMS_DB at campus_customs_new.db."
        )
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    mode = "rw" if write else "ro"
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode={mode}", uri=True)
    conn.row_factory = sqlite3.Row
    if write:
        _ensure_board_tables(conn)
    return conn


# Board tables the agents write to. They are not in the original database, so
# a reset (copying the original over the working file) clears them too.
BOARD_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS ticket_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    agent TEXT NOT NULL,
    old_status TEXT NOT NULL,
    new_status TEXT NOT NULL,
    note TEXT NOT NULL,
    shop_date TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    author_agent TEXT NOT NULL,
    recipient_role TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    shop_date TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS payment_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id),
    kind TEXT NOT NULL,
    ref_id INTEGER,
    vendor_id INTEGER,
    sku TEXT,
    size TEXT,
    qty INTEGER,
    amount REAL NOT NULL,
    requested_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    shop_date TEXT NOT NULL,
    decided_by TEXT,
    decision_note TEXT
);
"""

AGENT_NAMES = ("boss", "inventory", "accounting", "facilities", "customer_service")
AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]
TicketStatus = Literal["open", "in_progress", "waiting_on_human", "blocked", "resolved"]
HUMAN_APPROVER = os.environ.get("HUMAN_APPROVER", "David Wallace")


def _ensure_board_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(BOARD_TABLES_SQL)


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _rows(conn: sqlite3.Connection, table: str, sql: str, params: tuple = ()) -> list[dict]:
    """Rows from a board table, or [] if no agent has written to it yet."""
    if not _table_exists(conn, table):
        return []
    return [dict(r) for r in conn.execute(sql, params)]


def _public_ticket(row: sqlite3.Row) -> dict:
    """A ticket with the customer's personal name withheld (confidentiality)."""
    t = dict(row)
    if t["type"] == "customer_order":
        t["requester"] = "(customer name withheld for privacy)"
    return t


def _today(conn: sqlite3.Connection) -> date:
    """The shop's "today" comes from desk.date_today, never the computer clock."""
    row = conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()
    if row is None:
        raise RuntimeError("desk.date_today is missing from the database.")
    return date.fromisoformat(row["date_today"])


def _cash(conn: sqlite3.Connection) -> dict:
    accounts = [dict(r) for r in conn.execute("SELECT name, balance, date FROM cash_accounts")]
    return {"accounts": accounts, "total_balance": sum(a["balance"] for a in accounts)}


def _open_invoices(conn: sqlite3.Connection, today: date, vendor_id: int | None = None) -> list[dict]:
    sql = (
        "SELECT i.id, i.vendor_id, v.name AS vendor_name, i.amount, i.due_date, "
        "i.status, i.description FROM invoices i LEFT JOIN vendors v ON v.id = i.vendor_id "
        "WHERE i.status = 'open'"
    )
    params: tuple = ()
    if vendor_id is not None:
        sql += " AND i.vendor_id = ?"
        params = (vendor_id,)
    invoices = []
    for r in conn.execute(sql + " ORDER BY i.due_date", params):
        inv = dict(r)
        days = (today - date.fromisoformat(inv["due_date"])).days
        inv["days_overdue"] = max(days, 0)
        inv["overdue"] = days > 0
        invoices.append(inv)
    return invoices


def _vendor_options(conn: sqlite3.Connection, sku: str, today: date) -> dict:
    """Every vendor, with lead time, arrival date and whether an unpaid invoice blocks it.

    The database has no direct SKU-to-vendor link, so we return each vendor's
    specialty and flag vendors whose past invoices mention this SKU. The agent
    chooses by specialty; this tool does not guess.
    """
    vendors = []
    for v in conn.execute("SELECT id, name, specialty, lead_days FROM vendors ORDER BY id"):
        v = dict(v)
        blocking = _open_invoices(conn, today, v["id"])
        history = conn.execute(
            "SELECT id FROM invoices WHERE vendor_id = ? AND description LIKE ?",
            (v["id"], f"%{sku}%"),
        ).fetchall()
        v["earliest_arrival_if_ordered_today"] = date.fromordinal(
            today.toordinal() + v["lead_days"]
        ).isoformat()
        v["has_supplied_this_sku_before"] = bool(history)
        v["blocked"] = bool(blocking)
        v["blocking_invoices"] = blocking
        if blocking:
            total = sum(i["amount"] for i in blocking)
            ids = ", ".join(f"#{i['id']}" for i in blocking)
            v["unblock_step"] = (
                f"{v['name']} will not ship until invoice {ids} (${total:,.2f}) is paid. "
                "Flag this for a human to approve the payment. Do not pay it yourself."
            )
        vendors.append(v)
    return {
        "note": "No direct SKU-to-vendor link exists in the database. Pick the vendor by specialty.",
        "vendors": vendors,
    }


@mcp.tool
def check_stock_and_restock(sku: str, size: str, qty_needed: int = 1) -> dict:
    """Ticket 101 tool. Check stock for one product AND size, and if it is short,
    show which vendors could restock it, their lead time and arrival date, and
    whether an open unpaid invoice blocks them from shipping.

    Read-only. Never pays an invoice or places an order.
    """
    with _connect() as conn:
        today = _today(conn)
        item = conn.execute(
            "SELECT sku, name, size, qty, location FROM inventory WHERE sku = ? AND size = ?",
            (sku, size),
        ).fetchone()
        if item is None:
            sizes = [r["size"] for r in conn.execute("SELECT size FROM inventory WHERE sku = ?", (sku,))]
            return {
                "found": False,
                "message": (
                    f"No inventory row for SKU {sku!r} in size {size!r}. "
                    + (f"Sizes on file for this SKU: {sizes}." if sizes else "This SKU is not in inventory.")
                ),
            }
        item = dict(item)
        shortfall = max(qty_needed - item["qty"], 0)
        result = {
            "found": True,
            "today": today.isoformat(),
            "item": item,
            "qty_needed": qty_needed,
            "in_stock_enough": shortfall == 0,
            "shortfall": shortfall,
        }
        if shortfall:
            result["restock"] = _vendor_options(conn, sku, today)
            result["approval_note"] = HUMAN_APPROVAL_NOTE
        return result


@mcp.tool
def check_rent_due(lease_id: int) -> dict:
    """Ticket 102 tool. Look up a lease's rent and next due date, compare it with
    "today" (desk.date_today) and the cash balance, and show whether paying it
    would keep cash at or above zero. Also lists other open bills competing for
    the same cash.

    Read-only. Never pays rent. Paying needs a human's approval.
    """
    with _connect() as conn:
        today = _today(conn)
        lease = conn.execute(
            "SELECT id, space_name, landlord, monthly_rent, next_due, notes FROM leases WHERE id = ?",
            (lease_id,),
        ).fetchone()
        if lease is None:
            return {"found": False, "message": f"No lease with id {lease_id}."}
        lease = dict(lease)
        cash = _cash(conn)
        other_bills = _open_invoices(conn, today)
        days_until_due = (date.fromisoformat(lease["next_due"]) - today).days
        balance_after = cash["total_balance"] - lease["monthly_rent"]
        other_total = sum(i["amount"] for i in other_bills)
        return {
            "found": True,
            "today": today.isoformat(),
            "lease": lease,
            "days_until_due": days_until_due,
            "overdue": days_until_due < 0,
            "cash": cash,
            "balance_after_rent": balance_after,
            "cash_covers_rent": balance_after >= 0,
            "other_open_bills": other_bills,
            "balance_after_rent_and_open_bills": balance_after - other_total,
            "approval_note": HUMAN_APPROVAL_NOTE,
        }


@mcp.tool
def check_bulk_order_pricing(
    sku: str, size: str, qty_requested: int, discount_percent: float = 0.0
) -> dict:
    """Ticket 103 tool. For a bulk request, compare stock with the quantity
    requested and show unit cost, list price and margin. If a discount is given,
    show the discounted price and margin, and flag it if it goes below cost.
    Also shows the restock cost for any shortfall against the cash balance and
    whether the restocking vendor is blocked by an unpaid invoice.

    Read-only. Never sets a price, orders stock, or pays anything.
    """
    if not 0 <= discount_percent <= 100:
        return {"found": False, "message": "discount_percent must be between 0 and 100."}
    with _connect() as conn:
        today = _today(conn)
        item = conn.execute(
            "SELECT sku, name, size, qty FROM inventory WHERE sku = ? AND size = ?",
            (sku, size),
        ).fetchone()
        price = conn.execute(
            "SELECT unit_cost, list_price FROM pricing WHERE sku = ?", (sku,)
        ).fetchone()
        if item is None or price is None:
            missing = "inventory row" if item is None else "pricing row"
            return {"found": False, "message": f"No {missing} for SKU {sku!r} size {size!r}."}

        item, price = dict(item), dict(price)
        cost, list_price = price["unit_cost"], price["list_price"]
        shortfall = max(qty_requested - item["qty"], 0)
        discounted = round(list_price * (1 - discount_percent / 100), 2)
        margin = round(discounted - cost, 2)
        cash = _cash(conn)
        restock_cost = round(shortfall * cost, 2)
        bills = _open_invoices(conn, today)
        rent_due = [
            dict(r)
            for r in conn.execute(
                "SELECT id, space_name, monthly_rent, next_due FROM leases WHERE next_due <= ?",
                (date.fromordinal(today.toordinal() + 30).isoformat(),),
            )
        ]
        committed = sum(b["amount"] for b in bills) + sum(r["monthly_rent"] for r in rent_due)
        cash_after_all = round(cash["total_balance"] - committed - restock_cost, 2)

        result = {
            "found": True,
            "today": today.isoformat(),
            "item": item,
            "qty_requested": qty_requested,
            "shortfall": shortfall,
            "unit_cost": cost,
            "list_price": list_price,
            "list_margin_per_unit": round(list_price - cost, 2),
            "list_margin_percent": round((list_price - cost) / list_price * 100, 1),
            "max_discount_percent_before_loss": round((list_price - cost) / list_price * 100, 1),
            "discount_percent": discount_percent,
            "discounted_unit_price": discounted,
            "discounted_margin_per_unit": margin,
            "discounted_margin_percent": round(margin / discounted * 100, 1) if discounted else None,
            "below_cost": discounted < cost,
            "order_total_at_discount": round(discounted * qty_requested, 2),
            "order_profit_at_discount": round(margin * qty_requested, 2),
            "restock_cost_for_shortfall": restock_cost,
            "cash": cash,
            "cash_covers_restock_alone": cash["total_balance"] - restock_cost >= 0,
            "other_open_bills": bills,
            "rent_due_within_30_days": rent_due,
            "cash_after_bills_rent_and_restock": cash_after_all,
            "cash_covers_everything": cash_after_all >= 0,
            "approval_note": HUMAN_APPROVAL_NOTE,
        }
        if shortfall:
            result["restock"] = _vendor_options(conn, sku, today)
        return result


# ---------------------------------------------------------------------------
# Read tools added in Problem 5
# ---------------------------------------------------------------------------


@mcp.tool
def get_ticket_board(status: str = "open") -> dict:
    """List tickets on the board (default: open ones; use "all" for every ticket),
    each with its latest status update, number of drafts, and payment requests.
    Customer names are withheld. Read-only.
    """
    with closing(_connect()) as conn:
        today = _today(conn)
        sql = "SELECT * FROM tickets"
        params: tuple = ()
        if status != "all":
            sql += " WHERE status = ?"
            params = (status,)
        tickets = []
        for row in conn.execute(sql + " ORDER BY id", params):
            t = _public_ticket(row)
            t["latest_update"] = next(iter(_rows(
                conn, "ticket_updates",
                "SELECT agent, new_status, note, shop_date FROM ticket_updates "
                "WHERE ticket_id = ? ORDER BY id DESC LIMIT 1", (t["id"],))), None)
            t["draft_count"] = len(_rows(
                conn, "drafts", "SELECT id FROM drafts WHERE ticket_id = ?", (t["id"],)))
            t["payment_requests"] = _rows(
                conn, "payment_requests",
                "SELECT id, kind, amount, status FROM payment_requests WHERE ticket_id = ?",
                (t["id"],))
            tickets.append(t)
        return {"today": today.isoformat(), "filter": status, "tickets": tickets}


@mcp.tool
def get_ticket(ticket_id: int) -> dict:
    """Full detail for one ticket: the ticket (customer name withheld), its linked
    inventory/pricing rows, linked invoice and vendor, linked lease, plus every
    status update, draft, and payment request so far. Read-only.
    """
    with closing(_connect()) as conn:
        today = _today(conn)
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row is None:
            return {"found": False, "message": f"No ticket with id {ticket_id}."}
        t = _public_ticket(row)
        linked: dict = {}
        if t["sku"]:
            inv = conn.execute(
                "SELECT * FROM inventory WHERE sku = ? AND size = ?", (t["sku"], t["size"])
            ).fetchone()
            linked["inventory"] = dict(inv) if inv else None
            price = conn.execute("SELECT * FROM pricing WHERE sku = ?", (t["sku"],)).fetchone()
            linked["pricing"] = dict(price) if price else None
        if t["invoice_id"]:
            inv = conn.execute("SELECT * FROM invoices WHERE id = ?", (t["invoice_id"],)).fetchone()
            linked["invoice"] = dict(inv) if inv else None
            if inv:
                v = conn.execute("SELECT * FROM vendors WHERE id = ?", (inv["vendor_id"],)).fetchone()
                linked["invoice_vendor"] = dict(v) if v else None
        if t["lease_id"]:
            lease = conn.execute("SELECT * FROM leases WHERE id = ?", (t["lease_id"],)).fetchone()
            linked["lease"] = dict(lease) if lease else None
        return {
            "found": True,
            "today": today.isoformat(),
            "ticket": t,
            "linked": linked,
            "updates": _rows(conn, "ticket_updates",
                             "SELECT * FROM ticket_updates WHERE ticket_id = ? ORDER BY id", (ticket_id,)),
            "drafts": _rows(conn, "drafts",
                            "SELECT * FROM drafts WHERE ticket_id = ? ORDER BY id", (ticket_id,)),
            "payment_requests": _rows(conn, "payment_requests",
                                      "SELECT * FROM payment_requests WHERE ticket_id = ? ORDER BY id",
                                      (ticket_id,)),
        }


@mcp.tool
def get_cash_position() -> dict:
    """Accounting's view of the money: cash balance, every open invoice (with
    days overdue), rent due in the next 30 days, pending payment requests, and
    what cash would be left if all of them were paid. Read-only.
    """
    with closing(_connect()) as conn:
        today = _today(conn)
        cash = _cash(conn)
        bills = _open_invoices(conn, today)
        horizon = date.fromordinal(today.toordinal() + 30).isoformat()
        rent = [dict(r) for r in conn.execute(
            "SELECT id, space_name, monthly_rent, next_due FROM leases WHERE next_due <= ?", (horizon,))]
        pending = _rows(conn, "payment_requests",
                        "SELECT id, ticket_id, kind, ref_id, amount, requested_by FROM payment_requests "
                        "WHERE status = 'pending' ORDER BY id")
        pending_total = sum(p["amount"] for p in pending)
        obligations = sum(b["amount"] for b in bills) + sum(r["monthly_rent"] for r in rent)
        return {
            "today": today.isoformat(),
            "cash": cash,
            "open_invoices": bills,
            "rent_due_within_30_days": rent,
            "pending_payment_requests": pending,
            "pending_requests_total": pending_total,
            "cash_after_pending_requests": cash["total_balance"] - pending_total,
            "cash_after_open_invoices_and_rent": cash["total_balance"] - obligations,
            "note": "Cash only goes out in this shop. No tool can add money.",
        }


@mcp.tool
def list_payment_requests(status: str = "pending") -> dict:
    """Payment requests waiting for (or decided by) the human approver.
    status: "pending", "paid", "declined", or "all". Read-only.
    """
    with closing(_connect()) as conn:
        sql = "SELECT * FROM payment_requests"
        params: tuple = ()
        if status != "all":
            sql += " WHERE status = ?"
            params = (status,)
        return {"status": status, "requests": _rows(conn, "payment_requests", sql + " ORDER BY id", params)}


@mcp.tool
def list_drafts(ticket_id: int | None = None) -> dict:
    """Draft messages saved on the board (optionally for one ticket). Drafts are
    never sent anywhere. Read-only.
    """
    with closing(_connect()) as conn:
        if ticket_id is None:
            drafts = _rows(conn, "drafts", "SELECT * FROM drafts ORDER BY id")
        else:
            drafts = _rows(conn, "drafts", "SELECT * FROM drafts WHERE ticket_id = ? ORDER BY id", (ticket_id,))
        return {"drafts": drafts}


# ---------------------------------------------------------------------------
# Agent write tools: board only, never cash
# ---------------------------------------------------------------------------


@mcp.tool
def update_ticket_status(ticket_id: int, new_status: TicketStatus, agent: AgentName, note: str) -> dict:
    """Move a ticket to a new status and record who did it and why.
    Statuses: open, in_progress, waiting_on_human, blocked, resolved.
    Does not move money or stock.
    """
    if not note.strip():
        return {"ok": False, "message": "A note explaining the status change is required."}
    with closing(_connect(write=True)) as conn, conn:
        today = _today(conn)
        row = conn.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        if row is None:
            return {"ok": False, "message": f"No ticket with id {ticket_id}."}
        conn.execute("UPDATE tickets SET status = ? WHERE id = ?", (new_status, ticket_id))
        conn.execute(
            "INSERT INTO ticket_updates (ticket_id, agent, old_status, new_status, note, shop_date) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ticket_id, agent, row["status"], new_status, note.strip(), today.isoformat()),
        )
        return {"ok": True, "ticket_id": ticket_id, "old_status": row["status"], "new_status": new_status}


@mcp.tool
def save_draft_message(
    ticket_id: int,
    author_agent: AgentName,
    recipient_role: Literal["customer", "landlord", "vendor", "internal"],
    subject: str,
    body: str,
) -> dict:
    """Save a DRAFT message on the board for a ticket. Drafts are never emailed
    or sent to anyone; a human reads them on the dashboard.
    """
    if not subject.strip() or not body.strip():
        return {"ok": False, "message": "A draft needs a subject and a body."}
    with closing(_connect(write=True)) as conn, conn:
        today = _today(conn)
        if conn.execute("SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)).fetchone() is None:
            return {"ok": False, "message": f"No ticket with id {ticket_id}."}
        cur = conn.execute(
            "INSERT INTO drafts (ticket_id, author_agent, recipient_role, subject, body, shop_date) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (ticket_id, author_agent, recipient_role, subject.strip(), body.strip(), today.isoformat()),
        )
        return {"ok": True, "draft_id": cur.lastrowid, "status": "draft",
                "note": "Saved on the board only. Nothing was sent."}


@mcp.tool
def request_payment_approval(
    ticket_id: int,
    kind: Literal["invoice", "rent", "purchase_order"],
    requested_by: AgentName,
    reason: str,
    ref_id: int | None = None,
    vendor_id: int | None = None,
    sku: str | None = None,
    size: str | None = None,
    qty: int | None = None,
) -> dict:
    """Ask the human approver to consider a payment. This does NOT pay anything.

    kind="invoice": ref_id = invoices.id      (amount taken from the invoice)
    kind="rent":    ref_id = leases.id        (amount = monthly_rent)
    kind="purchase_order": vendor_id, sku, size, qty (amount = qty x unit_cost)

    The amount always comes from the database, never from the agent. Returns the
    request plus what cash would be left, so the human can see the impact.
    """
    with closing(_connect(write=True)) as conn, conn:
        today = _today(conn)
        if conn.execute("SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)).fetchone() is None:
            return {"ok": False, "message": f"No ticket with id {ticket_id}."}
        warnings: list[str] = []
        if kind == "invoice":
            inv = conn.execute("SELECT * FROM invoices WHERE id = ?", (ref_id,)).fetchone()
            if inv is None:
                return {"ok": False, "message": f"No invoice with id {ref_id}."}
            if inv["status"] != "open":
                return {"ok": False, "message": f"Invoice #{ref_id} is already {inv['status']}."}
            amount, vendor_id = inv["amount"], inv["vendor_id"]
        elif kind == "rent":
            lease = conn.execute("SELECT * FROM leases WHERE id = ?", (ref_id,)).fetchone()
            if lease is None:
                return {"ok": False, "message": f"No lease with id {ref_id}."}
            amount = lease["monthly_rent"]
        else:
            if not (vendor_id and sku and size and qty and qty > 0):
                return {"ok": False, "message": "A purchase order needs vendor_id, sku, size and qty > 0."}
            if conn.execute("SELECT 1 FROM vendors WHERE id = ?", (vendor_id,)).fetchone() is None:
                return {"ok": False, "message": f"No vendor with id {vendor_id}."}
            if conn.execute("SELECT 1 FROM inventory WHERE sku = ? AND size = ?", (sku, size)).fetchone() is None:
                return {"ok": False, "message": f"No inventory row for {sku} size {size}."}
            price = conn.execute("SELECT unit_cost FROM pricing WHERE sku = ?", (sku,)).fetchone()
            if price is None:
                return {"ok": False, "message": f"No pricing row for {sku}."}
            amount = round(qty * price["unit_cost"], 2)
            blocking = _open_invoices(conn, today, vendor_id)
            if blocking:
                warnings.append(
                    "Vendor is blocked by unpaid invoice(s) "
                    + ", ".join(f"#{b['id']}" for b in blocking)
                    + ". The human pay step will refuse this order until they are paid."
                )

        existing = conn.execute(
            "SELECT * FROM payment_requests WHERE status = 'pending' AND kind = ? "
            "AND IFNULL(ref_id, -1) = IFNULL(?, -1) AND IFNULL(sku, '') = IFNULL(?, '') "
            "AND IFNULL(size, '') = IFNULL(?, '')",
            (kind, ref_id, sku, size),
        ).fetchone()
        if existing:
            return {"ok": True, "duplicate": True, "request": dict(existing),
                    "message": f"A pending request (#{existing['id']}) already covers this."}

        cur = conn.execute(
            "INSERT INTO payment_requests (ticket_id, kind, ref_id, vendor_id, sku, size, qty, amount, "
            "requested_by, reason, shop_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ticket_id, kind, ref_id, vendor_id, sku, size, qty, amount, requested_by,
             reason.strip(), today.isoformat()),
        )
        cash = _cash(conn)["total_balance"]
        pending_total = sum(r["amount"] for r in conn.execute(
            "SELECT amount FROM payment_requests WHERE status = 'pending'"))
        if cash - pending_total < 0:
            warnings.append(
                f"All pending requests together (${pending_total:,.2f}) exceed cash (${cash:,.2f}). "
                "The human must choose which to approve; the pay step refuses anything that overdraws."
            )
        return {
            "ok": True,
            "request_id": cur.lastrowid,
            "status": "pending",
            "amount": amount,
            "cash_now": cash,
            "cash_after_this_payment": cash - amount,
            "cash_after_all_pending": cash - pending_total,
            "warnings": warnings,
            "note": f"Waiting for {HUMAN_APPROVER} to approve. No money has moved.",
        }


# ---------------------------------------------------------------------------
# Human-only tools: the ONLY way money leaves. Never given to an agent.
# ---------------------------------------------------------------------------

OSCAR = "Oscar (Accounting): "


def _add_month(d: date) -> date:
    year, month = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    for day in (d.day, 30, 29, 28):
        try:
            return date(year, month, day)
        except ValueError:
            continue
    raise ValueError(d)


# Oscar's payment priority: keep the shop open, then unblock sales, then grow sales.
PRIORITY = {"rent": 1, "invoice": 2, "purchase_order": 3}
PRIORITY_WHY = {
    "rent": "keeps us in the building",
    "invoice": "unblocks a vendor so we can sell",
    "purchase_order": "restocks to grow sales",
}
RISK_WINDOW_DAYS = 30


def _obligations(conn: sqlite3.Connection, today: date) -> list[dict]:
    """Every bill coming due (rent within 30 days, open invoices, pending purchase
    orders), whether or not anyone has asked to pay it yet, in Oscar's order."""
    items: list[dict] = []
    horizon = date.fromordinal(today.toordinal() + RISK_WINDOW_DAYS).isoformat()
    for lease in conn.execute("SELECT * FROM leases WHERE next_due <= ? ORDER BY next_due", (horizon,)):
        items.append({"kind": "rent", "ref_id": lease["id"], "amount": lease["monthly_rent"],
                      "label": f"Rent for {lease['space_name']} (${lease['monthly_rent']:,.2f}, due {lease['next_due']})",
                      "due": lease["next_due"]})
    for inv in _open_invoices(conn, today):
        overdue = f", {inv['days_overdue']} days overdue" if inv["overdue"] else ""
        items.append({"kind": "invoice", "ref_id": inv["id"], "amount": inv["amount"],
                      "label": f"Invoice #{inv['id']} to {inv['vendor_name']} (${inv['amount']:,.2f}{overdue})",
                      "due": inv["due_date"]})
    for po in _rows(conn, "payment_requests",
                    "SELECT * FROM payment_requests WHERE kind = 'purchase_order' AND status = 'pending'"):
        items.append({"kind": "purchase_order", "ref_id": po["id"], "amount": po["amount"],
                      "label": f"Purchase order #{po['id']}: {po['qty']} x {po['sku']} size {po['size']} (${po['amount']:,.2f})",
                      "due": po["shop_date"]})
    items.sort(key=lambda o: (PRIORITY[o["kind"]], o["due"]))
    return items


def _payment_risk(conn: sqlite3.Connection, today: date, req: sqlite3.Row, balance: float) -> dict:
    """Would paying this request leave too little cash for a MORE important bill?"""
    this_key = (req["kind"], req["ref_id"] if req["kind"] != "purchase_order" else req["id"])
    obligations = _obligations(conn, today)
    protected = [o for o in obligations
                 if PRIORITY[o["kind"]] < PRIORITY[req["kind"]] and (o["kind"], o["ref_id"]) != this_key]
    reserve = sum(o["amount"] for o in protected)
    after = balance - req["amount"]
    order, running = [], balance
    for o in obligations:
        affordable = running - o["amount"] >= 0
        running = running - o["amount"] if affordable else running
        order.append({"label": o["label"], "why": PRIORITY_WHY[o["kind"]], "affordable": affordable,
                      "cash_after": round(running, 2)})
    at_risk = after < reserve
    result = {"at_risk": at_risk, "cash_now": balance, "cash_after_this": round(after, 2),
              "reserve_needed": round(reserve, 2), "recommended_order": order,
              "bills_at_risk": [o["label"] for o in protected] if at_risk else []}
    if at_risk:
        result["warning"] = (
            OSCAR + f"Actually, hold on. Paying this ${req['amount']:,.2f} leaves ${after:,.2f}, but "
            + "; ".join(o["label"] for o in protected)
            + f" needs ${reserve:,.2f}. That's more important ("
            + ", ".join(PRIORITY_WHY[o['kind']] for o in protected)
            + "). My recommended order: " + " → ".join(o["label"].split(" (")[0] for o in obligations)
            + ". Only pay this now if you understand we may not cover that bill."
        )
    return result


@mcp.tool
def assess_payment_request(request_id: int) -> dict:
    """Read-only. Oscar's priority check for one pending request: would paying it
    leave too little cash for a more important bill (rent first, then overdue
    vendor invoices, then restock orders)? Returns the warning and recommended order.
    """
    with closing(_connect()) as conn:
        today = _today(conn)
        rows = _rows(conn, "payment_requests", "SELECT * FROM payment_requests WHERE id = ?", (request_id,))
        if not rows:
            return {"found": False, "message": f"No payment request #{request_id}."}
        req = conn.execute("SELECT * FROM payment_requests WHERE id = ?", (request_id,)).fetchone()
        return {"found": True, "request_id": request_id,
                **_payment_risk(conn, today, req, _cash(conn)["total_balance"])}


@mcp.tool
def human_approve_and_pay(request_id: int, approver: str, note: str = "", account: str = "checking",
                          acknowledge_risk: bool = False) -> dict:
    """HUMAN ONLY. Approve a pending payment request and pay it. `note` is the
    approver's reason, saved with the decision.

    Refuses (with Oscar's reason) if the approver is not the shop's human
    approver, the request is not pending, a purchase-order vendor is still
    blocked, or the payment would make the cash balance negative. If paying it
    would leave too little cash for a more important bill (rent protection), it
    stops and returns Oscar's warning unless acknowledge_risk=True. On success it
    records the payment and updates every related table.
    """
    if approver.strip() != HUMAN_APPROVER:
        return {"paid": False, "reason": OSCAR + f"Only {HUMAN_APPROVER} can approve payments. "
                "Agents and anyone else are refused."}
    with closing(_connect(write=True)) as conn, conn:
        today = _today(conn)
        req = conn.execute("SELECT * FROM payment_requests WHERE id = ?", (request_id,)).fetchone()
        if req is None:
            return {"paid": False, "reason": OSCAR + f"There is no payment request #{request_id}."}
        if req["status"] != "pending":
            return {"paid": False, "reason": OSCAR + f"Request #{request_id} is already {req['status']}."}
        acct = conn.execute("SELECT * FROM cash_accounts WHERE name = ?", (account,)).fetchone()
        if acct is None:
            return {"paid": False, "reason": OSCAR + f"There is no cash account named {account!r}."}

        if req["kind"] == "invoice":
            inv = conn.execute("SELECT status FROM invoices WHERE id = ?", (req["ref_id"],)).fetchone()
            if inv is None or inv["status"] != "open":
                return {"paid": False, "reason": OSCAR + f"Invoice #{req['ref_id']} is no longer open."}
        if req["kind"] == "purchase_order":
            blocking = _open_invoices(conn, today, req["vendor_id"])
            if blocking:
                ids = ", ".join(f"#{b['id']}" for b in blocking)
                return {"paid": False, "reason": OSCAR + "Actually, I can't send this order. "
                        f"The vendor won't ship while invoice {ids} is unpaid. Pay that first."}

        balance, amount = acct["balance"], req["amount"]
        if balance - amount < 0:
            return {
                "paid": False,
                "reason": OSCAR + f"Actually, I have to refuse. Paying ${amount:,.2f} from {account} "
                f"(balance ${balance:,.2f}) would leave -${amount - balance:,.2f}. "
                f"We are ${amount - balance:,.2f} short, and the balance can never go negative. "
                "No money moved.",
                "balance": balance,
                "amount": amount,
                "shortfall": round(amount - balance, 2),
            }

        risk = _payment_risk(conn, today, req, balance)
        if risk["at_risk"] and not acknowledge_risk:
            return {"paid": False, "needs_acknowledgement": True, "reason": risk["warning"], "risk": risk}

        new_balance = round(balance - amount, 2)
        conn.execute("UPDATE cash_accounts SET balance = ?, date = ? WHERE name = ?",
                     (new_balance, today.isoformat(), account))
        cur = conn.execute(
            "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (req["kind"], req["ref_id"] if req["kind"] != "purchase_order" else request_id,
             amount, account, today.isoformat(), approver.strip()),
        )
        updated = ["cash_accounts", "payments", "payment_requests"]
        if req["kind"] == "invoice":
            conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (req["ref_id"],))
            updated.append("invoices")
        elif req["kind"] == "rent":
            lease = conn.execute("SELECT next_due FROM leases WHERE id = ?", (req["ref_id"],)).fetchone()
            next_due = _add_month(date.fromisoformat(lease["next_due"])).isoformat()
            conn.execute("UPDATE leases SET next_due = ? WHERE id = ?", (next_due, req["ref_id"]))
            updated.append("leases")
        conn.execute(
            "UPDATE payment_requests SET status = 'paid', decided_by = ?, decision_note = ? WHERE id = ?",
            (approver.strip(),
             f"Paid as payment #{cur.lastrowid}." + (f" Reason: {note.strip()}" if note.strip() else "")
             + (" (Approved despite Oscar's priority warning.)" if risk["at_risk"] else ""),
             request_id),
        )
        return {"paid": True, "payment_id": cur.lastrowid, "amount": amount,
                "approved_despite_priority_warning": risk["at_risk"],
                "balance_before": balance, "balance_after": new_balance, "tables_updated": updated}


@mcp.tool
def human_decline_payment(request_id: int, approver: str, reason: str) -> dict:
    """HUMAN ONLY. Decline a pending payment request. No money moves."""
    if approver.strip() != HUMAN_APPROVER:
        return {"declined": False, "reason": f"Only {HUMAN_APPROVER} can decide on payments."}
    with closing(_connect(write=True)) as conn, conn:
        req = conn.execute("SELECT status FROM payment_requests WHERE id = ?", (request_id,)).fetchone()
        if req is None or req["status"] != "pending":
            return {"declined": False, "reason": f"Request #{request_id} is not pending."}
        conn.execute(
            "UPDATE payment_requests SET status = 'declined', decided_by = ?, decision_note = ? WHERE id = ?",
            (approver.strip(), f"Declined. Reason: {reason.strip() or 'none given'}", request_id),
        )
        return {"declined": True, "request_id": request_id}


@mcp.tool
def human_reset_working_database(confirm: bool) -> dict:
    """HUMAN ONLY. Copy the untouched original database over the working copy,
    undoing every payment, draft, status change and request. Needs confirm=True.
    """
    if not confirm:
        return {"reset": False, "reason": "Pass confirm=True to reset."}
    original = DB_PATH.parent / ORIGINAL_DB_NAME
    if DB_PATH.name == ORIGINAL_DB_NAME or not original.exists():
        return {"reset": False, "reason": "Original database not found next to the working copy."}
    shutil.copyfile(original, DB_PATH)
    with closing(_connect()) as conn:
        return {"reset": True, "today": _today(conn).isoformat(), "cash": _cash(conn)}


if __name__ == "__main__":
    mcp.run()
