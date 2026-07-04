/* eslint-disable react/prop-types */
import { Link } from 'react-router-dom';
import uptrend from '../../assets/uptrend.png';
import downtrend from '../../assets/downtrend.png';
import './TickerCard.css';

const TickerCard = ({ name, ticker, price, change, up }) => {
  return (
    <Link className="ticker-card" to={`/analysis2/${ticker}`}>
      <div className="ticker-card-top">
        <div>
          <div className="ticker-card-name">{name}</div>
          <div className="ticker-card-symbol">{ticker}</div>
        </div>
        <img
          className="ticker-card-trend"
          src={up ? uptrend : downtrend}
          alt={up ? 'Upward trend' : 'Downward trend'}
        />
      </div>
      <div className="ticker-card-bottom">
        <div className="ticker-card-price">{price}</div>
        <div className={`ticker-card-change ${up ? 'up' : 'down'}`}>{change}</div>
      </div>
    </Link>
  );
};

export default TickerCard;
