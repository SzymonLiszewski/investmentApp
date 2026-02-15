"""
Economic calendar fetcher using Alpha Vantage API.
"""
import csv
import requests
from typing import List

from decouple import config

from base.infrastructure.interfaces.economic_calendar import EconomicCalendarFetcher

_ALPHAVANTAGE_API_KEY = config('ALPHAVANTAGE_API_KEY', default="default_api_key")


class AlphaVantageEconomicCalendarFetcher(EconomicCalendarFetcher):
    """Fetch economic calendar data from Alpha Vantage."""

    def __init__(self, api_key: str = None):
        self._api_key = api_key or _ALPHAVANTAGE_API_KEY

    def get_earnings(self) -> List:
        url = f'https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&horizon=3month&apikey={self._api_key}'
        with requests.Session() as s:
            download = s.get(url)
            decoded_content = download.content.decode('utf-8')
            cr = csv.reader(decoded_content.splitlines(), delimiter=',')
            my_list = list(cr)
            return my_list[1:]

    def get_ipo(self) -> List:
        url = f'https://www.alphavantage.co/query?function=IPO_CALENDAR&apikey={self._api_key}'
        with requests.Session() as s:
            download = s.get(url)
            decoded_content = download.content.decode('utf-8')
            cr = csv.reader(decoded_content.splitlines(), delimiter=',')
            my_list = list(cr)
            return my_list[1:]
