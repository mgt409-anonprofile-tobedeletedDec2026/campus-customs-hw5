"""Reset the working database: copy the original over campus_customs_new.db.

Run before any full ticket run:  .venv\\Scripts\\python.exe backend\\reset_db.py
The original data/campus_customs.db is only read, never changed. The reset is
recorded in the audit trail, so the dashboard's feed starts fresh after it.
"""

import shutil
import sqlite3

import audit
from config import ORIGINAL_DB, WORKING_DB

if __name__ == "__main__":
    shutil.copyfile(ORIGINAL_DB, WORKING_DB)
    with sqlite3.connect(f"file:{WORKING_DB.as_posix()}?mode=ro", uri=True) as conn:
        balance = conn.execute("SELECT balance FROM cash_accounts WHERE name = 'checking'").fetchone()[0]
    audit.record("human", None, None, "database_reset", via="backend/reset_db.py",
                 starting_checking_balance=balance)
    print(f"Reset {WORKING_DB.name} from {ORIGINAL_DB.name}. Starting checking balance: ${balance:,.2f}")
