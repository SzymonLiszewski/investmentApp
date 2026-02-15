from base.infrastructure.interfaces import (
    StockDataFetcher,
    CryptoDataFetcher,
    FXDataFetcher,
    NewsFetcher,
    EconomicCalendarFetcher,
)

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
    """Factory: return a list of default NewsFetcher implementations."""
    from base.infrastructure.providers.news_fetchers import YahooNewsFetcher, NewsDataNewsFetcher
    return [YahooNewsFetcher(), NewsDataNewsFetcher()]


def get_default_economic_calendar_fetcher():
    """Factory: return the default EconomicCalendarFetcher implementation."""
    from base.infrastructure.providers.economic_calendar import AlphaVantageEconomicCalendarFetcher
    return AlphaVantageEconomicCalendarFetcher()
