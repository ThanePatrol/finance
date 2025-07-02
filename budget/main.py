from getpass import getpass

from ubank import Client, Passkey

# Load passkey from file.
with open("passkey.txt", "rb") as f:
    passkey = Passkey.load(f, password=getpass("Enter ubank password: "))

# Print account balances.
with Client(passkey) as client:
    for account in client.get_linked_banks().linkedBanks[0].accounts:
        print(
            f"{account.label} ({account.type}): {account.balance.available} {account.balance.currency}"
        )
