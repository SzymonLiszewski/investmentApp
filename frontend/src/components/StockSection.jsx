import React from 'react';
import StockInfoBox from './StockInfoBox';
import './styles/StockSection.css'


const StockSection = ({ stocks }) => {
  return (
    <div className="stock-section">
      <div className="stock-list">
        {stocks.map((stock, index) => (        
          <StockInfoBox
            key={index}
            name={stock.name}
            price={stock.price}
            change={stock.change}
            ticker={stock.ticker}
          />
        ))}
      </div>
    </div>
  );
};

export default StockSection;
