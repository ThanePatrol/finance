import csv
from datetime import datetime


class Transaction:
    def __init__(
        self,
        time: int,
        desc: str,
        debit: int,
        credit: int,
        fro: str,
        to: str,
        category: str,
        tran_id: str,
    ):
        self.time = time
        self.desc = desc
        self.debit = debit
        self.credit = credit
        self.fro = fro
        self.to = to
        self.category = category
        self.tran_id = tran_id

    def __str__(self) -> str:
        return f"time={self.time}, desc={self.desc}, debit={self.debit}, credit={self.credit}, category={self.category}, id={self.tran_id}"


trans = []
with open("ubank_18_05_2025-18_11_2025.csv", "r") as f:
    reader = csv.reader(f, quotechar='"')
    i = 0
    for l in reader:
        if i == 0:
            i += 1
            continue
        print(l[0])
        as_ts = int(datetime.strptime(l[0], "%H:%M %d-%m-%y").timestamp())
        desc = l[1]
        debit = 0 if l[2] == "" else int(float(l[2].replace("$", "").replace(",", "")))
        credit = 0 if l[3] == "" else int(float(l[3].replace("$", "").replace(",", "")))
        fro = l[4]
        to = l[5]
        category = l[7]
        tran_id = l[9]
        t = Transaction(as_ts, desc, debit, credit, fro, to, category, tran_id)

        print(t)
        i += 1
