import React from 'react';
import './styles/StockInfoBox.css';

const StockInfoBox = ({ name, price, change }) => {
  return (
    <div className="stock-info-box">
      <h3>{name}</h3>
      <p>Price: ${price}</p>
      <p>Change: {change}%</p>
    </div>
  );
};

export default StockInfoBox;
