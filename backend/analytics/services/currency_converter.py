"""
Currency converter for converting asset values between currencies.
"""
from typing import Optional
from decimal import Decimal
from forex_python.converter import CurrencyRates, RatesNotAvailableError


class CurrencyConverter:
    """
    Handles currency conversion using forex-python.
    """

    def __init__(self):
        """Initialize the currency converter."""
        self.currency_rates = CurrencyRates()
        self._cache = {}

    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str
    ) -> Optional[Decimal]:
        """
        Convert an amount from one currency to another.

        Args:
            amount: Amount to convert
            from_currency: Source currency code (e.g., 'USD')
            to_currency: Target currency code (e.g., 'PLN')

        Returns:
            Converted amount or None if conversion fails
        """
        # If currencies are the same, no conversion needed
        if from_currency == to_currency:
            return amount

        try:
            # Create cache key
            cache_key = f"{from_currency}_{to_currency}"
            
            # Get exchange rate
            if cache_key not in self._cache:
                rate = self.currency_rates.get_rate(from_currency, to_currency)
                self._cache[cache_key] = Decimal(str(rate))
            
            exchange_rate = self._cache[cache_key]
            converted_amount = amount * exchange_rate

            return converted_amount

        except (RatesNotAvailableError, Exception) as e:
            # Log error in production
            print(f"Error converting {from_currency} to {to_currency}: {str(e)}")
            return None

    def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[Decimal]:
        """
        Get the exchange rate between two currencies.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code

        Returns:
            Exchange rate or None if not available
        """
        if from_currency == to_currency:
            return Decimal('1.0')

        try:
            rate = self.currency_rates.get_rate(from_currency, to_currency)
            return Decimal(str(rate))
        except (RatesNotAvailableError, Exception) as e:
            print(f"Error getting rate {from_currency} to {to_currency}: {str(e)}")
            return None

    def clear_cache(self):
        """Clear the exchange rate cache."""
        self._cache.clear()
