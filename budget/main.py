from getpass import getpass
import time

from meatie import limit
from ubank import Client, Passkey

import sqlite3
import os
from dotenv import load_dotenv
import agent


class Transaction():
    def __init__(
        self,
        account_id: str,
        transaction_id: str,
        account_name: str,
        amount: int,
        time: int,
        vendor: str,
        category: str,
        location: str,
        description: str,
    ):
        self.account_id = account_id
        self.transaction_id = transaction_id
        self.account_name = account_name
        self.amount = amount
        self.time = time
        self.vendor = vendor
        self.category = category
        self.location = location
        self.description = description

    def to_tuple(self):
        return (
            self.account_id,
            self.transaction_id,
            self.account_name,
            self.amount,
            self.time,
            self.vendor,
            self.category,
            self.location,
            self.description,
        )


load_dotenv(".env")
HUGH_ACCOUNT_ID = os.environ.get("HUGH_ACCOUNT_ID")
BANK_ID = "1"
CUSTOMER_ID = os.environ.get("CUSTOMER_ID")
SQLITE_URL = os.environ.get("SQLITE_URL")
PASSKEY_PATH = os.environ.get("PASSKEY_PATH")
UBANK_PASS = os.environ.get("UBANK_PASS")
SHARED_SAVE_ACCOUNT_ID = os.environ.get("SHARED_SAVE_ACCOUNT_ID")
SHARED_SPEND_ACCOUNT_ID = os.environ.get("SHARED_SPEND_ACCOUNT_ID")
RENT_TABLE = "rent_payments"
TRANSACTION_TABLE = "transactions"

assert SQLITE_URL
assert CUSTOMER_ID
assert HUGH_ACCOUNT_ID
assert PASSKEY_PATH
assert UBANK_PASS
assert isinstance(SQLITE_URL, str)


con = sqlite3.connect(SQLITE_URL)
cur = con.cursor()

with open(PASSKEY_PATH, "rb") as f:
    passkey = Passkey.load(f, password=UBANK_PASS)


def get_plebs() -> dict[str, int]:
    res = cur.execute("SELECT name, discord_id FROM renter")
    plebs = res.fetchall()

    pleb_info = {}
    for pleb_name, pleb_id in plebs:
        pleb_info[pleb_name] = pleb_id
    print(f"pleb_names={pleb_info}")
    return pleb_info


def get_all_transaction_ids_from_table(
    table: str,
) -> set[str]:
    ids = cur.execute(f"SELECT transaction_id  FROM {table}").fetchall()
    ids = [x[0] for x in ids if x[0] != "" and x[0] != "backfilling data"]
    return set(ids)


def get_vendor_and_categories() -> dict[str, str]:
    vendors = cur.execute("SELECT vendor, category FROM transactions").fetchall()
    v = {}
    for vendor, category in vendors:
        v[vendor] = category
    return v


def store_pleb_transactions_in_db():
    pleb_info = get_plebs()
    all_transaction_ids = get_all_transaction_ids_from_table(RENT_TABLE)
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
                print(f"transaction had no legal name t={tran}")
                continue
            if not tran.value:
                continue

            pleb_name = tran.from_.legalName
            if pleb_name not in pleb_info:
                continue

            pleb_id = pleb_info[pleb_name]

            payment_in_cents = int(float(tran.value.amount) * 100)

            transactions_to_insert.append((pleb_id, payment_in_cents, now, tran.id))

        cur.executemany(
            f""" INSERT INTO {RENT_TABLE} VALUES (?, ?, ?, ?);""",
            transactions_to_insert,
        )
        con.commit()
        print(f"Saved {len(transactions_to_insert)} in db")


def get_all_bank_accounts():
    with Client(passkey) as client:
        banks = client.get_linked_banks()
        for b in banks.linkedBanks:
            for a in b.accounts:
                print(a.model_dump_json())


def store_saving_and_spend_transactions():
    all_transaction_ids = get_all_transaction_ids_from_table(TRANSACTION_TABLE)
    vendors = get_vendor_and_categories()
    with Client(passkey) as client:
        transactions_to_insert = []
        transactions = client.search_account_transactions(
            account_id=SHARED_SAVE_ACCOUNT_ID,
            bank_id=BANK_ID,
            customerId=CUSTOMER_ID,
        ).transactions
        transactions.extend(
            client.search_account_transactions(
                account_id=SHARED_SPEND_ACCOUNT_ID,
                bank_id=BANK_ID,
                customerId=CUSTOMER_ID,
            ).transactions
        )
        for tran in transactions:
            if tran.id in all_transaction_ids:
                continue
            if not tran.value:
                continue
            if not tran.posted:
                print(f"transaction not posted for id={tran.id}")
                continue

            source = (
                tran.from_.legalName
                if tran.from_ and tran.from_.legalName
                else "bonus interest"
            )

            payment_in_cents = int(float(tran.value.amount) * 100)

            tran_time = int(tran.posted.timestamp())

            if tran.lwc:
                tran_vendor = tran.lwc.get("merchantName", "")
                tran_location = tran.lwc.get("merchantLocation", "")
                transaction = Transaction(
                    tran.accountId,
                    tran.id,
                    source,
                    payment_in_cents,
                    tran_time,
                    tran_vendor,
                    "",
                    tran_location,
                    tran.shortDescription if tran.shortDescription else "",
                )
            else:
                transaction = Transaction(
                    tran.accountId,
                    tran.id,
                    source,
                    payment_in_cents,
                    tran_time,
                    "",
                    "Debit",
                    "",
                    "",
                )

            transactions_to_insert.append(transaction)

    # TODO
    categorize_transactions(vendors, transactions_to_insert)

    cur.executemany(
        f"""
        INSERT INTO {TRANSACTION_TABLE} VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?
        );
        """,
        [t.to_tuple() for t in transactions_to_insert],
    )
    con.commit()

def categorize_transactions(
    vendors: dict[str, str], transactions: list[Transaction]
) -> None:
    
    def _enforce_input_schema(
            t: Transaction
    ) -> agent.TransactionInput:
        return agent.TransactionInput(
            account_id=t.account_id,
            transaction_id=t.transaction_id,
            amount=t.amount,
            source=t.source,
            time=t.time,
            vendor=t.vendor,
            location=t.location,
            description=t.description,
        )

    transactions_to_categorize: list[agent.TransactionInput] = []
    for t in transactions:
        if t.category:
            continue
        if t.vendor in vendors:
            t.category = vendors[t.vendor]
            continue
        
        transactions_to_categorize.append(
            _enforce_input_schema(t)
        ) # Agent requires Pydantic base model as input

    if transactions_to_categorize:
        agent_output = agent.categorize_transactions(transactions_to_categorize)
        if agent_output:
            category = {e["transaction_id"]: e["category"] for e in agent_output}
            for t in transactions:
                if not t.category:
                    t.category = category[t.transaction_id]

if __name__ == "__main__":
    store_saving_and_spend_transactions()
    store_pleb_transactions_in_db()
