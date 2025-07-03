from getpass import getpass

from ubank import Client, Passkey

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv(".env")
HUGH_ACCOUNT_ID = os.environ.get("HUGH_ACCOUNT_ID")
BANK_ID = "1"
CUSTOMER_ID = os.environ.get("CUSTOMER_ID")
SQLITE_URL = os.environ.get("SQLITE_URL")
PASSKEY_PATH = os.environ.get("PASSKEY_PATH")

assert SQLITE_URL
assert CUSTOMER_ID
assert HUGH_ACCOUNT_ID
assert PASSKEY_PATH

con = sqlite3.connect(SQLITE_URL)
cur = con.cursor()

cur.execute("SELECT * FROM rent_payments")
rows = cur.fetchall()
print(rows)


# Load passkey from file.
with open(PASSKEY_PATH, "rb") as f:
    passkey = Passkey.load(f, password=getpass("Enter ubank password: "))

# Print account balances.
with Client(passkey) as client:
    for account in client.get_linked_banks().linkedBanks[0].accounts:
        print(
            f"{account.label} ({account.type}): {account.balance.available} {account.balance.currency}"
        )

    for tran in client.search_account_transactions(
        account_id=HUGH_ACCOUNT_ID,
        bank_id=BANK_ID,
        customerId=CUSTOMER_ID,
    ).transactions:
        print(tran)
