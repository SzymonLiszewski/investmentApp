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
        { name: 'Apple', price: 150, change: 1.2, ticker: 'AAPL'},
        { name: 'Google', price: 2800, change: -0.5, ticker: 'GOOGL' },
        { name: 'Microsoft', price: 45000, change: 5, ticker: 'MSFT' },
        { name: 'Tesla', price: 3000, change: 3, ticker: 'TSLA' },
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
      //<div className='stock-info-container'>
      //<StockSection stocks={stocks} />
      //<StockSection stocks={cryptos} />
      //<StockSection stocks={commodities} />
      // </div>
    return (
        <div className="homepage">
            <div className="mainItem">
              <div className="search-container">
                  <h1>StockSense</h1>
                  <h3>Unlock the power of investment insights</h3>
                  <h4>Choose Interesting stocks, discover our analysis and invest confidently </h4>
                  <SearchBox />
              </div>
              <img src="assets/image1.png"></img>
            </div>
            <div className='stock-info-container'>
              <StockSection stocks={stocks} />
            </div>
            
        </div>
    )
}
export default HomePage