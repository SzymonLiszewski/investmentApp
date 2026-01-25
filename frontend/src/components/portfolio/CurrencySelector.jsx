import React, { useState, useEffect } from 'react';
import './CurrencySelector.css';

const CURRENCIES = [
  { code: 'PLN', name: 'Polish Złoty', symbol: 'zł', flag: '🇵🇱' },
  { code: 'USD', name: 'US Dollar', symbol: '$', flag: '🇺🇸' },
  { code: 'EUR', name: 'Euro', symbol: '€', flag: '🇪🇺' },
  { code: 'GBP', name: 'British Pound', symbol: '£', flag: '🇬🇧' },
  { code: 'CHF', name: 'Swiss Franc', symbol: 'CHF', flag: '🇨🇭' },
  { code: 'JPY', name: 'Japanese Yen', symbol: '¥', flag: '🇯🇵' },
  { code: 'CAD', name: 'Canadian Dollar', symbol: 'C$', flag: '🇨🇦' },
];

function CurrencySelector({ onCurrencyChange }) {
  const [selectedCurrency, setSelectedCurrency] = useState('PLN');
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    // Load preferred currency from localStorage
    const savedCurrency = localStorage.getItem('preferredCurrency');
    if (savedCurrency) {
      setSelectedCurrency(savedCurrency);
    }
  }, []);

  const handleCurrencySelect = (currencyCode) => {
    setSelectedCurrency(currencyCode);
    localStorage.setItem('preferredCurrency', currencyCode);
    setIsOpen(false);
    
    // Notify parent component
    if (onCurrencyChange) {
      onCurrencyChange(currencyCode);
    }
  };

  const selectedCurrencyData = CURRENCIES.find(c => c.code === selectedCurrency) || CURRENCIES[0];

  return (
    <div className="currency-selector">
      <label className="currency-label">Portfolio Currency:</label>
      <div className="currency-dropdown">
        <button 
          className="currency-button"
          onClick={() => setIsOpen(!isOpen)}
          aria-label="Select currency"
        >
          <span className="currency-flag">{selectedCurrencyData.flag}</span>
          <span className="currency-code">{selectedCurrencyData.code}</span>
          <span className="currency-symbol">({selectedCurrencyData.symbol})</span>
          <span className={`dropdown-arrow ${isOpen ? 'open' : ''}`}>▼</span>
        </button>
        
        {isOpen && (
          <div className="currency-menu">
            {CURRENCIES.map((currency) => (
              <button
                key={currency.code}
                className={`currency-option ${currency.code === selectedCurrency ? 'selected' : ''}`}
                onClick={() => handleCurrencySelect(currency.code)}
              >
                <span className="currency-flag">{currency.flag}</span>
                <div className="currency-info">
                  <span className="currency-code-option">{currency.code}</span>
                  <span className="currency-name">{currency.name}</span>
                </div>
                <span className="currency-symbol-option">{currency.symbol}</span>
                {currency.code === selectedCurrency && (
                  <span className="checkmark">✓</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default CurrencySelector;
