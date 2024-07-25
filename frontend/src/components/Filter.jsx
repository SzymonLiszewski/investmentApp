import React from 'react';

const Filter = ({ setFilters }) => {
  const handleCategoryChange = (event) => {
    const categories = Array.from(event.target.selectedOptions, option => option.value);
    setFilters(prev => ({ ...prev, categories }));
  };

  const handleStockChange = (event) => {
    const stocks = Array.from(event.target.selectedOptions, option => option.value);
    setFilters(prev => ({ ...prev, stocks }));
  };

  return (
    <div>
      <select multiple onChange={handleCategoryChange}>
        <option value="Earnings">Earnings</option>
        <option value="Dividends">Dividends</option>
        <option value="Economic Data">Economic Data</option>
        <option value="Corporate Actions">Corporate Actions</option>
      </select>
      <select multiple onChange={handleStockChange}>
        <option value="AAPL">Apple</option>
        <option value="GOOGL">Google</option>
        <option value="MSFT">Microsoft</option>
        <option value="AMZN">Amazon</option>
      </select>
    </div>
  );
};

export default Filter;
