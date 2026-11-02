"""Run the agent team on one ticket from the command line.

    .venv\\Scripts\\python.exe backend\\reset_db.py      (before a full run)
    .venv\\Scripts\\python.exe backend\\run_ticket.py 101
"""

import asyncio
import sys

from agents import run_ticket

if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        sys.exit("Usage: run_ticket.py <ticket_id>")
    result = asyncio.run(run_ticket(int(sys.argv[1])))
    print(result.model_dump_json(indent=2))
