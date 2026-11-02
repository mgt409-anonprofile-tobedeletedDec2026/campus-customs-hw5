# Campus Customs MCP Server

The shared toolbox for the Campus Customs agent team (Michael/Boss, Dwight/Inventory, Oscar/Accounting, Darryl/Facilities, Pam/Customer Service). Every agent gets shop facts and makes board changes through these tools, never by touching the database directly, so the shop rules in [`../RULES.md`](../RULES.md) are enforced in one place.

## Database
- **Uses:** `hw5/data/campus_customs_new.db` (the working copy).
- **Never opens:** `hw5/data/campus_customs.db` (the original reset copy). The server refuses if pointed at it.
- The path is set once in `server.py` (`DB_PATH`). Override it with the `CAMPUS_CUSTOMS_DB` environment variable.
- "Today" always comes from `desk.date_today`, not the computer clock.
- The first agent write creates three board tables in the working copy: `ticket_updates`, `drafts`, `payment_requests`.

## Tools (15)

### Read tools (database opened read-only)
| Tool | Ticket | What it returns |
|---|---|---|
| `check_stock_and_restock(sku, size, qty_needed=1)` | 101 | Stock for one SKU + size. If short: vendors' specialty, lead time, arrival date, and whether an unpaid invoice blocks them. |
| `check_rent_due(lease_id)` | 102 | Rent, due date, days until due, cash balance, balance after rent and after other open bills. |
| `check_bulk_order_pricing(sku, size, qty_requested, discount_percent=0)` | 103 | Stock vs. request, cost, list price, margin, max discount before a loss, restock cost, whether cash covers bills + rent + restock, vendor block. |
| `get_ticket_board(status="open")` | all | Tickets with latest update, draft count, and payment requests (customer names withheld). |
| `get_ticket(ticket_id)` | all | One ticket with its linked inventory, pricing, invoice, vendor, lease, updates, drafts, and requests. |
| `get_cash_position()` | all | Cash, open invoices, rent due in 30 days, pending requests, and cash left after them. |
| `list_payment_requests(status="pending")` | all | Payment requests by status. |
| `list_drafts(ticket_id=None)` | all | Draft messages on the board. |
| `assess_payment_request(request_id)` | all | Rent protection: would paying this leave too little cash for a more important bill (rent, then vendor invoices, then restock)? Returns Oscar's warning and the recommended order. |

### Agent write tools (board only, no money moves)
| Tool | What it does |
|---|---|
| `update_ticket_status(ticket_id, new_status, agent, note)` | Changes a ticket's status and logs who and why in `ticket_updates`. |
| `save_draft_message(ticket_id, author_agent, recipient_role, subject, body)` | Saves a draft on the board. Never sent. |
| `request_payment_approval(ticket_id, kind, requested_by, reason, ...)` | Creates a *pending* request for the human. The amount comes from the database. Flags blocked vendors and cash shortfalls. |

### Human-only tools (never given to an agent)
| Tool | What it does |
|---|---|
| `human_approve_and_pay(request_id, approver, note="", account="checking", acknowledge_risk=False)` | Only `HUMAN_APPROVER` (David Wallace) can pay. Refuses, with Oscar's reason, if cash would go negative or a vendor is blocked. Stops on the rent-protection warning unless `acknowledge_risk=True`. On success, updates `cash_accounts`, `payments`, `invoices`/`leases`, and `payment_requests`. |
| `human_decline_payment(request_id, approver, reason)` | Declines a pending request, saving the reason. No money moves. |
| `human_reset_working_database(confirm)` | Copies the original database over the working copy (a fresh start). |

The human-only tools are called only by the backend's login-protected routes (`backend/main.py`), never by an agent.

## Run and test
The backend starts this server in-process automatically. `mcp_server/requirements.txt` lists the server's own needs (`fastmcp`) if you want to run it alone.
```powershell
# from hw5, using the one shared environment (see ../README.md)
.\.venv\Scripts\python.exe mcp_server\server.py        # run the server (stdio)
.\.venv\Scripts\python.exe mcp_server\test_safety.py   # money rules + rent protection on a throwaway copy
```
