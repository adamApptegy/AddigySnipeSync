# AddigySnipeSync

## Installation

`pip3 install -r requirements`

## Configuration

Copy the `.env.example` file to `.env` and fill out the required API keys

### Syncing purchase date and order number

You can optionally choose to sync purchase date or order number by adding a file called `purchase-dates.csv` and `order-number.csv`

The `purchase-dates.csv` file should be in the format:
```
Serial, purchase date
C02XXXXX,2022-09-20
```

The `order-number.csv` file should be in the format:
```
Serial,order number
C02XXXXX,12345678
```

## Running

`python3 AddigySnipeSync.py`
