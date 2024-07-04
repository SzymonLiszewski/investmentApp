import '../HomePage.css';
import React, {useState} from 'react';
import SearchBox from '../components/SearchBox';

function HomePage (){
    const [showSearchBox, setShowSearchBox] = useState(false);

    const toggleSearchBox = () => {
      setShowSearchBox(!showSearchBox);
    };

    return (
        <div className="homepage">
            <h1>StockSense</h1>
            <h3>Unlock the power of investment insights</h3>
            <div className="search-container">
                <SearchBox />
            </div>
            
        </div>
    )
}
export default HomePage