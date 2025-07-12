import csv


def merge_csvs():
    out_file = "/home/hugh/dev/finance/data/stocks/formatted.csv"

    with open(out_file, "w", newline="") as outfile:
        writer = csv.writer(outfile)

        # Write header using the specified format
        writer.writerow(
            [
                "Trade Date",
                "Instrument Code",
                "Market Code",
                "Quantity",
                "Price",
                "Transaction Type",
                "Exchange Rate (optional)",
                "Brokerage (optional)",
                "Brokerage Currency (optional)",
                "Comments (optional)",
            ]
        )

        merged = "/home/hugh/dev/finance/data/stocks/merged.csv"
        with open(merged, "r") as infile:
            reader = csv.reader(infile)
            next(
                reader, None
            )  # Skip header if it exists. Handles empty files gracefully

            for row in reader:
                # Assuming stake.csv structure is Date, Ticker, Action, Shares, Price, Total
                # Map stake.csv columns to the new header format. Fill unspecified columns with empty string
                date, ticker, action, shares, price, total = row
                writer.writerow(
                    [date, ticker, "ASX", shares, price, action, "", "", "", ""]
                )


if __name__ == "__main__":
    merge_csvs()
