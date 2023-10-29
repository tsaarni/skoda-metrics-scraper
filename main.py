#!/bin/env python3

import asyncio
import datetime
import logging
import os

from aiohttp import ClientSession
from skodaconnect import Connection

# Scraping time is 5:00 every day.
schedule = datetime.time(5, 0, 0)

# Configure logging to stdout.
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root_logger.addHandler(handler)


class SkodaConnectScraper(object):

    def __init__(self, username, password, vin, api_debug=False):
        self.username = username
        self.password = password
        self.vin = vin
        self.api_debug = api_debug
        self.log = logging.getLogger('Scraper')

    async def start(self):
        self.log.debug(f'Starting scraper: api_debug={self.api_debug}')

        # Schedule periodic scraping.
        asyncio.create_task(self.scrape_periodically())

        # Do not exit, keep running until killed.
        await asyncio.Event().wait()

    async def scrape_periodically(self):
        # Scrape once immediately and then schedule next scrape by waiting until wake up time.
        while True:
            try:
                await self.scrape()
            except Exception as e:
                self.log.error(f'Error scraping: {e}')

            # TODO: If scraping fails, retry after a short delay instead of waiting until next scheduled time.

            # Schedule next scrape.
            now = datetime.datetime.now()
            if now.time() >= schedule:
                # If it's past scheduled time, then schedule for tomorrow.
                tomorrow = now + datetime.timedelta(days=1)
                dt = datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, schedule.hour, schedule.minute, schedule.second)
            else:
                # If it's before scheduled time, schedule for today.
                dt = datetime.datetime(now.year, now.month, now.day, schedule.hour, schedule.minute, schedule.second)

            seconds_until_next_scrape = (dt - now).total_seconds()
            self.log.debug(f'Sleeping until {dt}: {seconds_until_next_scrape} seconds')
            await asyncio.sleep(seconds_until_next_scrape)

    async def scrape(self):
        # Create HTTP session.
        async with ClientSession() as session:
            # Create connection to Skoda Connect API.
            conn = Connection(session, self.username, self.password, self.api_debug)

            # Login with credentials.
            self.log.debug(f'Logging in: username={self.username} password={"<redacted>" if self.password else "None"}')
            await conn.doLogin()

            # Get vehicle status.
            self.log.debug(f'Getting vehicle status: vin={self.vin}')
            res_vehicle_status = await conn.getVehicleStatus(self.vin)
            self.log.debug(f'Result: {res_vehicle_status}')

            # Get charging status.
            self.log.debug(f'Getting changing status: vin={self.vin}')
            res_charging_status = await conn.getCharging(self.vin)
            self.log.debug(f'Result: {res_charging_status}')

            # Create record of vehicle data to send to timeseries database.
            vehicle_data = {
                'captured_at': res_vehicle_status['vehicle_remote']['capturedAt'],
                'odometer_km': res_vehicle_status['vehicle_remote']['mileageInKm'],
                'state_of_charge_percent': res_charging_status['battery']['stateOfChargeInPercent'],
                'range_km': res_charging_status['battery']['cruisingRangeElectricInMeters'] / 1000,
            }

            self.log.info(f'Vehicle data: {vehicle_data}')

            # TODO: Send data to timeseries database.


async def main():
    logger = logging.getLogger('main')

    username = os.environ.get('SKODA_USERNAME')
    password = os.environ.get('SKODA_PASSWORD')
    vin = os.environ.get('SKODA_VIN')

    if not username or not password:
        logger.error('No SKODA_USERNAME or SKODA_PASSWORD set in environment variables')
        exit(1)
    if not vin:
        logger.error('No SKODA_VIN set in environment variables')
        exit(1)

    # Debug for Skoda Connect API calls.
    debug = True if os.environ.get('DEBUG', 'false').lower() == 'true' else False

    await SkodaConnectScraper(username, password, vin, debug).start()

if __name__ == '__main__':
    asyncio.run(main())
