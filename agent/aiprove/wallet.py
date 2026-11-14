"""Wallet loading utilities.

Default source: the litcoin accounts.db (read-only), picking the wallet with
the lowest address (tie-break advantage in AIProve AutoGrade scoring: equal
scores are broken by the lower address winning).
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional

DEFAULT_DB = r"C:\Softs\litcoiin_ready1\data\accounts.db"


def load_from_db(db_path: str = DEFAULT_DB, address: Optional[str] = None) -> tuple[str, str]:
    """Return (address, private_key). If address is None, the lowest address."""
    uri = "file:" + Path(db_path).resolve().as_posix() + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        cur = con.cursor()
        if address:
            cur.execute("SELECT address, private_key FROM accounts WHERE address = ?", (address,))
            row = cur.fetchone()
            if not row:
                raise KeyError(f"address {address} not found in {db_path}")
            return row[0], row[1]
        cur.execute("SELECT address, private_key FROM accounts ORDER BY address ASC LIMIT 1")
        row = cur.fetchone()
        if not row:
            raise RuntimeError(f"no accounts in {db_path}")
        return row[0], row[1]
    finally:
        con.close()


def load_from_env() -> tuple[str, str]:
    pk = os.environ.get("AGENT_PRIVATE_KEY", "").strip()
    if not pk:
        raise RuntimeError("set AGENT_PRIVATE_KEY or use the accounts.db source")
    from eth_account import Account

    acct = Account.from_key(pk)
    return acct.address, pk


def load_wallet(address: Optional[str] = None, db_path: str = DEFAULT_DB, env: bool = False):
    if env or address is None and not os.path.exists(db_path):
        return load_from_env()
    return load_from_db(db_path, address)
