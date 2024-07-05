import '../HomePage.css';
import React, {useState} from 'react';
import SearchBox from '../components/SearchBox';
import StockSection from '../components/StockSection';

function HomePage (){
    const [showSearchBox, setShowSearchBox] = useState(false);

    const toggleSearchBox = () => {
      setShowSearchBox(!showSearchBox);
    };

    const stocks = [
        { name: 'Apple', price: 150, change: 1.2 },
        { name: 'Google', price: 2800, change: -0.5 },
        { name: 'Amazon', price: 3400, change: 2.0 },
        
      ];

      const cryptos = [
        { name: 'Bitcoin', price: 45000, change: 5 },
        { name: 'Ethereum', price: 3000, change: 3 },
        { name: 'Ripple', price: 1, change: -2 }
      ];
      
      const commodities = [
        { name: 'Gold', price: 1800, change: 1.2 },
        { name: 'Silver', price: 25, change: 2.1 },
        { name: 'Oil', price: 70, change: -0.5 }
      ];
      //<StockSection stocks={stocks} />
    return (
        <div className="homepage">
            
            <div className="search-container">
                <h1>StockSense</h1>
                <h3>Unlock the power of investment insights</h3>
                <SearchBox />
            </div>
            <div className='stock-info-container'>
                <StockSection stocks={stocks} />
                <StockSection stocks={cryptos} />
                <StockSection stocks={commodities} />
            </div>
        </div>
    )
}
export default HomePage