# Skoda Metrics Scraper

This project is a simple Python script to fetch metrics for Skoda Enyaq from the [Skoda Connect](https://www.skoda-connect.com/) API and store the data to time series database.
The script uses [skodaconnect](https://github.com/skodaconnect/skodaconnect) project to communicate with the API.
The data is fetched once per day.
When combined with the charger metrics (not part of this script) it enables analyzing the power consumption of the car over time.

The following metrics are fetched:

- The time of the last update from the car
- The odometer reading in kilometers
- The state of charge (SoC) of the battery in percentage
- The estimated range in kilometers

Note: This project is meant for personal use, and is not guaranteed to work for anyone else.

## Usage

Credentials for the Skoda Connect portal and the VIN of the car must be passed in as environment variables.

- SKODA_USERNAME: Username for the portal.
- SKODA_PASSWORD: Password for the portal.
- SKODA_VIN: Vehicle identification number of the car registered in the portal.

Run the script:

```bash
python3 main.py
```

Or build as container image:

```bash
docker build -t quay.io/tsaarni/skoda-metrics-scraper:latest .
```

## Dependencies

Install dependencies with:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
