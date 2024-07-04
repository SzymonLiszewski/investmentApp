import React, { useState, useEffect, useRef } from 'react';
import './styles/SearchBox.css'; // Stylizacja CSS

const SearchBox = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expanded, setExpanded] = useState(false); //expanded - show suggestions
  const [suggestions, setSuggestions] = useState([]);
  const [allStocks, setAllStocks] = useState([]);
  const [selectedSuggestions, setSelectedSuggestions] = useState([]);
  const searchBoxRef = useRef(null);

  const handleInputChange = (event) => {
    const value = event.target.value;
    setSearchTerm(value);
    if (value.length > 0) {
      setSuggestions(allStocks.filter(stock => stock.name.toLowerCase().includes(value.toLowerCase())));
    } else {
      setSuggestions([]);
    }
  };

  useEffect(() => {
    // starting values of suggestions
    setSuggestions(allStocks.slice(0, 5)); // displaying first 5 suggestions
  }, [allStocks])

  const handleInputClick = () => {
    setExpanded(!expanded); 
  };

  const handleSuggestionClick = (value) => {
    setSearchTerm(value.name);
    setExpanded(false);
};

  const handleCollapse = () => {
    setExpanded(false);
  };

  const handleClickOutside = (event) => {
    if (searchBoxRef.current && !searchBoxRef.current.contains(event.target)) {
        console.log("Clicked outside");
        handleCollapse();
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Escape") {
      handleCollapse();
    }
  };

  useEffect(() => {
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

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

  return (
    <div className={`search-box ${expanded ? 'expanded' : ''}`}>
      <input
        type="text"
        placeholder="Enter stock name..."
        value={searchTerm}
        onChange={handleInputChange}
        onClick={handleInputClick}
      />
      {suggestions.length > 0 && (
        <div className="suggestions">
          {suggestions.map(suggestion => (
            <div
              key={suggestion.id}
              className="suggestion-item"
              onClick={() => handleSuggestionClick(suggestion)}
            >
              {suggestion.name}
            </div>
          ))}
        </div>
      )}
      {selectedSuggestions.length > 0 && (
        <div className="selected-suggestions">
          <h4>Selected Suggestions:</h4>
          {selectedSuggestions.map(suggestion => (
            <div key={suggestion.id} className="selected-suggestion-item">
              {suggestion.name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchBox;
