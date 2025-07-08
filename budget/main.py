from getpass import getpass
import time

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
UBANK_PASS = os.environ.get("UBANK_PASS")

assert SQLITE_URL
assert CUSTOMER_ID
assert HUGH_ACCOUNT_ID
assert PASSKEY_PATH
assert UBANK_PASS

con = sqlite3.connect(SQLITE_URL)
cur = con.cursor()

res = cur.execute("SELECT * FROM renter")
plebs = res.fetchall()
print(plebs)

pleb_info = {}
for pleb_name, pleb_id in plebs:
    pleb_info[pleb_name] = pleb_id

print(f"pleb_names={pleb_info}")

all_transaction_ids = set(
    cur.execute("SELECT transaction_id FROM rent_payments").fetchall()
)

# Load passkey from file.
with open(PASSKEY_PATH, "rb") as f:
    passkey = Passkey.load(f, password=UBANK_PASS)


# Print account balances.
with Client(passkey) as client:
    transactions_to_insert = []
    now = int(time.time())
    for tran in client.search_account_transactions(
        account_id=HUGH_ACCOUNT_ID,
        bank_id=BANK_ID,
        customerId=CUSTOMER_ID,
    ).transactions:
        if tran.id in all_transaction_ids:
            continue
        if not tran.from_ or not tran.from_.legalName:
            print("transaction had no legal name")
            continue
        if not tran.value:
            print(f"no fucking transaction value? {tran}")
            continue

        pleb_name = tran.from_.legalName
        if pleb_name not in pleb_info:
            continue

        pleb_id = pleb_info[pleb_name]

        payment_in_cents = int(float(tran.value.amount) * 100)

        transactions_to_insert.append((pleb_id, payment_in_cents, now, tran.id))
        print(f"about to save transaction {(pleb_id, payment_in_cents, now, tran.id)}")

    cur.executemany(
        """
    INSERT INTO rent_payments VALUES (
        ?, ?, ?, ?
    );
    """,
        transactions_to_insert,
    )
    con.commit()
