from base.infrastructure.interfaces import (
    StockDataFetcher,
    CryptoDataFetcher,
    FXDataFetcher,
    NewsFetcher,
    EconomicCalendarFetcher,
)

from base.services.stock_data_service import get_stock_data
from base.services.economic_calendar_service import get_earnings, get_ipo

__all__ = [
    'StockDataFetcher',
    'CryptoDataFetcher',
    'FXDataFetcher',
    'NewsFetcher',
    'EconomicCalendarFetcher',
    'get_default_stock_fetcher',
    'get_default_crypto_fetcher',
    'get_default_fx_fetcher',
    'get_default_news_fetchers',
    'get_default_economic_calendar_fetcher',
    'get_stock_data',
    'get_earnings',
    'get_ipo',
]


def get_default_stock_fetcher():
    """Factory: return the default StockDataFetcher implementation."""
    from django.conf import settings
    if getattr(settings, 'USE_MOCK_DATA_FETCHER', False):
        from base.infrastructure.providers.mock_fetchers import MockStockDataFetcher
        return MockStockDataFetcher()
    from base.infrastructure.providers.yfinance_fetchers import YfinanceStockDataFetcher
    return YfinanceStockDataFetcher()


def get_default_crypto_fetcher():
    """Factory: return the default CryptoDataFetcher implementation."""
    from django.conf import settings
    if getattr(settings, 'USE_MOCK_DATA_FETCHER', False):
        from base.infrastructure.providers.mock_fetchers import MockCryptoDataFetcher
        return MockCryptoDataFetcher()
    from base.infrastructure.providers.yfinance_fetchers import YfinanceCryptoDataFetcher
    return YfinanceCryptoDataFetcher()


def get_default_fx_fetcher():
    """Factory: return the default FXDataFetcher implementation."""
    from django.conf import settings
    if getattr(settings, 'USE_MOCK_DATA_FETCHER', False):
        from base.infrastructure.providers.mock_fetchers import MockFXDataFetcher
        return MockFXDataFetcher()
    from base.infrastructure.providers.yfinance_fetchers import YfinanceFXDataFetcher
    return YfinanceFXDataFetcher()


def get_default_news_fetchers():
    """Factory: return a list of default NewsFetcher implementations. Yahoo/NewsData only when enabled."""
    from django.conf import settings
    from base.infrastructure.providers.news_fetchers import YahooNewsFetcher, NewsDataNewsFetcher
    fetchers = []
    if getattr(settings, 'YAHOO_NEWS_API_ENABLED', True):
        fetchers.append(YahooNewsFetcher())
    if getattr(settings, 'NEWSDATA_NEWS_API_ENABLED', False):
        fetchers.append(NewsDataNewsFetcher(api_key=settings.NEWSDATA_API_KEY))
    return fetchers


def get_default_economic_calendar_fetcher():
    """Factory: return EconomicCalendarFetcher. No-op when API key missing or USE_ECONOMIC_CALENDAR_API disabled."""
    from django.conf import settings
    from base.infrastructure.providers.economic_calendar import (
        NoOpEconomicCalendarFetcher,
        AlphaVantageEconomicCalendarFetcher,
    )
    if not getattr(settings, 'ECONOMIC_CALENDAR_API_ENABLED', False):
        return NoOpEconomicCalendarFetcher()
    return AlphaVantageEconomicCalendarFetcher(api_key=settings.ALPHAVANTAGE_API_KEY)
