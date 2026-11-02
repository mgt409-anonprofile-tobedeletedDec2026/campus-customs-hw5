# Campus Customs Agent Harness

The agents' briefing binder. Read this together with [`RULES.md`](../RULES.md). We'll keep adding to it in later problems.

- **Working database:** `data/campus_customs_new.db` (the agents read and write here)
- **Original database:** `data/campus_customs.db` (never changed; copy it over the working file to reset)

---

## 1. Tables and fields

### `desk`: the shop's "today"
| Field | Meaning |
|---|---|
| `date_today` | The shop's current date (`2026-08-31`). **Always use this, never the computer clock**, to judge what is due or overdue. |
| `notes` | Free-text note for the desk (currently empty). |

**Why it matters:** Every overdue, due-soon or arrival-date calculation starts here.

### `tickets`: the work board
| Field | Meaning |
|---|---|
| `id` | Ticket number (101, 102, 103). |
| `type` | Kind of work: `customer_order`, `rent_notice`, `price_override`. Tells the Boss who to route it to. |
| `requester` | Who asked (a customer, landlord or group). Customer Service drafts replies to them. **Don't copy it into public files.** |
| `subject` | Short title. |
| `sku`, `size`, `qty` | The product and amount involved → links to `inventory` and `pricing`. |
| `lease_id` | Links to `leases.id` (rent tickets). |
| `invoice_id` | Links to `invoices.id` (an invoice tied to this ticket). |
| `status` | `open` until resolved. Agents update it when the ticket is done. |
| `notes` | Details from the requester. |
| `created_at` | When the ticket arrived. |

**Why it matters:** This is the Boss's inbox. The link fields (`sku`, `lease_id`, `invoice_id`) tell agents which other tables to check.

### `inventory`: stock on hand
| Field | Meaning |
|---|---|
| `sku` | Product code (e.g. `CC-TEE-WHITE`). Links to `pricing.sku`. |
| `name` | Product name. |
| `size` | `S`/`M`/`L`/`XL`, or `OS` (one size). **Stock is tracked per SKU *and* size**, so always check both. |
| `qty` | Units on hand. `0` means out of stock. |
| `location` | Shelf aisle. |

**Why it matters:** Inventory checks this to fill orders and to spot shortfalls (requested qty − on-hand qty).

### `pricing`: cost and price per product
| Field | Meaning |
|---|---|
| `sku` | Product code. Links to `inventory.sku`. |
| `unit_cost` | What the shop pays a vendor per unit. **The floor for any discount.** Selling below this loses money. |
| `list_price` | Normal selling price. Margin = `list_price − unit_cost`. |

**Why it matters:** Accounting uses it to check margins on discounts and to price restock purchase orders (`qty × unit_cost`).

