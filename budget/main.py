from abc import ABC, abstractmethod
import argparse
import csv
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from enum import Enum
import os
import sqlite3
from hashlib import sha512


load_dotenv(".env")
TRANSACTION_TABLE = "transactions"
VALID_USERS = [u.strip() for u in os.environ.get("USERS", "shared").split(",") if u.strip()]
SQLITE_URL = os.environ.get("SQLITE_URL")


class Transaction:
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
        balance: str,
        user: str,
        original_record: str
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
        self.balance = balance
        self.user = user
        self.original_record = original_record
        self.hash = sha512(
            "|".join(
                str(field) if field else "!empty!" for field in [
                self.account_id, self.transaction_id, self.account_name,
                self.amount, self.time, self.vendor, self.category,
                self.location, self.description, self.balance, self.user]
            ).encode("utf-8")).hexdigest()

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
            self.balance,
            self.user,
            self.original_record,
            self.hash
        )

    def __str__(self):
        return ", ".join(f"{key}={value}" for key, value in self.__dict__.items())

class DataSource(Enum):
    UBANK_CSV = "ubank"
    NP_CSV    = "npbs"
    MB_CSV    = "macbank"

    def __str__(self):
        return self.value

class BaseTransactionParser(ABC):
    """Abstract base class for bank specific parsers"""
    
    @abstractmethod
    def process_transactions(
        self, file_path: str, user: Optional[str]
    ) -> list[Transaction]:
        pass

class UbankParser(BaseTransactionParser):
    def process_transactions(
        self, file_path: str, user: Optional[str]
    ) -> list[Transaction]:
        expected_fields = ["Date","Description","Debit","Credit","Balance"]
        expected_date_format = "%d %b %Y"
        transactions = []
        with open(file_path, mode="r") as f:
            reader = csv.DictReader(f)
            for record in reader:
                try:
                    if "Debit" in record:
                        amount_in_cents = get_amount_in_cents(record["Debit"]) * -1
                    elif "Credit" in record:
                        amount_in_cents = get_amount_in_cents(record["Credit"])
                    else:
                        print(f"Failed to find 'Debit' or 'Credit' amount in transaction={record}")
                        continue
    
                    if not (date := record.get("Date")):
                        print(f"Failed to find 'Date' in transaction={record}")
                    assert isinstance(date, str)
    
                    transactions.append(
                        Transaction(
                            account_id="",
                            transaction_id="",
                            account_name="",
                            amount=amount_in_cents,
                            time=get_date_as_timestamp(date, expected_date_format),
                            vendor="",
                            category="",
                            location="",
                            description=record.get("Description", ""),
                            balance=record.get("Balance", ""),
                            user=user if user else "",
                            original_record=str(record)
                        )
                    )
    
                except KeyError as e:
                    print(f"Failed to find '{e}' among expected fields: {expected_fields}")
                    exit(1)
    
        return transactions

class MbParser(BaseTransactionParser):
    def process_transactions(
        self, file_path: str, user: Optional[str]
    ) -> list[Transaction]:
        expected_fields = ["Transaction Date","Details","Account","Category","Subcategory","Tags","Notes","Debit","Credit","Balance","Original Description"]
        expected_date_format = "%d %b %Y"
        transactions = []
        with open(file_path, mode="r") as f:
            reader = csv.DictReader(f)
            for record in reader:
                try:
                    if record.get("Account") != "My spend":
                        print(f"Not associated with spend account, skipping transaction={record}")
    
                    if "Debit" in record:
                        amount_in_cents = get_amount_in_cents(record["Debit"]) * -1
                    elif "Credit" in record:
                        amount_in_cents = get_amount_in_cents(record["Credit"])
                    else:
                        print(f"Failed to find 'Debit' or 'Credit' amount in transaction={record}")
                        continue
    
                    if not (date := record.get("Transaction Date")):
                        print(f"Failed to find 'Transaction Date' in transaction={record}")
                    assert isinstance(date, str)
    
                    transactions.append(
                        Transaction(
                            account_id="",
                            transaction_id="",
                            account_name="",
                            amount=amount_in_cents,
                            time=get_date_as_timestamp(date, expected_date_format),
                            vendor="",
                            category=record.get("Category", ""),
                            location="",
                            description=record.get("Details", record.get("Original Description", "")),
                            balance=record.get("Balance", ""),
                            user=user if user else "",
                            original_record=str(record)
                        )
                    )
    
                except KeyError as e:
                    print(f"Failed to find '{e}' among expected fields: {expected_fields}")
                    exit(1)
    
        return transactions

