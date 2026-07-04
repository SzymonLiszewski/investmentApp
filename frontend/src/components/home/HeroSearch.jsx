/* eslint-disable react/prop-types */
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './HeroSearch.css';

const MAX_SUGGESTIONS = 8;

// variant="compact" renders a smaller field without the Analyze button
// (used in the stock-page watchlist row).
const HeroSearch = ({
  variant = 'hero',
  placeholder = 'Search any stock — e.g. AAPL, Tesla…',
  inputRef,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [allStocks, setAllStocks] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/test_stock_names.json');
        const data = await response.json();
        setAllStocks(data);
      } catch (error) {
        console.error('Error loading stock data:', error);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (rootRef.current && !rootRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const filterStocks = (value) => {
    const query = value.trim().toLowerCase();
    if (!query) return [];
    return allStocks
      .filter(
        (stock) =>
          stock.name.toLowerCase().includes(query) ||
          stock.Symbol.toLowerCase().startsWith(query)
      )
      .slice(0, MAX_SUGGESTIONS);
  };

  const handleInputChange = (event) => {
    const value = event.target.value;
    setSearchTerm(value);
    setSuggestions(filterStocks(value));
    setOpen(true);
  };

  const goToSymbol = (symbol) => {
    setOpen(false);
    navigate(`/analysis2/${symbol.trim().toUpperCase()}`);
  };

  const handleAnalyze = (event) => {
    event.preventDefault();
    const query = searchTerm.trim();
    if (!query) return;
    const exact = allStocks.find(
      (stock) => stock.Symbol.toLowerCase() === query.toLowerCase()
    );
    if (exact) {
      goToSymbol(exact.Symbol);
    } else if (suggestions.length > 0) {
      goToSymbol(suggestions[0].Symbol);
    } else {
      goToSymbol(query);
    }
  };

  return (
    <form
      className={`hero-search${variant === 'compact' ? ' hero-search-compact' : ''}`}
      ref={rootRef}
      onSubmit={handleAnalyze}
    >
      <div className="hero-search-row">
        <div className="hero-search-field">
          <svg
            className="hero-search-icon"
            viewBox="0 0 20 20"
            width="16"
            height="16"
            aria-hidden="true"
          >
            <circle cx="9" cy="9" r="6.5" fill="none" stroke="currentColor" strokeWidth="2" />
            <line x1="13.8" y1="13.8" x2="18" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <input
            type="text"
            ref={inputRef}
            value={searchTerm}
            onChange={handleInputChange}
            onFocus={() => setOpen(true)}
            placeholder={placeholder}
            aria-label="Search any stock"
          />
        </div>
        {variant !== 'compact' && (
          <button type="submit" className="hero-search-button">Analyze</button>
        )}
      </div>
      {open && suggestions.length > 0 && (
        <div className="hero-search-suggestions">
          {suggestions.map((stock) => (
            <button
              key={stock.Symbol}
              type="button"
              className="hero-search-suggestion"
              onClick={() => goToSymbol(stock.Symbol)}
            >
              <span className="hero-search-suggestion-symbol">{stock.Symbol}</span>
              <span className="hero-search-suggestion-name">{stock.name}</span>
            </button>
          ))}
        </div>
      )}
    </form>
  );
};

export default HeroSearch;
