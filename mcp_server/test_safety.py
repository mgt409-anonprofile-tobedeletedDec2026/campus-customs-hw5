"""Safety test for the money tools, run on a THROWAWAY copy of the original database.

    .venv\\Scripts\\python.exe test_safety.py

Never touches data/campus_customs_new.db. Checks that amounts come from the
database, only the human approver can pay, blocked vendors can't be paid, cash
never goes negative (with Oscar's reason), and every related table is updated.
"""

import asyncio
import os
import sys
import shutil
import sqlite3
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
TMP_DIR = Path(tempfile.mkdtemp())
TMP = TMP_DIR / "safety_copy.db"
shutil.copyfile(HERE.parent / "data" / "campus_customs.db", TMP)
shutil.copyfile(HERE.parent / "data" / "campus_customs.db", TMP_DIR / "campus_customs.db")  # its reset source
os.environ["CAMPUS_CUSTOMS_DB"] = str(TMP)
os.environ["HUMAN_APPROVER"] = "David Wallace"

from fastmcp import Client  # noqa: E402

from server import mcp  # noqa: E402


def db(sql):
    with sqlite3.connect(TMP) as c:
        return c.execute(sql).fetchall()


async def main():
    async with Client(mcp) as c:
        async def tool(name, **args):
            return (await c.call_tool(name, args)).data

        inv = await tool("request_payment_approval", ticket_id=101, kind="invoice", ref_id=501,
                         requested_by="accounting", reason="Unblock Bulldog Print Co")
        assert inv["amount"] == 840, inv
        print("[ok] invoice request amount comes from the database: $840")

        po = await tool("request_payment_approval", ticket_id=103, kind="purchase_order", vendor_id=1,
                        sku="CC-HOOD-NAVY", size="M", qty=12, requested_by="accounting", reason="Restock")
        assert po["amount"] == 264 and po["warnings"], po
        print("[ok] purchase order = 12 x $22 = $264, flagged: vendor blocked")

        r = await tool("human_approve_and_pay", request_id=po["request_id"], approver="David Wallace")
        assert not r["paid"] and "invoice #501" in r["reason"], r
        print("[ok] pay refused while vendor blocked:", r["reason"])

        r = await tool("human_approve_and_pay", request_id=inv["request_id"], approver="Michael Scott")
        assert not r["paid"], r
        print("[ok] non-human approver refused:", r["reason"])

        rent = await tool("request_payment_approval", ticket_id=102, kind="rent", ref_id=1,
                          requested_by="accounting", reason="Rent due 2026-09-02")
        assert rent["amount"] == 2400, rent
        dup = await tool("request_payment_approval", ticket_id=102, kind="rent", ref_id=1,
                         requested_by="accounting", reason="again")
        assert dup.get("duplicate"), dup
        print("[ok] rent request $2,400; duplicate request detected")

        r = await tool("human_approve_and_pay", request_id=inv["request_id"], approver="David Wallace")
        assert r["paid"] and r["balance_after"] == 2560, r
        assert db("SELECT status FROM invoices WHERE id=501") == [("paid",)]
        print("[ok] David Wallace paid #501: cash 3400 -> 2560, invoice marked paid")

        r = await tool("human_approve_and_pay", request_id=rent["request_id"], approver="David Wallace")
        assert r["paid"] and r["balance_after"] == 160, r
        assert db("SELECT next_due FROM leases WHERE id=1") == [("2026-10-02",)]
        print("[ok] rent paid: cash 2560 -> 160, lease next_due -> 2026-10-02")

        r = await tool("human_approve_and_pay", request_id=po["request_id"], approver="David Wallace")
        assert not r["paid"] and r["shortfall"] == 104, r
        assert db("SELECT balance FROM cash_accounts") == [(160.0,)]
        print("[ok] restock refused, cash stays $160:", r["reason"])

        assert db("SELECT kind, amount, approved_by FROM payments ORDER BY id") == [
            ("invoice", 840.0, "David Wallace"), ("rent", 2400.0, "David Wallace")]
        print("[ok] payments table: 2 rows, both approved_by David Wallace")

        d = await tool("save_draft_message", ticket_id=101, author_agent="customer_service",
                       recipient_role="customer", subject="Your tee", body="Hi there!")
        s = await tool("update_ticket_status", ticket_id=101, new_status="waiting_on_human",
                       agent="boss", note="Waiting on approval")
        assert d["ok"] and s["ok"]
        print("[ok] draft saved (not sent) and ticket status updated with a note")

        # --- Rent protection: approving in the wrong order -----------------
        r = await tool("human_reset_working_database", confirm=True)
        assert r["reset"] and r["cash"]["total_balance"] == 3400
        print("\n[ok] throwaway copy reset for the rent-protection test: $3,400")
        inv = await tool("request_payment_approval", ticket_id=101, kind="invoice", ref_id=501,
                         requested_by="accounting", reason="Unblock vendor")
        po = await tool("request_payment_approval", ticket_id=103, kind="purchase_order", vendor_id=1,
                        sku="CC-HOOD-NAVY", size="M", qty=12, requested_by="accounting", reason="Restock")
        r = await tool("human_approve_and_pay", request_id=inv["request_id"], approver="David Wallace")
        assert r["paid"] and not r["approved_despite_priority_warning"] and r["balance_after"] == 2560, r
        print("[ok] #501 paid with no warning: $2,560 still covers the $2,400 rent")

        risk = await tool("assess_payment_request", request_id=po["request_id"])
        assert risk["at_risk"] and risk["cash_after_this"] == 2296 and risk["reserve_needed"] == 2400, risk
        r = await tool("human_approve_and_pay", request_id=po["request_id"], approver="David Wallace")
        assert not r["paid"] and r["needs_acknowledgement"], r
        assert db("SELECT balance FROM cash_accounts") == [(2560.0,)]
        print("[ok] restock stopped until David acknowledges:", r["reason"])

        r = await tool("human_approve_and_pay", request_id=po["request_id"], approver="David Wallace",
                       acknowledge_risk=True)
        assert r["paid"] and r["approved_despite_priority_warning"] and r["balance_after"] == 2296, r
        print("[ok] David ticked 'I understand, pay anyway': restock paid, cash $2,296")

        rent = await tool("request_payment_approval", ticket_id=102, kind="rent", ref_id=1,
                          requested_by="accounting", reason="Rent due")
        r = await tool("human_approve_and_pay", request_id=rent["request_id"], approver="David Wallace")
        assert not r["paid"] and r["shortfall"] == 104, r
        assert db("SELECT balance FROM cash_accounts") == [(2296.0,)]
        print("[ok] exactly the risk Oscar warned about: rent refused, $104 short, cash stays $2,296")
    print("\nAll safety checks passed on a throwaway copy. Working database untouched.")


if __name__ == "__main__":
    asyncio.run(main())
