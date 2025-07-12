import csv

def merge_csvs():
    stake_file = '/home/hugh/dev/finance/data/stocks/stake.csv'
    asx_file = '/home/hugh/dev/finance/data/stocks/ASX-Movements-Hugh_Mandalidis-2019-03-29-2025-07-12.csv'
    merged_file = '/home/hugh/dev/finance/data/stocks/merged.csv'

    with open(merged_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        
        # Write header
        writer.writerow(['Date', 'Ticker', 'Action', 'Shares', 'Price', 'Total'])

        # Process stake.csv
        with open(stake_file, 'r') as infile:
            reader = csv.reader(infile)
            header = next(reader)  # Skip header
            for row in reader:
                writer.writerow(row)

        # Process ASX-Movements.csv
        with open(asx_file, 'r') as infile:
            reader = csv.reader(infile)
            header = next(reader)  # Skip header
            
            # Get column indices
            trade_date_idx = header.index('Trade Date')
            code_idx = header.index('Code')
            action_idx = header.index('Action')
            units_idx = header.index('Units')
            avg_price_idx = header.index('Average Price')
            total_idx = header.index('Total')

            for row in reader:
                # Handle cases where some rows might be empty or malformed
                if not row or not row[trade_date_idx]:
                    continue
                
                # Extract and format data
                date = row[trade_date_idx]
                ticker = row[code_idx]
                action = row[action_idx]
                shares = row[units_idx]
                price = row[avg_price_idx]
                total = row[total_idx]
                
                writer.writerow([date, ticker, action, shares, price, total])

if __name__ == '__main__':
    merge_csvs()