class NpParser(BaseTransactionParser):
    def process_transactions(
        self, file_path: str, user: Optional[str]
    ) -> list[Transaction]:
        expected_fields = ["Date","Description","Amount","Balance"]
        expected_date_format = "%d/%m/%Y"
        transactions = []
        date_idx = desc_idx = amt_idx = bal_idx = None
        with open(file_path, mode="r") as f:
            reader = csv.reader(f)
    
            for record in reader:
                try:
                    # Skip bs in stupid csv-not-csv
                    if date_idx is None:
                        if all([f in record for f in expected_fields]):
                            date_idx = record.index("Date")
                            desc_idx = record.index("Description")
                            amt_idx = record.index("Amount")
                            bal_idx = record.index("Balance")
                        continue
                    if not (desc_idx and amt_idx and bal_idx):
                        print("Failed to find expected fields")
                        exit(1)
    
                    if len(record) <= max(date_idx, desc_idx, amt_idx):
                        print(f"Skipping malformed line={record}")
                        continue
    
                    date_val = record[date_idx]
                    desc_val = record[desc_idx]
                    amt_val = record[amt_idx]
                    bal_val = record[bal_idx]
    
                    if amt_val:
                        amount_in_cents = get_amount_in_cents(amt_val)
                    else:
                        print(f"Failed to find 'Amount' in transaction={record}")
                        continue
    
                    if not date_val:
                        print(f"Failed to find 'Date' in transaction={record}")
    
                    transactions.append(
                        Transaction(
                            account_id="",
                            transaction_id="",
                            account_name="",
                            amount=amount_in_cents,
                            time=get_date_as_timestamp(date_val, expected_date_format),
                            vendor="",
                            category="",
                            location="",
                            description=desc_val,
                            balance=bal_val,
                            user=user if user else "shared",
                            original_record=str(record)
                        )
                    )
    
                except KeyError as e:
                    print(f"Failed to find '{e}' among expected fields: {expected_fields}")
                    exit(1)
    
        return transactions

# Helpers

def get_amount_in_cents(dollar_amount_string: str) -> int:
    amt = dollar_amount_string.strip().replace("$", "").replace(",", "")
    if "." in amt:
        dollars, cents = amt.split(".", 1)
        cents = (cents + "00")[:2]
        return int(dollars + cents)
    else:
        return int(amt + "00")

def get_date_as_timestamp(date: str, fmt: str) -> int:
    try:
        dt = datetime.strptime(date, fmt)
        return int(dt.timestamp())
    except Exception:
        print(f"Failed to convert date={date} according to expected format={fmt}")
        exit(1)

def get_parser_for_datasource(source: DataSource) -> BaseTransactionParser:
    try:
        match source:
            case DataSource.UBANK_CSV:
                return UbankParser()
            case DataSource.MB_CSV:
                return MbParser()
            case DataSource.NP_CSV:
                return NpParser()

    except KeyError:
        raise ValueError(f"No parser implemented for unknown datasource={source}")

def insert_bulk_transactions(transactions: list[Transaction]) -> None:
    if not transactions:
        return

    # Define time interval which transactions span
    min_time = min(transactions, key=lambda t: t.time).time
    max_time = max(transactions, key=lambda t: t.time).time
    
    # Define existing transactions in table, for which this run should not add duplicates
    cur.execute(
        f"SELECT hash FROM {TRANSACTION_TABLE} WHERE time >= ? AND time <= ?",
        (min_time, max_time)
    )
    rows = cur.fetchall()
    # Actual value is first in tuple
    hashes_to_not_duplicate = set([r[0] for r in rows])
    transactions_to_insert = [t.to_tuple() for t in transactions if t.hash not in hashes_to_not_duplicate]

    if (transactions_count := len(transactions_to_insert)) > 0:
        print(f"About to insert {transactions_count} unique records out of {len(transactions)} total records...")
    else:
        print("No new transactions to insert.")
        return

    cur.executemany(
        f"""
        INSERT INTO {TRANSACTION_TABLE} VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        );
        """,
        transactions_to_insert
    )
    con.commit()

def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read CSVs containing historical transactions"
    )

    file_or_directory_group = parser.add_mutually_exclusive_group(required=True)
    file_or_directory_group.add_argument(
        "-f",
        "--file",
        help="file paths to read"
    )
    file_or_directory_group.add_argument(
        "-d",
        "--directory",
        help=f"directory containing subdirectories named like: {[e.value for e in DataSource]}"
    )

    parser.add_argument(
        "-s",
        "--src",
        type=DataSource,
        choices=list(DataSource),
        help="type of transaction data source (required if using -f)"
    )
    parser.add_argument(
        "-u",
        "--user",
        type=str,
        choices=VALID_USERS,
        help="user to record on db save (hint: set comma-delimited USERS in .env)"
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="set if you do not want to insert to db, just print"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()

    # Parse csv
    transactions_to_insert = []

    # TODO Default user
    if args.directory:
        for source in DataSource:
            dir_path = os.path.join(args.directory, source.value)
            if os.path.isdir(dir_path):
                if args.user is None:
                    if source == DataSource.NP_CSV:
                        print("No user provided, defaulting to 'shared' for datasource=npbs")
                    else:
                        print(f"Skipping directory '{source.value}': --user must be provided unless --src=npbs")
                        continue
                
                for filename in os.listdir(dir_path):
                    if filename.lower().endswith(".csv"):
                        filepath = os.path.join(dir_path, filename)
                        transactions_to_insert.extend(
                            get_parser_for_datasource(source).process_transactions(filepath, args.user)
                        )
    else:
        # Validation
        if args.user is None:
            if args.src == DataSource.NP_CSV:
                print("No user provided, defaulting to 'shared' for datasource=npbs")
            else:
                print("--user must be provided unless --src=npbs")
                exit(1)
        transactions_to_insert = get_parser_for_datasource(args.src).process_transactions(file_path=args.file, user=args.user)

    # Persist to db
    if args.dry_run:
        for t in transactions_to_insert:
            print(t)
    else:
        if not SQLITE_URL:
            raise ValueError("Failed to find SQLITE_URL in .env")
    
        con = sqlite3.connect(SQLITE_URL)
        cur = con.cursor()
        try:
            insert_bulk_transactions(transactions_to_insert)
        finally:
            cur.close()
            con.close()
