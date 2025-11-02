# TODO:
- Model house price and potential return over x years given stamp duty, avg percent price for suburb (ideally more granular - block of apts), purchase price
- Breakdown to per sqm would be useful
- Ability to model repayments with mortgage + add additional repayments

# Requirements
- Predicted Return over x years
- Per property or per sqm
-

## Gross return of property?
- Return = sell price - purchase price
- sell price = purchase price + modelled return
- modeled return = avg return of postcode in percent per year?

## What to store
- All homes in pyrmont in apts
- Init price + sell price + years
- sqm
- Last 20 years?

```sql
CREATE TABLE property_sale (
    apt_num TEXT,
    street_num TEXT,
    street TEXT,
    postcode INTEGER,
    listing_price INTEGER,
    square_mtr INTEGER,
    sell_time INTEGER, --unix timestamp
    bedrooms INTEGER,
    bathrooms INTEGER,
    car_spaces INTEGER,
    water_rates INTEGER,
    council_rates INTEGER,
    strata INTEGER
);

```
