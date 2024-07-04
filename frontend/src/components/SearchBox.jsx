import React, { useState, useEffect, useRef } from 'react';
import './styles/SearchBox.css'; // Stylizacja CSS

const SearchBox = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [expanded, setExpanded] = useState(false); // Stan, który określa, czy pole wyszukiwania jest rozwinięte
  const searchBoxRef = useRef(null);

  const handleInputChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleInputClick = () => {
    setExpanded(!expanded); // Przełączanie stanu po kliknięciu
  };

  const handleSuggestionClick = (value) => {
    setSearchTerm(value);
    setExpanded(false); // Po wybraniu sugestii, zwijamy pasek wyszukiwania
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

  return (
    <div className={`search-box ${expanded ? 'expanded' : ''}`}>
      <input
        type="text"
        placeholder="Enter stock name..."
        value={searchTerm}
        onChange={handleInputChange}
        onClick={handleInputClick}
      />
      <div className="suggestions">
        {[
          'JavaScript',
          'React',
          'Node.js',
          'HTML',
          'CSS',
          'TypeScript'
        ].map((suggestion, index) => (
          <div
            key={index}
            className="suggestion"
            onClick={() => handleSuggestionClick(suggestion)}
          >
            {suggestion}
          </div>
        ))}
      </div>
    </div>
  );
};

export default SearchBox;
