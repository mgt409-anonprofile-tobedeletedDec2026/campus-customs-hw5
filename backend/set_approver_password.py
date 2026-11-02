"""Set David Wallace's approver password (run this yourself in a terminal).

    cd hw5\\backend
    ..\\.venv\\Scripts\\python.exe set_approver_password.py

Your typing is hidden. Only a salted PBKDF2 hash is saved, as
APPROVER_PASSWORD_HASH in hw5/.env. The password itself is never stored or printed.
"""

from getpass import getpass

from dotenv import set_key

from auth import HASH_ENV, hash_password
from config import ROOT

MIN_LENGTH = 8

if __name__ == "__main__":
    first = getpass("New approver password for David Wallace (hidden): ")
    if len(first) < MIN_LENGTH:
        raise SystemExit(f"Please use at least {MIN_LENGTH} characters. Nothing was saved.")
    if getpass("Type it again to confirm (hidden): ") != first:
        raise SystemExit("The two passwords didn't match. Nothing was saved.")
    env_file = ROOT / ".env"
    env_file.touch(exist_ok=True)
    set_key(str(env_file), HASH_ENV, hash_password(first), quote_mode="never")
    print(f"Saved a salted hash to {env_file.name} as {HASH_ENV}. The password itself was not stored.")
