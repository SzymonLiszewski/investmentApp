/* eslint-disable react/prop-types */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import uptrend from '../../assets/uptrend.png';
import downtrend from '../../assets/downtrend.png';
import './TickerCard.css';

const TickerCard = ({ name, ticker }) => {
  const [price, setPrice] = useState(null);
  const [change, setChange] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const getData = async () => {
      try {
        const response = await fetch(`/api/basic/${ticker}/`);
        const data = await response.json();
        if (!cancelled) {
          setPrice(data['Current Price']);
          setChange(data['Percent Change']);
        }
      } catch {
        // leave placeholders when the quote is unavailable
      }
    };
    getData();
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  const priceValid = price !== null && price !== 'N/A' && !isNaN(Number(price));
  const changeValid = change !== null && change !== 'N/A' && !isNaN(Number(change));
  const up = changeValid && Number(change) >= 0;

  return (
    <Link className="ticker-card" to={`/analysis2/${ticker}`}>
      <div className="ticker-card-top">
        <div>
          <div className="ticker-card-name">{name}</div>
          <div className="ticker-card-symbol">{ticker}</div>
        </div>
        {changeValid && (
          <img
            className="ticker-card-trend"
            src={up ? uptrend : downtrend}
            alt={up ? 'Upward trend' : 'Downward trend'}
          />
        )}
      </div>
      <div className="ticker-card-bottom">
        <div className="ticker-card-price">
          {priceValid ? `$${Number(price).toFixed(2)}` : '—'}
        </div>
        {changeValid && (
          <div className={`ticker-card-change ${up ? 'up' : 'down'}`}>
            {up ? '+' : '−'}{Math.abs(Number(change)).toFixed(2)}%
          </div>
        )}
      </div>
    </Link>
  );
};

export default TickerCard;
