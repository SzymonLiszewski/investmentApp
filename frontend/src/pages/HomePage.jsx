import '../HomePage.css';
import React, {useState} from 'react';
import { Link } from 'react-router-dom';
import SearchBox from '../components/SearchBox';
import StockSection from '../components/StockSection';
import homePageImage from '../assets/image1.png'

function HomePage (){
    const [showSearchBox, setShowSearchBox] = useState(false);
    const isDemoMode = import.meta.env.VITE_USE_MOCK_DATA_FETCHER === 'true';
    

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
                  <h1>Captrivio</h1>
                  <h3>Keep your investments under control.</h3>
                  <h4>
                    <Link to="/login">Sign in</Link> to unlock portfolio insights.
                  </h4>
                  {isDemoMode && (
                    <p className="demo-banner">
                      Demo version - prices and predictions are for illustrative purposes only.
                    </p>
                  )}
                  <SearchBox navigation={'analysis2'}/>
              </div>
              <div className="homepage-image-wrapper">
                <img src={homePageImage} alt="Investment illustration" />
                <p className="image-credit">Designed by Freepik</p>
              </div>
            </div>
            <div className='stock-info-container'>
              <StockSection stocks={stocks} />
            </div>
            
        </div>
    )
}
export default HomePage