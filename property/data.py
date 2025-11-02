from datetime import datetime
import json
import sys
from typing import Optional
import psycopg2
import re


def parse_json():
    try:
        with open(f"results.json", "r") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(e)
        exit(1)

def extract_fields(sale: dict):
    listing_id = int(sale["listingId"])
    square_mtr = int(sale.get("landSize", {}).get("value", 0))

    display_price = sale.get("price", {}).get("display", 0)
    listing_price = parse_price(display_price)
    if listing_price == 0:
        print(f"Could not parse price, display='{display_price}'")
        return

    street_addr = sale["address"]["streetAddress"]
    if not street_addr:
        print("Could not find street address")
        return
    apt_num, street_num, street = split_address(street_addr) 
    postcode = int(sale["address"]["postCode"])

    if (general_features := sale["features"]["general"]):
        bedrooms = int(general_features["bedrooms"])
        bathrooms = int(general_features["bathrooms"])
        car_spaces = int(general_features["parkingSpaces"])
    elif (general_features := sale["generalFeatures"]):
        bedrooms = int(general_features["bedrooms"]["value"]) 
        bathrooms = int(general_features["bathrooms"]["value"])
        car_spaces = int(general_features["parkingSpaces"]["value"])
    else:
        bedrooms = 0
        bathrooms = 0
        car_spaces = 0

    # Convert to timestamp
    date_sold = sale["dateSold"]["value"]
    if not date_sold:
        print("Could not find date sold")
        return
    sell_time = int(datetime.strptime(date_sold, "%Y-%m-%d").timestamp())

    description = sale["description"]
    strata = parse_amount_or_zero(
        # Get everything from "strata" to the end of the number incl. commas
        regex_match=re.search(r"[sS]trata[^0-9]+?\d[0-9,]+", description)
    )
    water_rates = parse_amount_or_zero(
        regex_match=re.search(r"[wW]ater[^0-9]+?\d[0-9,]+", description)
    )
    council_rates = parse_amount_or_zero(
        regex_match=re.search(r"[cC]ouncil[^0-9]+?\d[0-9,]+", description)
    )
    return (
        apt_num,
        street_num,
        street,
        postcode,
        listing_price,
        square_mtr,
        sell_time,
        bedrooms,
        bathrooms,
        car_spaces,
        water_rates,
        council_rates,
        strata,
        listing_id
    )

def parse_amount_or_zero(regex_match: Optional[re.Match[str]]) -> int:
    if not regex_match:
        return 0
    text = regex_match.group()
    digits = []
    for c in text:
        if c.isnumeric():
            digits.append(c)
    return int("".join(digits))

# TODO Use better regex in case of oddities like "40/1 -19 Allen Street"
def split_address(text: str) -> tuple[str, str, str]:
    delimiter = text.find("/")

    # Anticipate strange formats
    if not delimiter: delimiter = text.find("\\")
    if not delimiter: delimiter = text.find("-")

    apt_num = text[:delimiter]

    space = text.find(" ", delimiter + 1)
    street_num = text[delimiter + 1 : space]
    street = text[space + 1 :]
    return (apt_num, street_num, street)

def parse_price(display: Optional[str]) -> int:
    if not display or "$" not in display:
        return 0
    match = re.search(r"\$?([\d,]+)", display)
    if match:
        price_str = match.group(1).replace(",", "")
        return int(price_str)
    return 0

def write_to_db(data: list[tuple], db_location: str):
    try:
        conn = psycopg2.connect(db_location)
        cur = conn.cursor()
    
        for vals_tuple in data:
            cur.execute(
                """
                INSERT INTO property_sale
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                vals_tuple
            )

        cur.close()
        conn.commit()
        conn.close()
    except Exception as e:
        print(e)

if __name__ == "__main__":
    sales = parse_json()
    data = []
    for s in sales:
        record = extract_fields(s)
        if record:
            print(record)
            data.append(record)
    write_to_db(data, sys.argv[1])