### `vendors`: who can restock
| Field | Meaning |
|---|---|
| `id` | Vendor number. Links to `invoices.vendor_id`. |
| `name` | Vendor name. |
| `specialty` | What they supply. **Bulldog Print Co** handles apparel reprints, **Elm City Gifts** handles mugs and small goods, and **QuickShip CT** is only a courier (it doesn't supply product). |
| `lead_days` | Days from order to arrival. Arrival = `date_today` + `lead_days`. |

**Why it matters:** Inventory picks the right vendor for a SKU and estimates when stock arrives.

### `invoices`: bills the shop owes vendors
| Field | Meaning |
|---|---|
| `id` | Invoice number. Linked from `tickets.invoice_id`. |
| `vendor_id` | Which vendor is owed. Links to `vendors.id`. |
| `amount` | Amount owed. |
| `due_date` | Overdue if earlier than `desk.date_today`. |
| `status` | `open` = unpaid. Set it to paid after an approved payment. **A vendor with an open invoice will not ship.** |
| `description` | What the bill was for. |

**Why it matters:** Accounting watches it. An open invoice blocks restocking from that vendor.

### `leases`: the shop space
| Field | Meaning |
|---|---|
| `id` | Lease number. Linked from `tickets.lease_id`. |
| `space_name` | The space (Chapel Street shop). |
| `landlord` | Who gets the rent. |
| `monthly_rent` | Rent amount ($2,400). |
| `next_due` | Next rent due date. Move it forward a month once rent is paid. |
| `notes` | Free text. |

**Why it matters:** Facilities owns it. It tells agents how much rent is due and when.

### `cash_accounts`: the money
| Field | Meaning |
|---|---|
| `name` | Account (`checking`). |
| `balance` | Cash available ($3,400). **Can never go below zero.** |
| `date` | Date the balance was last updated. |

**Why it matters:** Every payment comes out of here. Cash only goes out in this homework.

### `payments`: record of money paid (empty to start)
| Field | Meaning |
|---|---|
| `id` | Payment number. |
| `kind` | What was paid (e.g. invoice, rent). |
| `ref_id` | The ID of the thing paid (an `invoices.id` or `leases.id`, depending on `kind`). |
| `amount` | Amount paid. |
| `account` | Which `cash_accounts.name` it came from. |
| `paid_at` | Date paid. |
| `approved_by` | **The human who approved it. Must always be filled.** No approval, no payment. |

**Why it matters:** This is the audit trail that proves a human approved every payment.

### How the tables connect
```
tickets.sku ──► inventory.sku (+ size) ──► pricing.sku
tickets.invoice_id ──► invoices.id ──► invoices.vendor_id ──► vendors.id
tickets.lease_id ──► leases.id
payments.ref_id ──► invoices.id or leases.id      payments.account ──► cash_accounts.name
```

---

## 2. Snapshot as of `date_today` = 2026-08-31

- **Cash:** $3,400 in checking.
- **Out of stock:** White tee size S (0) and Crest Mug (0).
- **Open invoice:** #501, $840 to Bulldog Print Co, due 2026-08-28. **Overdue by 3 days.**
- **Rent:** $2,400 due 2026-09-02 (in 2 days).

---

## 3. The three open tickets

### Ticket 101: customer order (1 white tee, size S)
- **Links:** `inventory` (CC-TEE-WHITE, S) → `pricing` → `invoices` #501 → `vendors` #1 Bulldog Print Co.
- **What an agent finds:** Size S has **0 in stock**. The only apparel vendor is Bulldog Print Co (5-day lead). Invoice #501 to them ($840) is **open and overdue**, so **they won't ship** until it's paid.
- **Path to resolve:** Accounting prepares the $840 payment → a human approves → mark #501 paid → order the reprint → stock arrives around 2026-09-05 (5 days after payment) → Customer Service drafts a message about the delay.

### Ticket 102: rent notice
- **Links:** `leases` #1 → `cash_accounts`.
- **What an agent finds:** $2,400 is due 2026-09-02 and the balance is $3,400.
- **Path to resolve:** Facilities confirms the lease → Accounting prepares the payment → a human approves → record it in `payments`, lower the balance, and move `next_due` to the next month.
- **Note:** The ticket says "Email". Do **not** email the landlord. Any reply is a draft on the board.

### Ticket 103: bulk discount request (20 navy hoodies, size M)
- **Links:** `inventory` (CC-HOOD-NAVY, M) → `pricing` → `vendors` #1 Bulldog Print Co.
- **What an agent finds:** Only **8 in stock**, so the order is **12 short**. Cost is $22 and list price is $58 ($36 margin per hoodie). Restocking 12 costs about **$264**, from the same vendor that **#501 blocks**.
- **Path to resolve:** Accounting checks what discount keeps a healthy margin (never below the $22 cost). The Boss decides. Inventory plans the restock once #501 is paid. Customer Service drafts the offer.

---

## 4. Watch-outs (possible slip-ups)

1. **Cash is tight.** Invoice #501 ($840) + rent ($2,400) = $3,240 and leaves **$160**. The hoodie restock (~$264) would then **overdraw by ~$104**, so the pay tool must refuse it. Rent is the most urgent (due in 2 days), so the order of payments matters.
2. **Vendor #1 is blocked by #501.** Tickets 101 and 103 both need Bulldog Print Co. Neither restock can happen until #501 is paid with human approval.
3. **Don't route around the block.** QuickShip CT is a courier, not an apparel supplier, and Elm City Gifts only does mugs and small goods. Neither can supply tees or hoodies.
4. **Check stock by size, not just SKU.** White tees exist in M/L/XL, but the customer needs S, which has 0.
5. **Discount floor.** A bulk discount must stay above the $22 unit cost, or the shop loses money on every hoodie.
6. **Use `desk.date_today` (2026-08-31), not the real date**, to decide what's overdue.
7. **Every payment needs a human `approved_by`**, even when an agent or a ticket says it's fine to pay.
8. **No emails.** All customer, landlord and vendor messages stay as drafts on the board.
9. **Update every related table after a payment:** `payments`, `cash_accounts`, plus `invoices.status` or `leases.next_due`.

---

## 5. MCP tools (Problem 3)

Server: [`mcp_server/server.py`](../mcp_server/server.py), built with FastMCP. Reads `data/campus_customs_new.db` only, in read-only mode, and refuses to open the original. All three tools are read-only: none pays, orders, or edits anything. "Today" is always `desk.date_today`.

### `check_stock_and_restock(sku, size, qty_needed=1)` → Ticket 101
- **Reads:** `desk` (today), `inventory` (row matching `sku` + `size`), `vendors` (all, with `lead_days`), `invoices` (open invoices per vendor, and past invoices whose description mentions the SKU).
- **Returns:** on-hand qty and shortfall. If short, every vendor's specialty, lead time, arrival date (`date_today + lead_days`), `blocked` flag, blocking invoices with days overdue, and an `unblock_step` telling the agent to flag the payment for a human.
- **Why it's right for 101:** The customer needs a white tee in size **S**, which has 0 on hand. This tool checks the exact size, then shows that the only apparel vendor (Bulldog Print Co, which has supplied this SKU before) is blocked by overdue invoice #501 ($840), so the agent knows it must ask a human to approve that payment before a 5-day reprint can arrive.

### `check_rent_due(lease_id)` → Ticket 102
- **Reads:** `desk` (today), `leases` (`monthly_rent`, `next_due`), `cash_accounts` (all balances), `invoices` (other open bills).
- **Returns:** rent, due date, `days_until_due`, `overdue` flag, cash balance, balance after rent, whether cash covers rent, and the balance after rent **plus** every other open bill.
- **Why it's right for 102:** The rent ticket links to `lease_id` 1. This tool confirms $2,400 is due 2026-09-02 (2 days out), that cash covers it ($3,400 → $1,000), and that paying invoice #501 too leaves only $160, which is what the human needs to know before approving.

### `check_bulk_order_pricing(sku, size, qty_requested, discount_percent=0)` → Ticket 103
- **Reads:** `desk` (today), `inventory` (`sku` + `size`), `pricing` (`unit_cost`, `list_price`), `cash_accounts`, `invoices` (open bills), `leases` (rent due within 30 days), `vendors` (restock options and block status).
- **Returns:** stock vs. request and shortfall, unit cost, list price, margin ($ and %), the largest discount before a loss, the discounted price/margin/order profit, a `below_cost` flag, restock cost for the shortfall, cash left after open bills + upcoming rent + restock, and vendor block status.
- **Why it's right for 103:** The student group wants 20 size-M hoodies but only 8 are on hand. This tool shows the 12-unit shortfall costs $264 to restock from the blocked apparel vendor, that any discount must stay under 62.1% to beat the $22 cost, and that after #501 and rent, the restock would leave cash at **−$104**, so the agent must flag it instead of promising the order.

### Test results (run against the working database, no changes made)
| Call | Key result |
|---|---|
| `check_stock_and_restock("CC-TEE-WHITE", "S", 1)` | qty 0, shortfall 1; Bulldog Print Co blocked by #501 ($840, 3 days overdue); arrival 2026-09-05 once ordered |
| `check_rent_due(1)` | $2,400 due in 2 days; balance after rent $1,000; after rent + open bills $160 |
| `check_bulk_order_pricing("CC-HOOD-NAVY", "M", 20, 15)` | 8 on hand, short 12; 15% off = $49.30 (margin $27.30); restock $264; cash after everything −$104 → `cash_covers_everything: false` |
| Missing size / missing lease | Returns `found: false` with a clear message (no guessing) |
| Pointed at `campus_customs.db` | Refuses to open the original |

---

## 6. The agent team (Problem 5)

Built with PydanticAI in [`backend/agents.py`](../backend/agents.py). One prompt per agent in [`backend/prompts/`](../backend/prompts/), data types in [`backend/models.py`](../backend/models.py). Every agent uses **`gpt-6-luna`** through Portkey (set once in `backend/config.py`). Any agent can ask any other agent for help with `ask_teammate` (full connectivity), within the limits in section 8. Personalities are short flavor; **the shop rules always win**.

| Agent | Character | Job | MCP tools it may use |
|---|---|---|---|
| `boss` | Michael Scott | Reads each ticket, delegates, makes the final call, sets ticket status, escalates to the human | `get_ticket_board`, `get_ticket`, `get_cash_position`, `list_payment_requests`, `list_drafts`, `update_ticket_status` |
| `inventory` | Dwight Schrute | Stock by SKU + size, shortfalls, which vendor restocks, vendor blocks | `get_ticket`, `check_stock_and_restock`, `check_bulk_order_pricing` |
| `accounting` | Oscar Martinez | Cash, invoices, margins; **prepares** payment requests for the human; explains refusals | `get_ticket`, `get_cash_position`, `check_rent_due`, `check_bulk_order_pricing`, `check_stock_and_restock`, `list_payment_requests`, `request_payment_approval`, `assess_payment_request` |
| `facilities` | Darryl Philbin | Lease, rent amount, due date | `get_ticket`, `check_rent_due`, `get_cash_position` |
| `customer_service` | Pam Beesly | Draft messages that stay on the board | `get_ticket`, `list_drafts`, `save_draft_message` |
| **Human approver** | **David Wallace** | The only one who can approve or decline a payment (on the dashboard) | `human_approve_and_pay`, `human_decline_payment` (no agent has these) |

Every agent also has `ask_teammate` (a delegation tool in the backend, not a shop-data tool).

## 7. All MCP tools and the tables they use

Server: [`mcp_server/server.py`](../mcp_server/server.py). All shop facts and changes go through it; the backend has no other path to the database.

| Tool | Kind | Tables read | Tables written |
|---|---|---|---|
| `check_stock_and_restock` | read | desk, inventory, vendors, invoices | none |
| `check_rent_due` | read | desk, leases, cash_accounts, invoices | none |
| `check_bulk_order_pricing` | read | desk, inventory, pricing, cash_accounts, invoices, leases, vendors | none |
| `get_ticket_board` | read | desk, tickets, ticket_updates, drafts, payment_requests | none |
| `get_ticket` | read | desk, tickets, inventory, pricing, invoices, vendors, leases, ticket_updates, drafts, payment_requests | none |
| `get_cash_position` | read | desk, cash_accounts, invoices, vendors, leases, payment_requests | none |
| `list_payment_requests` | read | payment_requests | none |
| `list_drafts` | read | drafts | none |
| `update_ticket_status` | agent write (board) | desk, tickets | tickets.status, ticket_updates |
| `save_draft_message` | agent write (board) | desk, tickets | drafts |
| `request_payment_approval` | agent write (request only, **no money moves**) | desk, tickets, invoices, leases, vendors, inventory, pricing, cash_accounts | payment_requests |
| `assess_payment_request` | read (rent protection) | desk, payment_requests, leases, invoices, vendors, cash_accounts | none |
| `human_approve_and_pay` | **human only** (stops on the rent-protection warning unless David acknowledges it) | payment_requests, cash_accounts, invoices, vendors, leases, desk | cash_accounts, payments, invoices.status or leases.next_due, payment_requests |
| `human_decline_payment` | **human only** | payment_requests | payment_requests |
| `human_reset_working_database` | **human only** | desk, cash_accounts | replaces the whole working database with the original |

`ticket_updates`, `drafts` and `payment_requests` are board tables the server creates in the working copy the first time an agent writes. Resetting the database removes them.

## 8. Safety

### Guardrails for real customers and real money
- **Strict approval process.** Agents can only *request* a payment. The pay tool is human-only, checks that the approver is David Wallace, and is never given to any agent (enforced by a per-agent tool allowlist plus a server-side approver check).
- **Human sign-off on every payment,** recorded in `payments.approved_by`. Payment amounts always come from the database, never from an agent, so an agent can't inflate or invent a bill.
- **No negative cash.** The pay step refuses any payment that would overdraw, with Oscar's reason (balance, amount, shortfall). It also refuses purchase orders to vendors blocked by unpaid invoices. No tool can add cash.
- **Rent protection (payment order matters).** Approving in the wrong order can strand a critical bill. For example, restock $264 then #501 $840 leaves $2,296, so the $2,400 rent can't be paid. Before any approval, `human_approve_and_pay` (and the read-only `assess_payment_request`) checks the bills coming due in the next 30 days, in Oscar's priority order: **1) rent (keeps us in the building), 2) open vendor invoices (unblock sales), 3) restock orders (grow sales)**. If paying a request would leave less cash than the more important bills still need, the payment **stops** and David's inbox shows Oscar's warning, naming the bill at risk and the recommended order with the running cash. David must tick **"I understand, pay anyway"** before the payment goes through. The override is saved in the decision note and the audit trail. Cash still can never go negative. Tested on a throwaway database copy (`mcp_server/test_safety.py`): #501 paid with no warning ($2,560 still covers rent); the restock was **stopped** until acknowledged; once acknowledged it paid ($2,296); rent was then refused, $104 short. That is exactly the risk the flag warns about.
- **High confidentiality.** Customer names are withheld from every tool result, so they never reach the model, the drafts, or the audit trail. No API keys in code or logs. `.env` is git-ignored.
- **Nothing leaves the environment.** The agents have no email, web, phone, or file tools. Messages are drafts on the board for a human to read.
- **Strict documentation.** Every agent step (prompt, model text, tool call, tool result, delegation, limit hit, final report, token count) is appended to `output/audit_trail.json`, never wiped. Every ticket status change needs a note and is kept in `ticket_updates`. Every request for money is a `payment_requests` row with who asked, why, and the amount.
- **Identity can't be faked.** The backend fills in the acting agent's name on status changes, drafts, and payment requests, so one agent can't sign as another.
- **Least privilege.** Each agent sees only the tools its job needs (section 6). Only Michael changes ticket status, only Oscar requests payments, and only Pam writes drafts. When a run finishes, the backend marks the ticket resolved.
- **Replaceable agents.** Personalities live in one prompt file each. An agent that breaks a rule can be swapped for another character without touching the tools or rules.
- **Reset button.** `backend/reset_db.py` copies the untouched original over the working copy before a full run.

### Token limits (in `backend/config.py`)
| Limit | Value |
|---|---|
| Model requests per ticket (all agents combined) | 40 |
| Model requests per single agent turn | 8 |
| Total tokens per ticket | 200,000 |
| Delegation depth | 3 (Boss → A → B → C) |
| Times one agent may ask the same teammate, per ticket | 2 |
| Audit entries trimmed at | 4,000 characters |

Hitting a limit stops that branch cleanly, records a `limit_hit` entry, and tells the agent to flag the gap for the human. Personalities are capped at one short line per reply.

### Checks run (Problem 5)
- `backend/check_setup.py`: config (`gpt-6-luna`), MCP server starts with 13 tools, allowlists valid, no agent sees a `human_` tool, all 5 agents build, one tiny Portkey call to `gpt-6-luna` answered "OK", working database unchanged.
- `mcp_server/test_safety.py` (throwaway copy): amounts from the database, non-human approver refused, blocked vendor refused, #501 and rent paid by David Wallace with every table updated, the $264 restock then refused because cash would be −$104 (stays $160), duplicate requests caught.

---

## 9. Backend routes (Problem 7)

FastAPI app in [`backend/main.py`](../backend/main.py). Start it from `backend/` with `uvicorn main:app --reload --port 8000` → `http://localhost:8000`. Every shop fact and change goes through the MCP server. 🔒 = David Wallace must be logged in.

- `GET /api/health`: confirms the server is up, the model (`gpt-6-luna`), and who the human approver is.
- `GET /api/tickets`: all three tickets, each marked open or resolved, with its detailed status (e.g. `waiting_on_human`) and latest update.
- `GET /api/tickets/{id}`: one ticket with its linked rows, status history, drafts, and payment requests.
- `POST /api/tickets/{id}/run`: starts Michael and the team on that ticket in the background and returns a `run_id` right away (one run at a time). When the run finishes, the ticket is marked **resolved**, and any unpaid request is listed as `awaiting_david`.
- `GET /api/runs/current`: whether the team is working now, plus the last run's final report.
- `GET /api/events?after=&ticket_id=&run_id=&since_reset=`: recent agent events from `audit_trail.json` (what each character said, delegations, and tools used), for the board to poll. `since_reset=true` hides runs from before the last reset.
- `GET /api/cash`: the current checking balance from `cash_accounts`, plus open bills and pending requests.
- `GET /api/payment-requests?status=pending`: payment requests waiting for David Wallace (or `paid` / `declined` / `all`).
- `POST /api/login`: David Wallace logs in with the approver password and gets a 30-minute session token.
- `POST /api/logout`: ends the session.
- `GET /api/session`: says whether the caller is logged in as David Wallace and whether a password has been set.
- 🔒 `POST /api/payment-requests/{id}/approve` `{reason}`: **the only route that moves cash.** It pays the request and saves David's reason, or refuses with Oscar's explanation if cash would go negative or the vendor is blocked.
- 🔒 `POST /api/payment-requests/{id}/decline` `{reason}`: declines the request and saves David's reason. No money moves.
- 🔒 `POST /api/reset`: resets the working database to the original values (refused while a run is in progress). The audit trail is kept.

### Approver login safety
- The password is never stored. `.env` holds only `APPROVER_PASSWORD_HASH`, a **salted PBKDF2-SHA256 hash** (600,000 iterations), written by `backend/set_approver_password.py` with hidden typing.
- Passwords are checked with a **constant-time comparison**. Sessions are random tokens that **expire after 30 minutes**. **5 wrong guesses lock login for 5 minutes.**
- If no password is set, login and approval refuse with a clear message (no crash and no default password).
- Every login, failed login, approval, decline, and reset is appended to `audit_trail.json`.
- The `human_*` MCP tools are called only by these protected routes. Agents can't see or call them.
- Classroom-level: a real business would add single sign-on and two-factor login for anyone who approves money.

### Route tests (Problem 7)
All routes were tested against the live server, using a throwaway test password that was deleted afterwards.
- With no password set: approve and login returned 503 with the setup message.
- Without login: approve and reset returned 401.
- **Real agent run on ticket 102:** Michael asked Darryl and Oscar. Oscar created rent request #1 ($2,400) and no money moved. Michael set the ticket to `waiting_on_human`.
- **David approved rent:** cash $3,400 → $1,000, `leases.next_due` → 2026-10-02, and his reason was saved.
- **Approved invoice #501:** cash → $160.
- **The $264 hoodie order was refused** (409, "Oscar (Accounting): Actually, I have to refuse... -$104.00...") and then declined with a reason.
- **Lockout:** the 6th wrong password returned 429. Logout ended the session.
- **Database:** reset to the original values at the end (byte-for-byte match).


---

## 10. The dashboard (Problem 8)

React + Vite + TypeScript in [`frontend/`](../frontend/), started with `npm run dev` at `http://localhost:5173`. It talks only to the backend at `http://localhost:8000`, which allows that origin (CORS). Full design notes are in [`output/design.md`](design.md).

- **Ticket board (left):** three sticky notes with **Start the team** buttons and status stickers: 📬 Open, ⏳ Team working…, ✅ Resolved (set when the run finishes), plus a separate 💰 **Awaiting David · $X** sticker while a payment is pending.
- **Live feed (center):** refreshes every 1.5 s from `/api/events`. Each agent has their own color and cartoon portrait. Hand-offs show as **Michael → Dwight** banners, and tool calls as plain-English chips with the MCP tool name. Michael's built-in jokes rotate during a run (no tokens).
- **What each agent did:** summary cards, the tools each agent used, and **the Dundies** on a retro TV: 23 awards, drawn fresh for each run.
- **David Wallace's desk (right):** password login (salted hash, lockout), approval inbox with a reason box, Oscar's refusal bubble, the **rent-protection warning** with the "I understand, pay anyway" checkbox, and a login-only reset.
- **Cash:** always visible. On an approved payment a red **−$X** pops off and the balance counts down.

## 11. The official run (Problem 9)

Reset at 2026-11-02 01:55 UTC (starting checking **$3,400.00**). Then the team ran tickets 101, 102, 103 one at a time. **The student, logged in as David Wallace, made every approval in the dashboard. The AI approved nothing.**

| Ticket | Run | Agents (first call → hand-offs) | Requests | David's decision | Cash after |
|---|---|---|---|---|---|
| 101 tee | `fd1edb471c5c` · 19 calls · 51.9K tokens | Michael → **Dwight**, Oscar, Pam; Dwight → Oscar | #1 invoice #501 $840 | Approved: "we need this to be paid to keep making money" | $2,560.00 |
| 102 rent | `5520d2876479` · 15 calls · 42.8K tokens | Michael → **Darryl**, Oscar; Darryl → Oscar | #2 rent $2,400 | Approved: "we can't work without the office" | $160.00 |
| 103 hoodies | `bf019b8b99fe` · 26 calls · 81.5K tokens | Michael → **Dwight**, Oscar, Pam; Dwight → Oscar; Pam → Oscar; Oscar → Michael (one deeper hand-off stopped by the depth guardrail) | none (Oscar deferred the $264 restock: −$104) | n/a | $160.00 |

**Ending checking balance: $160.00** = `cash_accounts` (`('checking', 160.0, '2026-08-31')`). The math: $3,400 − $840 − $2,400 = $160. Two rows in `payments`, both `approved_by = David Wallace`. Invoice #501 is `paid`, and the lease's `next_due` is now 2026-10-02. Two customer drafts were saved and none were sent.

Outputs: Expected vs. Actual and the itemized Cash tab are in [`desk_tickets.html`](desk_tickets.html), per-ticket details in [`resolved_tickets.json`](resolved_tickets.json), screenshots in [`resolved_board.html`](resolved_board.html), and every step in [`audit_trail.json`](audit_trail.json).

## 12. How to read the audit trail
`output/audit_trail.json` is append-only, so it keeps the full build history:
- **Entries 0–402 are development tests** (Problems 5–8: route tests, dashboard tests and practice runs). Approvals in that range happened on data that was **reset afterwards**. The AI's tests used a throwaway approver password that was then deleted, and nothing carried into the official run.
- **Entry 403 (`database_reset`, $3,400) starts the official Problem 9 run.** It covers the three ticket runs, the student's own login as David Wallace, the two approvals ($840 and $2,400), and an ending balance of $160.00.
- A final `audit_note` entry records this same guide inside the file itself.

## 13. Coverage checklist
- **Tables:** section 1. **MCP tools** (15, with tables): sections 5 and 7. **Five agents:** section 6. **API routes:** section 9. **Dashboard:** section 10. **Safety rules** (approval, cash, rent protection, confidentiality, documentation, token limits, login): sections 8 and 9. **Official run and cash:** section 11.
