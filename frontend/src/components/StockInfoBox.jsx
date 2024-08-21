import React from 'react';
import './styles/StockInfoBox.css';
import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';

const StockInfoBox = ({ name, price, change, ticker }) => {
  const textColor = change >=0 ? '#3ae307' : 'red';
  const trendIcon = change >=0 ? 'assets/uptrend.png' : 'assets/downtrend.png';
  let [CurrentPrice, setCurrentPrice] = useState(0)
    let [PriceChange, setPriceChange] = useState(0)

    let getData = async () =>{
      let response = await fetch(`/api/basic/${ticker}/`)
      let data = await response.json()
      setCurrentPrice(data['Current Price'])
      setPriceChange(data['Percent Change'])
  }

  useEffect(()=>{
    getData()
}, [])
  return (
    <Link to={`/analysis2/${ticker}`} className="stock-info-box">

      <h3 style = {{color: textColor}}>{name}</h3>
      <p style = {{color: textColor}}>Price: ${CurrentPrice.toFixed(2)}</p>
      <p style = {{color: textColor}} id="change">Change: {PriceChange.toFixed(2)}%</p>
      <img src={trendIcon} id='trendIcon'></img>

    </Link>
  );
};

export default StockInfoBox;
