import "../components/styles/Portfolio.css"
import UserEarningsChart from "../components/portfolio/UserEarningsChart"
import UserStocksChart from "../components/portfolio/UserStocksChart"
import AssetClassAllocationChart from "../components/portfolio/AssetClassAllocationChart"
import IndicatorsGaugeChart from "../components/portfolio/IndicatorsGaugeChart"
import CurrencySelector from "../components/portfolio/CurrencySelector"
import { Fragment, useEffect, useState } from 'react';
import { format } from 'date-fns';
import { Link } from "react-router-dom"

function Portfolio(){
    const [sharpeRatio, setSharpeRatio] = useState(-100)
    const [sortinoRatio, setSortinoRatio] = useState(-100)
    const [alpha, setAlpha] = useState(-100)
    const [profit, setProfit] = useState([])
    const [selectedCurrency, setSelectedCurrency] = useState(() => {
        return localStorage.getItem('preferredCurrency') || 'PLN';
    })

    useEffect(()=>{
        const getUserAsset = async () => {
          try {
              const assetData = await fetchUserProfit();
          } catch (error) {
              console.log(error.message);
          }
      };
      getUserAsset();
      },[]);
      const fetchUserProfit = async () => {
        try {
            const token = localStorage.getItem('access');
            const response = await fetch('api/analytics/portfolio/profit/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            });
  
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
  
            const data = await response.json();

            const rawCalculatedData = data.calculated_data;
        
        const jsonString = rawCalculatedData.replace(/^"(.+)"$/, '$1');

        const parsedData = JSON.parse(jsonString);

        console.log('Parsed Data:', parsedData);

            const formattedData = Object.entries(parsedData).map(([unixTime, price]) => ({
              date: format(new Date(Number(unixTime)), 'yyyy-MM-dd'),
              price: price
          }));
        setSharpeRatio(data.sharpe)
        setSortinoRatio(data.sortino)
        setAlpha(data.alpha)
        setProfit(formattedData);
            return formattedData;
        } catch (error) {
            console.error('There has been a problem with your fetch operation:', error);
            throw error;
        }
    };
    //  value interpretation
    const interpretSharpe = sharpeRatio < 1 ? "Low return relative to its risk."
    : (sharpeRatio >= 1 && sharpeRatio < 2) ? "Decent return for its risk."
    : "Optimal return for its risk.";

    const interpretSortino = sortinoRatio < 0.5 ? "High downside risk relative to its return."
    : (sortinoRatio >= 0.5 && sortinoRatio < 1) ? "Moderate downside risk."
    : "Low downside risk relative to its return.";

    const interpretAlpha = alpha < 0 ? "Underperforms compared to the benchmark after adjusting for market risk."
    : (alpha >= 0 && alpha < 0.02) ? "Performs similarly to the benchmark after adjusting for market risk."
    : "Outperforms the benchmark after adjusting for market risk.";

    const handleCurrencyChange = (currency) => {
        setSelectedCurrency(currency);
    };

    return (
        <Fragment>
        <div style={{display: 'flex', gap: '10px', marginLeft: '5vw', marginRight: '5vw', marginBottom: '10px', alignItems: 'center', justifyContent: 'space-between'}}>
            <div style={{display: 'flex', gap: '10px'}}>
                <button className="connectedAccountsButton"><Link to="/connectAccounts" style={{color: "#000000"}}>connected accounts</Link></button>
                <button className="connectedAccountsButton"><Link to="/addStock" style={{color: "#000000"}}>add assets</Link></button>
            </div>
            <CurrencySelector onCurrencyChange={handleCurrencyChange} />
        </div>
        <div className="portfolio">
            <div className="portfolioDiv" id="return">
                <h1><UserEarningsChart profit={profit}/></h1>
            </div>
            <div className="portfolioDiv" id="composition">
                <UserStocksChart currency={selectedCurrency} />
            </div>
            <div className="portfolioDiv" id="compositionByClass">
                <AssetClassAllocationChart currency={selectedCurrency} />
            </div>
            <div className="portfolioDiv" id="indicators">
                <h3>Sharpe Ratio</h3>
                <IndicatorsGaugeChart data={sharpeRatio} range={[-1, 3]} name="Sharpe Ratio" interpretation={interpretSharpe}/>

                <h3>Sortino Ratio</h3>
                <IndicatorsGaugeChart data={sortinoRatio} range={[-0.5, 2]} name="Sortino Ratio" interpretation={interpretSortino}/>

                <h3>Alpha</h3>
                <IndicatorsGaugeChart data={alpha} range={[-0.05, 0.05]} name="Alpha" interpretation={interpretAlpha}/>
            </div>
        </div>
        </Fragment>
    )
}
    

export default Portfolio