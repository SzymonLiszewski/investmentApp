"""
Economic calendar fetcher using Alpha Vantage API.
"""
import csv
import requests
from typing import List

from base.infrastructure.interfaces.economic_calendar import EconomicCalendarFetcher


class NoOpEconomicCalendarFetcher(EconomicCalendarFetcher):
    """Fetcher that does not call any API. Returns empty lists. Use when API is disabled or key not set."""

    def get_earnings(self) -> List:
        return []

    def get_ipo(self) -> List:
        return []


class AlphaVantageEconomicCalendarFetcher(EconomicCalendarFetcher):
    """Fetch economic calendar data from Alpha Vantage. Requires api_key (e.g. from settings)."""

    def __init__(self, api_key: str):
        self._api_key = api_key

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
