# Campus Customs Multi-Agent Operations (Homework 5)

An Office-themed agent team runs the Campus Customs shop. Michael (Boss), Dwight (Inventory), Oscar (Accounting), Darryl (Facilities), and Pam (Customer Service) work the ticket board through an MCP server. A human, **David Wallace**, approves every payment from a login-protected dashboard.

| Folder / file | What it is |
|---|---|
| `mcp_server/` | FastMCP server: every shop fact and change goes through it (`server.py`, tool list in its README) |
| `backend/` | PydanticAI agent team (`agents.py`, `prompts/`, `models.py`) plus the FastAPI routes (`main.py`) |
| `frontend/` | React + Vite + TypeScript dashboard (the Agent Desk) |
| `data/` | `campus_customs.db` (original, never changed) and `campus_customs_new.db` (working copy, as left by the official run) |
| `output/` | Harness, smoke tests, desk tickets (Expected/Actual/Cash/Reflection), design notes, resolved tickets, screenshots, audit trail |
| `RULES.md` | The shop rules every agent and tool follows |
| `AI_prompts.md` | The prompts I typed to my vibe coder, one section per problem |

Every agent uses only **`gpt-6-luna`** through Portkey (set once in `backend/config.py`).

## 1. One-time setup

You need Python 3.12+, Node.js 20+, and your own Portkey API key. Commands are for **Windows PowerShell**, with Mac/Linux versions underneath.

```powershell
# from the hw5 folder
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env          # then open .env and paste your PORTKEY_API_KEY
cd frontend; npm install; cd ..
```
Mac/Linux: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && cp .env.example .env && (cd frontend && npm install)`

**Set the approver password** (needed to approve or decline payments and to reset from the dashboard). The script asks for a password with hidden typing and saves only a salted PBKDF2 hash to `.env` as `APPROVER_PASSWORD_HASH`. The password itself is never stored. If you skip this, the app works but every approval is refused with a clear message.
```powershell
cd backend
..\.venv\Scripts\python.exe set_approver_password.py
cd ..
```
Mac/Linux: `cd backend && ../.venv/bin/python set_approver_password.py && cd ..`

## 2. Copy the original database to the working copy (clean run)

`data/campus_customs.db` is the original and is never changed. The app only reads and writes `data/campus_customs_new.db`. Whenever you want a clean run, copy the original over the working copy. Either command does it, and the script also logs the reset in the audit trail:
```powershell
.\.venv\Scripts\python.exe backend\reset_db.py
# or by hand:
copy data\campus_customs.db data\campus_customs_new.db
```
Mac/Linux: `.venv/bin/python backend/reset_db.py` or `cp data/campus_customs.db data/campus_customs_new.db`

Note: the working copy in this repo is the state **after** the official Problem 9 run (checking $160.00). Reset it first if you want to re-run the tickets.

## 3. Start the MCP server

The backend starts the MCP server for you, in-process, every time it runs, so the agents and routes always go through it. To run it on its own (for example, for a vibe coder or a quick test):
```powershell
.\.venv\Scripts\python.exe mcp_server\server.py
```
Mac/Linux: `.venv/bin/python mcp_server/server.py`

To connect it to Claude Code, `.mcp.json` in this folder registers it as `campus-customs` (on Mac/Linux change the command to `.venv/bin/python`). Restart Claude Code and approve the server.

## 4. Start the FastAPI backend (terminal 1)

```powershell
cd backend
..\.venv\Scripts\uvicorn.exe main:app --reload --port 8000
```
Mac/Linux: `cd backend && ../.venv/bin/uvicorn main:app --reload --port 8000`. If your venv is activated, plain `uvicorn main:app --reload --port 8000` works too.

This serves `http://localhost:8000` (route docs at `/docs`; route list in `output/harness.md`, section 9). It allows the dashboard's origin, `http://localhost:5173`.

## 5. Start the React board (terminal 2)

```powershell
cd frontend
npm run dev
```
Open `http://localhost:5173`. Pick a ticket, click **Start the team**, and watch the live feed. Log in on **David Wallace's desk** to approve or decline payments.

## 6. A full three-ticket run

1. **Reset the database first** (step 2, or the 🔥 reset button on David's desk), so you start from checking $3,400.00.
2. Start the backend and the board (steps 4–5).
3. Run tickets **101, 102, 103** one at a time with **Start the team**. Each takes 1–2 minutes and roughly 40–80K tokens.
4. As David, approve or decline each payment request. Oscar's rent-protection warning appears if an approval would leave too little for a more important bill.

## Stopping the servers

Press **Ctrl+C** in each terminal. Before restarting, make sure nothing is still using port 8000:
```powershell
netstat -ano | findstr :8000
taskkill /PID <pid> /T /F
```
Mac/Linux: `lsof -i :8000` then `kill <pid>`

## Checks

- `.\.venv\Scripts\python.exe backend\check_setup.py`: model, MCP server, agent tool access, and one tiny Portkey call.
- `.\.venv\Scripts\python.exe mcp_server\test_safety.py`: the money rules and rent protection, tested on a throwaway copy of the database.

## How to read `output/audit_trail.json`

The audit trail is append-only, so it keeps the whole history of building this app:
- **Entries 0–402 (before 2026-11-02 01:55 UTC) are development tests** from Problems 5–8: route and dashboard tests, plus my practice runs. Approvals in that range were made on data that was **reset afterwards**. During the AI's tests, they used a throwaway test password that was deleted, and none of those payments carried into the official run.
- **Entry 403 (`database_reset`, starting balance $3,400) begins the official Problem 9 run.** From there: the three ticket runs (`fd1edb471c5c`, `5520d2876479`, `bf019b8b99fe`), then my own login as David Wallace and my two approvals (invoice #501 $840 and rent $2,400). Ending checking: $160.00.
