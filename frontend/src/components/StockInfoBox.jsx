import React from 'react';
import './styles/StockInfoBox.css';

const StockInfoBox = ({ name, price, change }) => {
  const textColor = change >=0 ? '#3ae307' : 'red';
  const trendIcon = change >=0 ? 'src/assets/uptrend.png' : 'src/assets/downtrend.png';
  return (
    <div className="stock-info-box">
      <h3 style = {{color: textColor}}>{name}</h3>
      <p style = {{color: textColor}}>Price: ${price}</p>
      <p style = {{color: textColor}} id="change">Change: {change}%</p>
      <img src={trendIcon} id='trendIcon'></img>
    </div>
  );
};

export default StockInfoBox;
